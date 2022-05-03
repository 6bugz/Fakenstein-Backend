from PIL import Image, ImageFilter

def blur_image(image):
    #blurImage = image.filter(ImageFilter.BLUR)
    blurImage = image.filter(ImageFilter.BoxBlur(5))
    return blurImage
