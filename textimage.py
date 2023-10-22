import pytesseract
from PIL import Image
image = Image.open('your_image.png')
text = pytesseract.image_to_string(image)
