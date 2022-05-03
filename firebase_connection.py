import firebase_admin
from firebase_admin import credentials
from firebase import firebase, Firebase
import os
import random
from PIL import Image

database_path = "https://fakenstein-239a1-default-rtdb.europe-west1.firebasedatabase.app"
storage_path = "fakenstein-239a1.appspot.com"

if not firebase_admin._apps:
    cred = credentials.Certificate('fakenstein-239a1-firebase-adminsdk-4rprv-d88ff62cf1.json')
    default_app = firebase_admin.initialize_app(cred, {'databaseURL': database_path})

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="fakenstein-239a1-firebase-adminsdk-4rprv-d88ff62cf1.json"
firebase = firebase.FirebaseApplication(database_path)

def retrieve_image_from_database(age, gender, race):
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

    id, image_no = random.choice(list(all_image_names.items()))
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

    if os.path.isdir("blend_faces") == False:
        os.mkdir("blend_faces")

    image_name = "blend_faces/retrieved_face_{}.jpg".format(image_no)
    storage.child("images/{}".format(image_no)).download(image_name)
    read_image = Image.open(image_name)

    #delete image
    os.remove(image_name)

    return read_image
