import blur
import sys
from PIL import Image
import json

def main():
    #read image
    image_path = sys.argv[1]
    image = Image.open(image_path)

    #read json
    json_path = "faces.json"
    json_f = open(json_path)
    faces = json.load(json_f)

    last_image_name = image_path

    #todo: which face to blur - what is the input
    for face in faces:
        properties = faces[face]
        left = properties["left"]
        top = properties["top"]
        right = properties["left"] + properties["width"]
        bottom = properties["top"] + properties["height"]
        single_face = image.crop((left, top, right, bottom))
        blurred_img = blur.blur_image(single_face)
        image.paste(blurred_img, (int(left), int(top)))

        last_image_name = 'blurred{}.png'.format(face)
        image.save(last_image_name)

    print(last_image_name)

if __name__ == "__main__":
    main()