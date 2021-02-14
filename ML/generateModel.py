# Basically a wrapper for 3DDFA/main.py
import subprocess
import sys
import os

# To generate an image, run
# `python generateModel.py <image name>`
# in bash command line

# Code for making processing static test image:
# FILENAME = 'cdot_test.png'
# subprocess.call(f"python main.py -f pictures/{FILENAME}", shell=True)

IMAGES = 'images'
IMAGE_NAME = 'user_image.jpg'
IMAGE_PATH = os.path.join(IMAGES, IMAGE_NAME)
    
if __name__ == "__main__":
    #f = open(IMAGE_PATH, 'wb')
    #f.write(decoded_image)
    #f.close()    
    os.chdir(os.path.join(os.getcwd(), '3DDFA'))
    subprocess.call(f"python main.py -f ../{sys.argv[1]}", shell=True)
    os.chdir(os.path.join(os.path.dirname( __file__ ), '..' ))
    print(f"Images Generated in folder {os.path.join(os.path.dirname(sys.argv[1]), '..' )}")
