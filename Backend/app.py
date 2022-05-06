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
import io
from blur import blur_image
import new_blending

app = Flask("__name__")
cors = CORS(app)

def resize_box(left, top, right, bottom, width, height):
    left_new = left
    right_new = right
    top_new = top
    bottom_new = bottom

    if (left - 20) > 0:
        left_new -= 20
    else:
        left_new = 0

    if right + 20 < width:
        right_new = right_new + 20
    else:
        right_new = width - 1

    if (top - 20) > 0:
        top_new -= 20
    else:
        top_new = 0

    if bottom + 20 < height:
        bottom_new = bottom_new + 20
    else:
        bottom_new = height - 1

    return left_new, top_new, right_new, bottom_new

@app.route("/detect", methods=['POST'])
def detect():
    imagefile = request.files.get('image', '')
    image = Image.open(imagefile, mode='r')
    boundary_boxes = detection.detect(image)

    if boundary_boxes is None:
        print("error")
        raise InvalidUsage('No faces detected', status_code=410)

    return jsonify({"boxes": boundary_boxes, "message": "successful"})


@app.route("/detect_web", methods=['POST'])
def detect_web():
    #print(request.form)
    print(request.get_json())
    image64 = request.get_json().get('image')
    print(image64)
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    cv2.imwrite("cv2.jpg", np_image)

    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    boundary_boxes = detection.detect(image)

    if boundary_boxes is None:
        print("error")
        raise InvalidUsage('No faces detected', status_code=410)

    return jsonify({"boxes": boundary_boxes, "message": "successful"})


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
            left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)

            single_face = image.crop((left, top, right, bottom))
            single_face.save("00replace_does_it_crop{}.jpg".format(index))

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
            db_image.save("01replace_db{}.jpg".format(index))

            #blended = blending.blend_faces(db_image.convert("RGB"), single_face.convert("RGB"))#single_face.convert('RGB')) #is in PIL IMAGE FORMAT
            blended = new_blending.blend_image(db_img=db_image.convert("RGB"), src_img=single_face.convert("RGB"))#single_face.convert('RGB')) #is in PIL IMAGE FORMAT
            if blended is None:
                print("no destination face!!!!!!")
                face[index]["invalid"] = True
            else:
                face[index]["invalid"] = False
                #image.paste(blended, (left, top))
                image.paste(blended, (int(round(left)), int(round(top))))
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

@app.route("/replace_web", methods=['POST'])
def replace_web():
    image64 = request.get_json().get('image')
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    # cv2.imwrite("cv2.jpg", np_image)

    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    faces_str = request.get_json().get('faces')
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
            left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)

            single_face = image.crop((left, top, right, bottom))
            single_face.save("replace_does_it_crop{}.jpg".format(index))

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

            #blended = blending.blend_faces(db_image.convert("RGB"), single_face.convert("RGB"))#single_face.convert('RGB')) #is in PIL IMAGE FORMAT
            blended = new_blending.blend_image(db_img=db_image.convert("RGB"), src_img=single_face.convert("RGB"))
            if blended is None:
                print("no destination face!!!!!!")
                face[index]["invalid"] = True
            else:
                face[index]["invalid"] = False
                #image.paste(blended, (left, top))
                image.paste(blended, (int(round(left)), int(round(top))))
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
    #imagefile = request.files.get('image', '')
    #image = Image.open("src.jpg", mode='r')

    image64 = request.form.get('image')
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    cv2.imwrite("cv2.jpg", np_image)

    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    faces_str = request.form.get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print("faces:", faces)
    # todo: change here for single face
    properties = faces
    left = properties["left"]
    top = properties["top"]
    right = properties["left"] + properties["width"]
    bottom = properties["top"] + properties["height"]
    age = properties["age"]
    gender = properties["gender"]
    race = properties["skinColor"]

    left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)

    single_face = image.crop((left, top, right, bottom))
    single_face.save("00blend_does_it_crop.jpg")
    #retrieve image from database here (called db_image)
    db_image = firebase_connection.retrieve_image_from_database(age, gender, race)
    message = ""
    db_image.save("01blend_db.jpg")
    #blended = blending.blend_faces(db_image.convert("RGB"), single_face.convert("RGB"))#single_face.convert('RGB')) #is in PIL IMAGE FORMAT
    blended = new_blending.blend_image(db_img=db_image.convert("RGB"), src_img=single_face.convert(
        "RGB"))  # single_face.convert('RGB')) #is in PIL IMAGE FORMAT

    if blended is None:
        print("no destination face!!!!!!")
        faces["invalid"] = True
        message = "error"
    else:
        faces["invalid"] = False
        image.paste(blended, (int(round(left)), int(round(top))))
        image.save('output_blended_blend{}.png')
        message = "successful"

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
    result = {"image": response_img, "message": message}

    return jsonify(result)

