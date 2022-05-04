from PIL import Image, ImageFilter

def blur_image(image):
    blurImage = image.filter(ImageFilter.GaussianBlur(3))
    return blurImage
