import cv2
import os
import numpy
import facerec

# detect faces from an img and than take the face out, resize the face img to 200*200 gray format.
def detect(filename, outfile=None):
    face_cascade = cv2.CascadeClassifier('./cascades/haarcascade_frontalface_default.xml')
    img = cv2.imread(filename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        f = cv2.resize(gray[y:y + h, x:x + w], (200, 200))
        if outfile:
            outfile = "{}.{}".format(outfile, "jpg")
            cv2.imwrite(outfile, f)
        return f


def read_images(path):  # read training imgs in to array

    id = 1
    img_list, label = [], []
    for filename in os.listdir(path):
        if "jm" in filename:
            id=1
        else:
            id=0
        filepath = os.path.join(path, filename)
        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (200, 200))  # resize imgs into 200*200 pixels
        img_list.append(numpy.asarray(img, dtype=numpy.uint8))
        label.append(id)
    return [img_list, label]


def face_rec(training_img_path, img_path):
    [x, y] = read_images(training_img_path)
    y = numpy.asarray(y, dtype=numpy.int32)

    model = cv2.face.createEigenFaceRecognizer()  # create face recognizer
    model.train(numpy.asarray(x), numpy.asarray(y))  # train recognizer
    face_cascade = cv2.CascadeClassifier('./cascades/haarcascade_frontalface_default.xml')
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # read img needs to be classified
    faces = face_cascade.detectMultiScale(img, 1.3, 5)
    for (x, y, w, h) in faces:
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except Exception:
            gray = img
        roi = gray[x:x + w, y:y + h]
        roi = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_LINEAR)
        params = model.predict(roi)
        return params


if __name__ == "__main__":
    print cv2.__version__
    img_path = 'rawand.jpg'
    training_imgs = "./faces"
    print face_rec(training_imgs, img_path)
