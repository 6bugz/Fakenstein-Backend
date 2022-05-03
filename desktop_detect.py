import sys
from PIL import Image
import detection
import json

#INPUT: reads image path from system args
#PRINT: prints error if there were no faces detected in the image
#SAVE: saves the detected faces into faces.json file with the following values:
#isBackground: if the face is in background - True, else - False
#height: height of boundary box
#width: width of boundary box
#top: y of boundary box (left top corner)
#left: x of boundary box (left top corner)

def main():
    image_path = sys.argv[1]
    image = Image.open(image_path)

    boundary_boxes = detection.detect(image)

    if boundary_boxes is None:
        print("error")
    else:
        with open('faces.json', 'w') as fp:
            json.dump(boundary_boxes, fp)

if __name__ == "__main__":
    main()