from PIL import Image, ImageFilter

def blur_image(image):
    blurImage = image.filter(ImageFilter.GaussianBlur(3))
    #blurImage.show()
    return blurImage
    # Save blurImage
    #blurImage.save('images/simBlurImage.jpg')