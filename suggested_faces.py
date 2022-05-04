#save suggested faces

import firebase_admin
from firebase_admin import credentials
from firebase import firebase, Firebase
import os
import random
from PIL import Image
import json
import sys
import shutil

database_path = "https://fakenstein-239a1-default-rtdb.europe-west1.firebasedatabase.app"
storage_path = "fakenstein-239a1.appspot.com"

if not firebase_admin._apps:
    cred = credentials.Certificate('fakenstein-239a1-firebase-adminsdk-4rprv-d88ff62cf1.json')
    default_app = firebase_admin.initialize_app(cred, {'databaseURL': database_path})

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="fakenstein-239a1-firebase-adminsdk-4rprv-d88ff62cf1.json"
firebase = firebase.FirebaseApplication(database_path)

json_path = "faces.json"
json_f = open(json_path)
faces = json.load(json_f)

index = sys.argv[1]
print(index)
print(faces)

def retrieve_suggested_faces(age, gender, race):
    age_str = "old"
    if age == 1:
        age_str = "young"

    gender_str = "female"
    if gender == 1:
        gender_str = "male"

    skin_str = "pale"
    if race == 1:
        skin_str = "dark"
    path = gender_str + '/' + age_str + '/' + skin_str

    #get name of the image to download (randomly chosen)
    all_image_names = firebase.get(path, None)
    #print(path)
    #print(all_image_names)
    #print(len(all_image_names.keys()))


    (id1, id2, id3) = random.sample(list(all_image_names.values()), 3)

    #print(id, image_no)

    #download image
    config = {
      "apiKey": "fakenstein-239a1-firebase-adminsdk-4rprv-d88ff62cf1.json",
      "authDomain": "fakenstein-239a1.firebaseapp.com",
      "databaseURL": database_path,
      "storageBucket": storage_path
    }
    firebase_images = Firebase(config)
    storage = firebase_images.storage()

    if os.path.isdir("suggested_faces") == False:
        os.mkdir("suggested_faces")

    if os.path.isdir("suggested_faces/{}".format(index)) == False:
        os.mkdir("suggested_faces/{}".format(index))

    ids = [id1, id2, id3]
    for i in range(3):
        image_name = "suggested_faces/{}/{}.jpg".format(index, i)
        storage.child("images/{}".format(ids[i])).download(image_name)
        #read_image = Image.open(image_name)

    #delete image
    #os.remove(image_name)


retrieve_suggested_faces(faces[index]["age"],faces[index]["gender"], faces[index]["skinColor"])