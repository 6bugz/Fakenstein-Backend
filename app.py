from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw as D
import classification
import detection
import base64
import blending
import json
import cv2
import numpy as np
import firebase_connection

app = Flask("__name__")
cors = CORS(app)

@app.route("/detect", methods=['POST'])
def detect():
    imagefile = request.files.get('image', '')
    image = Image.open(imagefile, mode='r')
    boundary_boxes = detection.detect(image)

    if boundary_boxes is None:
        print("error")
        raise InvalidUsage('No faces detected', status_code=410)

    return jsonify(boundary_boxes)

@app.route("/replace", methods=['POST'])
def replace():
    imagefile = request.files.get('image', '')
    image = Image.open(imagefile, mode='r')
    faces_str = request.form.get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print(faces)
    #draw = D.Draw(image)

    for face in faces:
        if face is None:
            print("null value here!")
            continue
        for index in face:
            print(face[index])
            print(index)
            properties = face[index]
            left = properties["left"]
            top = properties["top"]
            right = properties["left"] + properties["width"]
            bottom = properties["top"] + properties["height"]

            #draw.rectangle([(left, top), (right, bottom)], outline="red", fill="magenta")
            #image.save("isitface{}.jpg".format(face), "JPEG")

            #adjust bounding box
            #todo: ideas about improving blending:
            #if the facebox is too big, it can't detect -> resize the box? (smaller)
            if (left - 20) > 0:
                left -= 20
            else:
                left = 0
            print("left", left)

            if right + 20 < image.width:
                right = right + 20
            else:
                right = image.width - 1
            print("right", right)

            if (top - 20) > 0:
                top -= 20
            else:
                top = 0
            print("top", top)

            if bottom + 20 < image.height:
                bottom = bottom + 20
            else:
                bottom = image.height - 1
            print("bottom", bottom)

            single_face = image.crop((left, top, right, bottom))
            single_face.save("{}_cropped.jpg".format(index))

            print("Benim croplar size:", single_face.size)

            age, gender, race = classification.classify(single_face)
            face[index]["age"] = age
            face[index]["gender"] = gender
            face[index]["skinColor"] = race

            print("saved to index: ", index)
            print("age", face[index]["age"])
            print("height", face[index]["height"])
            print("gender", face[index]["gender"])

            #retrieve image from database here (called db_image)
            db_image = firebase_connection.retrieve_image_from_database(age, gender, race)

            blended = blending.blend_faces(db_image.convert("RGB"), single_face.convert("RGB"))#single_face.convert('RGB')) #is in PIL IMAGE FORMAT
            if blended is None:
                print("no destination face!!!!!!")
                face[index]["invalid"] = True
            else:
                face[index]["invalid"] = False
                #image.paste(blended, (left, top))
                image.paste(blended, (left, top))
                image.save('output_blended{}.png'.format(index))
                #raise InvalidUsage("No destination face found! Remove box from image!", status_code=410)
                #image = blended


    #convert image(PIL) to numpy
    print("image size before sending", image.size)
    rgb_img = image.convert("RGB")
    np_image = np.array(rgb_img)
    np_image = np_image[:, :, : :-1].copy()

    #encode numpy image
    print("numpy before encoding size", np_image.shape)
    success, encoded_image = cv2.imencode('.png', np_image)
    content = encoded_image.tobytes()
    response_img = base64.b64encode(content).decode('ascii')

    print("final faces:", faces)
    result = {"image": response_img, "faces": faces}

    return jsonify(result)

@app.route("/blend", methods=['POST'])
def blend():
    imagefile = request.files.get('image', '')
    image = Image.open(imagefile, mode='r')
    faces_str = request.form.get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print(faces)

    for face in faces:
        if face is None:
            print("null value here!")
            continue
        for index in face:
            print(face[index])
            print(index)
            properties = face[index]
            left = properties["left"]
            top = properties["top"]
            right = properties["left"] + properties["width"]
            bottom = properties["top"] + properties["height"]
            age = properties["age"]
            gender = properties["gender"]
            race = properties["skinColor"]

            #adjust bounding box
            if (left - 20) > 0:
                left -= 20
            else:
                left = 0

            if right + 20 < image.width:
                right = right + 20
            else:
                right = image.width - 1

            if (top - 20) > 0:
                top -= 20
            else:
                top = 0

            if bottom + 20 < image.height:
                bottom = bottom + 20
            else:
                bottom = image.height - 1

            single_face = image.crop((left, top, right, bottom))

            #retrieve image from database here (called db_image)
            db_image = firebase_connection.retrieve_image_from_database(age, gender, race)

            blended = blending.blend_faces(db_image.convert("RGB"), single_face.convert("RGB"))#single_face.convert('RGB')) #is in PIL IMAGE FORMAT
            if blended is None:
                print("no destination face!!!!!!")
                face[index]["invalid"] = True
            else:
                face[index]["invalid"] = False
                image.paste(blended, (left, top))
                image.save('output_blended_blend{}.png'.format(index))

    #convert image(PIL) to numpy
    print("image size before sending", image.size)
    rgb_img = image.convert("RGB")
    np_image = np.array(rgb_img)
    np_image = np_image[:, :, : :-1].copy()

    #encode numpy image
    print("numpy before encoding size", np_image.shape)
    success, encoded_image = cv2.imencode('.png', np_image)
    content = encoded_image.tobytes()
    response_img = base64.b64encode(content).decode('ascii')

    print("final faces:", faces)
    result = {"image": response_img, "faces": faces}

    return jsonify(result)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == "__main__":
    app.run(host="176.88.100.24", port=5000, debug=True)