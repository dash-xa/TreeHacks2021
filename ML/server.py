from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import base64
import subprocess
import os
from simplify_obj_to_stl import simplify_obj
from stl_construction import construct_fitter

app = Flask(__name__, static_url_path='/images') 
CORS(app)

IMAGES = 'images'
IMAGE_NAME = 'user_image.jpg'
IMAGE_PATH = os.path.join(IMAGES, IMAGE_NAME)


@app.route('/api/generate', methods=['GET', 'POST'])
def handle_image():
    # Save image locally
    encoded_image = request.data
    decoded_image = base64.decodestring(encoded_image[22:])
    print('Handle image called. Directory: ' + os.getcwd())
    print('Image path: ' + IMAGE_PATH)
    f = open(IMAGE_PATH, 'wb')
    f.write(decoded_image)
    f.close()    
    # Generate 3d face models
    construct_face3d()
    
    #return app.send_static_file('user_image_0.obj')
    print('Current dir: ' + os.getcwd())
    pretty_obj, original_obj = simplify_obj('images/user_image_0.obj')
    
    fitter_filename = construct_fitter(original_obj)
    
    return send_file(fitter_filename, mimetype='text/plain')#'images/user_image_0.obj', mimetype='text/plain')

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
    os.chdir('..')
