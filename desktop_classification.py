import classification
import sys
from PIL import Image
import json
import firebase_connection
import blending

#INPUT: reads image path from system args, reads faces.json from filesystem
#PRINT: prints error if there were no faces detected in the image
#SAVE: saves the classified faces into faces.json file with the following values:
#isBackground: if the face is in background - True, else - False
#height: height of boundary box
#width: width of boundary box
#top: y of boundary box (left top corner)
#left: x of boundary box (left top corner)
#age: 0 if old, 1 if young
#gender: 0 if female, 1 if male
#skinColor: 0 if pale, 1 if dark
#invalid: if there was no face detected in the given boundary box, invalid is True

def resize_box(left, top, right, bottom, width, height):
    left_new = left
    right_new = right
    top_new = top
    bottom_new = bottom

    if (left - 20) > 0 :
        left_new -= 20
    else :
        left_new = 0
    #print("left", left_new)

    if right + 20 < width:
        right_new = right_new + 20
    else :
        right_new = width - 1
    #print("right", right_new)

    if (top - 20) > 0:
        top_new -= 20
    else :
        top_new = 0
    #print("top", top_new)

    if bottom + 20 < height:
        bottom_new = bottom_new + 20
    else :
        bottom_new = height - 1
    #print("bottom", bottom_new)
    return left_new, top_new, right_new, bottom_new

def main():
    #read image
    image_path = sys.argv[1]
    image = Image.open(image_path)

    #read json
    json_path = "faces.json"
    json_f = open(json_path)
    faces = json.load(json_f)

    last_image_name = image_path

    #parse faces and classify each face
    #todo: does it have index (like android) or only faces? (currently has index)
    #todo: face is not going to be classified(foreground) sends null?
    for face in faces:
        for index in face:
            if(face[index]["isBackground"] == False):
                continue
            properties = face[index]
            left = properties["left"]
            top = properties["top"]
            right = properties["left"] + properties["width"]
            bottom = properties["top"] + properties["height"]

            # draw.rectangle([(left, top), (right, bottom)], outline="red", fill="magenta")
            # image.save("isitface{}.jpg".format(face), "JPEG")

            left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)
            single_face = image.crop((left, top, right, bottom))

            #single_face.save("{}_cropped.jpg".format(index))
            #print("Benim croplar size:", single_face.size)

            age, gender, race = classification.classify(single_face)
            face[index]["age"] = age
            face[index]["gender"] = gender
            face[index]["skinColor"] = race

            # retrieve image from database here (called db_image)
            db_image = firebase_connection.retrieve_image_from_database(age, gender, race)

            blended = blending.blend_faces(db_image.convert("RGB"), single_face.convert(
                "RGB"))  # single_face.convert('RGB')) #is in PIL IMAGE FORMAT
            if blended is None:
                face[index]["invalid"] = True
            else:
                face[index]["invalid"] = False
                image.paste(blended, (left, top))
                last_image_name = 'output_blended{}.png'.format(index)
                image.save(last_image_name)
                # raise InvalidUsage("No destination face found! Remove box from image!", status_code=410)
                # image = blended

    with open('faces.json', 'w') as fp:
        json.dump(faces, fp)
    print(last_image_name)

if __name__ == "__main__":
    main()