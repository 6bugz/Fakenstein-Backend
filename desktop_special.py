#special feature
# blend with a selected face(from face library or suggested faces)

import sys
from PIL import Image
import json
import blending

#INPUT: reads image path(original) and selected and the face index from system args, reads faces.json from filesystem
#PRINT: prints error if there were no faces detected in the image
#SAVE: saves the reblended faces into faces.json file with the following values:
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

    if right + 20 < width:
        right_new = right_new + 20
    else :
        right_new = width - 1

    if (top - 20) > 0:
        top_new -= 20
    else :
        top_new = 0

    if bottom + 20 < height:
        bottom_new = bottom_new + 20
    else :
        bottom_new = height - 1

    return left_new, top_new, right_new, bottom_new

def main():
    #read image
    image_path = sys.argv[1]
    image = Image.open(image_path)

    #read selected image
    selected_image_path = sys.argv[2]
    selected_image = Image.open(selected_image_path)

    # read selected image
    index = sys.argv[3]

    #read json
    json_path = "faces.json"
    json_f = open(json_path)
    faces = json.load(json_f)

    last_image_name = image_path

    #in json, read parameter: reblend: if it is True, reblend the face, else don't touch it!
    face = faces[index]
    left = face["left"]
    top = face["top"]
    right = face["left"] + face["width"]
    bottom = face["top"] + face["height"]

    left, top, right, bottom = resize_box(left, top, right, bottom, image.width, image.height)
    single_face = image.crop((left, top, right, bottom))
    #single_face.save("{}_cropped.jpg".format(index))

    blended = blending.blend_faces(selected_image.convert("RGB"), single_face.convert("RGB"))
    if blended is None:
        faces[index]["invalid"] = True

    else:
        faces[index]["invalid"] = False
        image.paste(blended, (int(left), int(top)))
        last_image_name = "output.jpg"
        image.save(last_image_name)

    with open('faces.json', 'w') as fp:
        json.dump(faces, fp) #in case anything was invalid

    print(last_image_name)

if __name__ == "__main__":
    main()
