from flask import Flask, jsonify, request
from flask_cors import CORS
import base64
import subprocess
import os

app = Flask(__name__) 
CORS(app)

IMAGES = 'images'
IMAGE_NAME = 'user_image.jpg'
IMAGE_PATH = os.path.join(IMAGES, IMAGE_NAME)


@app.route('/api/generate', methods=['GET', 'POST'])
def handle_image():
    # Save image locally
    encoded_image = request.data
    print(encoded_image)
    decoded_image = base64.decodestring(encoded_image[22:])
    f = open(IMAGE_PATH, 'wb')
    f.write(decoded_image)
    f.close()    
    # Generate 3d face models
    construct_face3d()
    
    return decoded_image

def construct_face3d():
    """
    1) Save image received as GET/POST request
    2) Call 3DDFA to generate 3D model of face
    3) Pass it off to cdot for SolidWorks wizardry
    
    The model files are saved wherever the original image is
    """ 
    # Change path to execute 3DDFA scripts
    os.chdir(os.path.join(os.getcwd(), '3DDFA'))
    # Call magic function from command line
    subprocess.call(f"python main.py -f ../{IMAGE_PATH}", shell=True)
    # Return to normal directory
    os.chdir(os.path.join(os.path.dirname( __file__ ), '..' ))
