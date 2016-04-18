#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) Philipp Wagner. All rights reserved.
# Licensed under the BSD license. See LICENSE file in the project root for full license information.

import csv, os, sys
# Import PIL
import cv2

try:
    from PIL import Image
except ImportError:
    import Image
# Import numpy:
import numpy as np
# Import facerec:
from facerec.feature import ChainOperator, Fisherfaces
from facerec.preprocessing import Resize
from facerec.dataset import NumericDataSet
from facerec.distance import EuclideanDistance
from facerec.classifier import NearestNeighbor
from facerec.model import PredictableModel
from facerec.validation import KFoldCrossValidation
from facerec.serialization import save_model, load_model


# This is the face recognition module for the RESTful Webservice.
#
# The current implementation uses a fixed model defined in code. 
# A simple wrapper works around a limitation of the current framework, 
# because as time of writing this only integer labels can be passed into 
# the classifiers of the facerec framework. 

# This wrapper hides the complexity of dealing with integer labels for
# the training labels. It also supports updating a model, instead of 
# re-training it. 
class PredictableModelWrapper(object):
    def __init__(self, model):
        self.model = model
        self.numeric_dataset = NumericDataSet()

    def compute(self):
        X, y = self.numeric_dataset.get()
        self.model.compute(X, y)

    def set_data(self, numeric_dataset):
        self.numeric_dataset = numeric_dataset

    def predict(self, image):
        prediction_result = self.model.predict(image)
        # Only take label right now:
        num_label = prediction_result[0]
        str_label = self.numeric_dataset.resolve_by_num(num_label)
        return str_label

    def add_data(self, new_numeric_dataset):
        data = new_numeric_dataset.data
        for name, img_list in data.iteritems():
            for img in img_list:
                self.update(name, img)

    def update(self, name, image):
        self.numeric_dataset.add(name, image)
        class_label = self.numeric_dataset.resolve_by_str(name)
        extracted_feature = self.model.feature.extract(image)
        self.model.classifier.update(extracted_feature, class_label)

    def __repr__(self):
        return "PredictableModelWrapper (Inner Model=%s)" % (str(self.model))


# Now define a method to get a model trained on a NumericDataSet,
# which should also store the model into a file if filename is given.
def get_model(numeric_dataset, model_filename=None):
    feature = ChainOperator(Resize((128, 128)), Fisherfaces())
    classifier = NearestNeighbor(dist_metric=EuclideanDistance(), k=1)
    inner_model = PredictableModel(feature=feature, classifier=classifier)
    model = PredictableModelWrapper(inner_model)
    model.set_data(numeric_dataset)
    model.compute()
    if not model_filename is None:
        save_model(model_filename, model)
    return model


# Now a method to read images from a folder. It's pretty simple,
# since we can pass a numeric_dataset into the read_images  method 
# and just add the files as we read them. 
def read_images(path, identifier, numeric_dataset):
    for filename in os.listdir(path):
        try:
            img_path = os.path.abspath(os.path.join(path, filename))
            temp_path = os.path.abspath(os.path.join(path, "temp_%s" % filename))
            detect_face(img_path, temp_path)
            img = Image.open(temp_path)
            img = img.convert("L")
            img = np.asarray(img, dtype=np.uint8)
            numeric_dataset.add(identifier, img)
            print "%s -> %s" % (filename, identifier)
            os.remove(temp_path)
        except IOError, (errno, strerror):
            print "I/O error({0}): {1}".format(errno, strerror)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise


def read_image(path, identifier, numeric_dataset):
    try:
        path_parts = path.split(".")

        if path_parts[-1] not in ("jpg","jpeg"):
            return

        img_path = os.path.abspath(path)
        temp_path = os.path.abspath("temp.%s" % path_parts[-1])
        detect_face(img_path, temp_path)
        img = Image.open(temp_path)
        img = img.convert("L")
        img = np.asarray(img, dtype=np.uint8)
        numeric_dataset.add(identifier, img)
        print "%s -> %s" % (img_path, identifier)
        os.remove(temp_path)
    except IOError, (errno, strerror):
        print "I/O error({0}): {1}".format(errno, strerror)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise


# read_csv is a tiny little method, that takes a csv file defined
# like this:
#
#   Philipp Wagner;D:/images/philipp
#   Another Name;D:/images/another_name
#   ...
#
def read_from_csv(filename):
    numeric_dataset = NumericDataSet()
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='#')
        for row in reader:
            identifier = row[0]
            path = row[1]
            read_images(path, identifier, numeric_dataset)
    return numeric_dataset


def get_numeric_dataset(image_paths, identifier):
    numeric_dataset = NumericDataSet()
    for path in image_paths:
        read_image(path, identifier, numeric_dataset)
    return numeric_dataset


# Just some sugar on top...
def get_model_from_csv(filename, out_model_filename=None):
    numeric_dataset = read_from_csv(filename)
    model = get_model(numeric_dataset, out_model_filename)
    return model


def load_model_file(model_filename):
    load_model(model_filename)


# Detect and return cropped faces in an image. Returns empty array if none detect.
# If multiple faces detect, it'll return the first one identified
def detect_face(filename, outfile=None):
    face_cascade = cv2.CascadeClassifier('./cascades/haarcascade_frontalface_default.xml')

    if not os.path.isfile(filename):
        return

    img = cv2.imread(filename)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces):
        x, y, w, h = faces[0]
        cropped = gray[y:y + h, x:x + w]
        if outfile:
            cv2.imwrite(outfile, cropped)
        return cropped


if __name__ == "__main__":
    img_path = 'kim1.jpg'
    coverted_img_path = "temp_%s" % img_path
    detect_face(img_path, outfile=coverted_img_path)
    model = get_model_from_csv("faces.csv")
    img = Image.open(coverted_img_path)
    img = img.convert("L")
    p = model.predict(img)
    print "*******", p

    new_numeric_dataset = read_from_csv("new_faces.csv")
    model.add_data(new_numeric_dataset)

    print model.numeric_dataset.data.keys()

    p = model.predict(img)
    print "*******", p