@app.route("/blend_web", methods=['POST'])
def blend_web():
    #imagefile = request.files.get('image', '')
    #image = Image.open("src.jpg", mode='r')

    image64 = request.get_json().get('image')
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    cv2.imwrite("cv2.jpg", np_image)

    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    faces_str = request.get_json().get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print("faces:", faces)
    # todo: change here for single face
    properties = faces
    left = properties["left"]
    top = properties["top"]
    right = properties["left"] + properties["width"]
    bottom = properties["top"] + properties["height"]
    age = properties["age"]
    gender = properties["gender"]
    race = properties["skinColor"]

    left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)

    single_face = image.crop((left, top, right, bottom))
    single_face.save("blend_did_it_change.jpg")
    #retrieve image from database here (called db_image)
    db_image = firebase_connection.retrieve_image_from_database(age, gender, race)
    message = ""
    #blended = blending.blend_faces(db_image.convert("RGB"), single_face.convert("RGB"))#single_face.convert('RGB')) #is in PIL IMAGE FORMAT
    blended = new_blending.blend_image(db_img=db_image.convert("RGB"), src_img=single_face.convert(
        "RGB"))  # single_face.convert('RGB')) #is in PIL IMAGE FORMAT
    if blended is None:
        print("no destination face!!!!!!")
        faces["invalid"] = True
        message = "error"
    else:
        faces["invalid"] = False
        image.paste(blended, (int(round(left)), int(round(top))))
        image.save('output_blended_blend{}.png')
        message = "successful"

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
    result = {"image": response_img, "message": message}

    return jsonify(result)

@app.route("/blur", methods=['POST'])
def blur():
    image64 = request.form.get('image')
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    #cv2.imwrite("cv2.jpg", np_image)

    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    faces_str = request.form.get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print("faces", faces)

    properties = faces
    left = properties["left"]
    top = properties["top"]
    right = properties["left"] + properties["width"]
    bottom = properties["top"] + properties["height"]

    left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)

    single_face = image.crop((left, top, right, bottom))
    single_face.save("00blur_does_it_crop.jpg")
    blurred_img = blur_image(single_face)
    image.paste(blurred_img, (int(round(left)), int(round(top))))
    image.save('output_blurred.png')

    # convert image(PIL) to numpy
    print("image size before sending", image.size)
    rgb_img = image.convert("RGB")
    np_image = np.array(rgb_img)
    np_image = np_image[:, :, : :-1].copy()

    # encode numpy image
    print("numpy before encoding size", np_image.shape)
    success, encoded_image = cv2.imencode('.png', np_image)
    content = encoded_image.tobytes()
    response_img = base64.b64encode(content).decode('ascii')
    result = {"image": response_img}

    return jsonify(result)

@app.route("/blur_web", methods=['POST'])
def blur_web():
    image64 = request.get_json().get('image')
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    #cv2.imwrite("cv2.jpg", np_image)

    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    faces_str = request.get_json().get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print("faces", faces)

    properties = faces
    left = properties["left"]
    top = properties["top"]
    right = properties["left"] + properties["width"]
    bottom = properties["top"] + properties["height"]

    left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)
    single_face = image.crop((left, top, right, bottom))
    blurred_img = blur_image(single_face)
    image.paste(blurred_img, (int(round(left)), int(round(top))))
    image.save('output_blurred.png')

    # convert image(PIL) to numpy
    print("image size before sending", image.size)
    rgb_img = image.convert("RGB")
    np_image = np.array(rgb_img)
    np_image = np_image[:, :, : :-1].copy()

    # encode numpy image
    print("numpy before encoding size", np_image.shape)
    success, encoded_image = cv2.imencode('.png', np_image)
    content = encoded_image.tobytes()
    response_img = base64.b64encode(content).decode('ascii')
    result = {"image": response_img}

    return jsonify(result)

