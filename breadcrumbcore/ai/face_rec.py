import sys, os

sys.path.append("../..")
# import facerec modules
from facerec.feature import Fisherfaces
from facerec.distance import EuclideanDistance
from facerec.classifier import NearestNeighbor
from facerec.model import PredictableModel
from facerec.validation import KFoldCrossValidation
from facerec.visual import subplot
from facerec.util import minmax_normalize
import cv2
# import numpy, matplotlib and logging
import numpy as np
from facerec.dataset import NumericDataSet

from PIL import Image
import matplotlib.cm as cm
import logging

def detect_face(filename, outfile=None):
    face_cascade = cv2.CascadeClassifier('./cascades/haarcascade_frontalface_default.xml')
    img = cv2.imread(filename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        #img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        f = cv2.resize(gray[y:y + h, x:x + w], (200,200))
        if outfile:
            cv2.imwrite(outfile, f)
        return f

def read_images(path, sz=None, keys=[]):
    """Reads the images in a given folder, resizes images on the fly if size is given.

    Args:
        path: Path to a folder with subfolders representing the subjects (persons).
        sz: A tuple with the size Resizes

    Returns:
        A list [X,y]

            X: The images, which is a Python list of numpy arrays.
            y: The corresponding labels (the unique number of the subject, person) in a Python list.
    """
    c = len(keys)
    X, y = [], []

    for dirname, dirnames, filenames in os.walk(path):
        for subdirname in dirnames:
            subject_path = os.path.join(dirname, subdirname)
            subject_count = 0
            for filename in os.listdir(subject_path):
                try:
                    temp_path = os.path.abspath(os.path.join(subject_path, "temp_%s" % filename))
                    path = os.path.join(subject_path, filename)
                    temp_file = detect_face(path, temp_path)
                    im = Image.open(temp_path)
                    im = im.convert("L")
                    os.remove(temp_path)
                    # resize to given size (if given)
                    if (sz is not None):
                        im = im.resize(sz, Image.ANTIALIAS)
                    X.append(np.asarray(im, dtype=np.uint8))
                    y.append(c)
                    subject_count+=1
                except IOError, e:
                    pass
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
            print "%s->%s (%s)" % (subdirname, c,subject_count)
            keys.append(subdirname)

            c = c + 1
    return [X, y, keys]

class PredictableModelWrapper(object):

    def __init__(self, model):
        self.model = model
        self.numeric_dataset = NumericDataSet()

    def compute(self):
        X,y = self.numeric_dataset.get()
        self.model.compute(X,y)

    def set_data(self, numeric_dataset):
        self.numeric_dataset = numeric_dataset

    def predict(self, image):
        prediction_result = self.model.predict(image)
        # Only take label right now:
        num_label = prediction_result[0]
        str_label = self.numeric_dataset.resolve_by_num(num_label)
        return str_label

    def update(self, name, image):
        self.numeric_dataset.add(name, image)
        class_label = self.numeric_dataset.resolve_by_str(name)
        extracted_feature = self.feature.extract(image)
        self.classifier.update(extracted_feature, class_label)

    def __repr__(self):
        return "PredictableModelWrapper (Inner Model=%s)" % (str(self.model))

if __name__ == "__main__":
    # This is where we write the images, if an output_dir is given
    # in command line:

    out_dir = None
    # You'll need at least a path to your image data, please see
    # the tutorial coming with this source code on how to prepare
    # your image data:

    # Now read in the image data. This must be a valid path!
    [X, y, keys] = read_images("../faces/")
    print len(X), keys

    # Then set up a handler for logging:
    feature = Fisherfaces()
    # Define a 1-NN classifier with Euclidean Distance:
    classifier = NearestNeighbor(dist_metric=EuclideanDistance(), k=1)
    # Define the model as the combination
    model = PredictableModel(feature=feature, classifier=classifier)
    # Compute the Fisherfaces on the given data (in X) and labels (in y):
    model.compute(X, y)

    # Then turn the first (at most) 16 eigenvectors into grayscale
    # images (note: eigenvectors are stored by column!)
    # E = []
    # for i in xrange(min(model.feature.eigenvectors.shape[1], 16)):
    #     e = model.feature.eigenvectors[:, i].reshape(X[0].shape)
    #     E.append(minmax_normalize(e, 0, 255, dtype=np.uint8))


    img_path = 'rawand1.jpg'
    coverted_img_path = "temp_%s" % img_path
    detect_face(img_path,outfile=coverted_img_path)
    img = Image.open(coverted_img_path)
    img = img.convert("L")

    p = model.predict(img)[0]
    label = keys[p]
    print label

    [X, y, keys] = read_images("../faces2/", keys=keys)
    model.classifier.update(X,y)


    p = model.predict(img)[0]
    label = keys[p]
    print label

