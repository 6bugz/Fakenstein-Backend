from mtcnn.mtcnn import MTCNN
import cv2
import numpy as np
from matplotlib import pyplot
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw as D

def face_detection(image):
  # load image from file
  #pixels = pyplot.imread(filename)

  # create the detector, using default weights
  detector = MTCNN()
  # detect faces in the image
  faces = detector.detect_faces(image)


  #faces contain for each face index:
  #box: the x, y, width, height of each detected face
  #confidence, key_points

  for face in faces:
      # get coordinates
      x, y, width, height = face['box']

  return faces


def detect_background(image, pil_image):
    #image = cv2.imread(filename)
    size = image.shape
    faces = face_detection(image)

    if faces is None or len(faces) == 0:
        #print("No faces detected")
        return [],[]

    ratio_box_array = []
    for face in faces:
        # new array with_ratio = x, y, w, h, woran, horan (image and faces ratio)
        with_ratio = face['box'].copy()
        with_ratio.append(face['box'][2] / size[1])
        with_ratio.append(face['box'][3] / size[0])

        ratio_box_array.append(with_ratio)

    # sort accroding to ratio
    ratio_box_array.sort(key=lambda ratio_box_array : ratio_box_array[4], reverse=True)
    ratio_box_array = np.array(ratio_box_array)

    # compare ratios and find background ones

    max_ratio = ratio_box_array[0][4]
    #print(max_ratio)

    # 4th index have the ratio of the width ratios to the max ratio
    ratio_box_array[:, 4] /= max_ratio

    fore_array = []
    back_array = []

    for box in ratio_box_array:
        if max_ratio > 0.05:
            if box[4] > 0.8:
                fore_array.append(box)
            else :
                back_array.append(box)
        else :
            if box[4] > 0.6 :
                fore_array.append(box)
            else :
                back_array.append(box)
    bf_boundary_box(pil_image, fore_array, back_array)

    return fore_array, back_array

def bf_boundary_box(i, foreground_faces, background_faces):
    # load the image

    draw = D.Draw(i)

    # plot each box
    for face in foreground_faces:
        # get coordinates
        x, y, width, height, _, _ = face
        # create the shape
        draw.rectangle([(x, y), (x + width, y + height)], outline="white")

    for face in background_faces:
        # get coordinates
        x, y, width, height, _, _ = face
        # create the shape
        draw.rectangle([(x, y), (x + width, y + height)], outline="blue")
    #i.save("elifeeee.jpg", "JPEG")

def detect(image):
    numpy_img = np.array(image)
    fore_array, back_array = detect_background(numpy_img, image)
    #format: dict- isBackground(bool), height, width, top(y), left(x)
    faces = {}
    count = 0
    for fore_face in fore_array:
        x = fore_face[0]
        y = fore_face[1]
        width = fore_face[2]
        height = fore_face[3]
        face = {"isBackground": False, "height": height, "width": width, "top": y, "left": x}
        faces[str(count)] = face
        count += 1
    for back_face in back_array:
        x = back_face[0]
        y = back_face[1]
        width = back_face[2]
        height = back_face[3]
        face = {"isBackground": True, "height": height, "width": width, "top": y, "left": x}
        #changed for desktop!! (array in server version)
        faces[str(count)] = face
        count += 1

    if len(faces) == 0:
        return None
    return faces