@app.route("/selected_swap", methods=['POST'])
def selected_swap():
    print(request.get_json())
    image64 = request.get_json().get('src_image')
    print(image64)
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image.save("src_im_selected_swap.jpg")

    selected64 = request.get_json().get('selected_image')
    print(selected64)
    decoded_selected = np.fromstring(base64.b64decode(selected64), np.uint8)
    np_selected = cv2.imdecode(decoded_selected, cv2.IMREAD_COLOR)
    selected_image = cv2.cvtColor(np_selected, cv2.COLOR_BGR2RGB)
    selected_image = Image.fromarray(selected_image)
    selected_image.save("selected_im_selected_swap.jpg")

    faces_str = request.get_json().get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print("faces", faces)

    properties = faces
    left = properties["left"]
    top = properties["top"]
    right = properties["left"] + properties["width"]
    bottom = properties["top"] + properties["height"]
    left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)
    single_face = image.crop((left, top, right, bottom))
    single_face.save("WHYYY.jpg")

    #blended = blending.blend_faces(selected_image.convert("RGB"), single_face.convert("RGB"))
    blended = new_blending.blend_image(db_img=selected_image.convert("RGB"), src_img=single_face.convert(
        "RGB"))  # single_face.convert('RGB')) #is in PIL IMAGE FORMAT

    message = ""
    if blended is None:
        print("no destination face!!!!!!")
        message = "error"
    else:
        faces["invalid"] = False
        image.paste(blended, (int(round(left)), int(round(top))))
        message = "successful"

    # convert image(PIL) to numpy
    print("image size before sending", image.size)
    rgb_img = image.convert("RGB")
    np_image = np.array(rgb_img)
    np_image = np_image[:, :, : :-1].copy()

    # encode numpy image
    print("numpy before encoding size", np_image.shape)
    success, encoded_image = cv2.imencode('.png', np_image)
    content = encoded_image.tobytes()
    response_img = base64.b64encode(content).decode('ascii')

    print("final faces:", faces)
    result = {"image" : response_img, "message": message}

    return jsonify(result)

@app.route("/suggested_faces", methods=['POST'])
def suggested_faces():
    faces_str = request.get_json().get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print("faces:", faces)

    properties = faces
    age = properties["age"]
    gender = properties["gender"]
    race = properties["skinColor"]
    result = {}
    suggested_list = firebase_connection.retrieve_suggested_images(age, gender, race)
    face_names = ["face1", "face2", "face3"]

    for i in range(3):
        cur_face = suggested_list[i]
        #convert image(PIL) to numpy
        print("image size before sending", cur_face.size)
        rgb_img = cur_face.convert("RGB")
        np_image = np.array(rgb_img)
        np_image = np_image[:, :, : :-1].copy()

        #encode numpy image
        print("numpy before encoding size", np_image.shape)
        success, encoded_image = cv2.imencode('.png', np_image)
        content = encoded_image.tobytes()
        response_img = base64.b64encode(content).decode('ascii')
        print(i)
        print(face_names[i])
        result[face_names[i]] = response_img

    print(result)
    return jsonify(result)

@app.route("/i_feel_lucky", methods=['POST'])
def i_feel_lucky():
    image64 = request.form.get('image')
    decoded_img = np.fromstring(base64.b64decode(image64), np.uint8)
    np_image = cv2.imdecode(decoded_img, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)

    faces_str = request.form.get('faces')
    print(faces_str)
    faces = json.loads(faces_str)
    print("faces", faces)

    properties = faces
    left = properties["left"]
    top = properties["top"]
    right = properties["left"] + properties["width"]
    bottom = properties["top"] + properties["height"]
    left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)
    single_face = image.crop((left, top, right, bottom))

    random_image = firebase_connection.retrieve_random_image()
    #blended = blending.blend_faces(random_image.convert("RGB"), single_face.convert("RGB"))
    blended = new_blending.blend_image(db_img=random_image.convert("RGB"), src_img=single_face.convert(
        "RGB"))  # single_face.convert('RGB')) #is in PIL IMAGE FORMAT
    message = ""
    if blended is None :
        print("no destination face!!!!!!")
        message = "error"
    else :
        faces["invalid"] = False
        image.paste(blended, (int(round(left)), int(round(top))))
        message = "successful"

    # convert image(PIL) to numpy
    print("image size before sending", image.size)
    rgb_img = image.convert("RGB")
    np_image = np.array(rgb_img)
    np_image = np_image[:, :, : :-1].copy()

    # encode numpy image
    print("numpy before encoding size", np_image.shape)
    success, encoded_image = cv2.imencode('.png', np_image)
    content = encoded_image.tobytes()
    response_img = base64.b64encode(content).decode('ascii')

    print("final faces:", faces)
    result = {"image": response_img, "message": message}

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
    app.run(host="0.0.0.0", port=5000, debug=True)