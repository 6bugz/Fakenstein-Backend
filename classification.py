from torchvision import transforms
from torch.utils.data import Dataset, DataLoader
import torch

class FaceDataset(Dataset):
  def __init__(self, img, **kwargs) :
    self.img = img

  def __len__(self) :
    return 1

  def __getitem__(self, index) :
    img = self.img
    preprocess = transforms.Compose([
      transforms.Resize(256),
      transforms.CenterCrop(224),
      transforms.ToTensor(),
      transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), ])
    input_tensor = preprocess(img)
    return input_tensor, 0


def get_dataset(image) :
  dataset = FaceDataset(image)
  return dataset

# ------ CLASSIFY IMAGES ACC TO AGE-GENDER-RACE -----------
""" PyTorch for Gender"""
def classify_gender(image, device):
  dataset = get_dataset(image)
  loader = DataLoader(dataset, batch_size=1, shuffle=False)
  model = torch.load("models/classification/resnet_new_gender.pth", device)

  model.to(device)
  model.eval()

  with torch.no_grad():
    for data, target in loader:
      data = data.to(device)
      output = model(data.float())
      if output > 0.5: #male
        return 1
      else:
        return 0

""" PyTorch for Age """
def classify_age(image, device):
  dataset = get_dataset(image)
  loader = DataLoader(dataset, batch_size=1, shuffle=False)
  model = torch.load("models/classification/resnet_new_age.pth", device)

  model.to(device)
  model.eval()

  with torch.no_grad():
    for data, target in loader:
      data = data.to(device)
      output = model(data.float())
      if output > 0.5: #young
        return 1
      else:
        return 0


""" Detects race """
def classify_race(image, device):
  dataset = get_dataset(image)
  loader = DataLoader(dataset, batch_size=1, shuffle=False)
  model = torch.load("models/classification/resnet_race.pth", device)
  model.to(device)
  model.eval()

  with torch.no_grad():
    for data, target in loader:
      data = data.to(device)
      output = model(data.float())
      if output > 0.5: #dark
        return 1
      else:
        return 0


def classify(image):
  use_gpu = torch.cuda.is_available()
  if use_gpu :
    device = torch.device("cuda")
  else :
    device = torch.device("cpu")

  gender = classify_gender(image, device)
  age = classify_age(image, device)
  race = classify_race(image, device)

  print('Gender',gender)
  print('Age',age)
  print('Race',race)

  return age, gender, race