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
INPUT_IMAGE_NAME = 'user_image.jpg'
OUTPUT_OBJ_NAME = 'user_image_0.obj'
INPUT_IMAGE_PATH = os.path.join(IMAGES, INPUT_IMAGE_NAME)
OUTPUT_OBJ_PATH = os.path.join(IMAGES, OUTPUT_OBJ_NAME)

# 2 things needed for frontend:
# 1) face render + mask for 3d static image
# 2) just mask for AR

@app.route('/api/generate_facemask', methods=['GET', 'POST'])
def generate_facemask():
    # Save image sent as GET/POST request
    encoded_image = request.data
    decoded_image = base64.decodestring(encoded_image[22:])
    print('generate_facemask called, directory: ' + os.getcwd())
    
    # Generate 3D models and make fitter
    pretty_obj, original_obj = generate_3d_models(decoded_image)
    fitter_filename = construct_fitter(original_obj)
    
    # Send fitter back
    return send_file(fitter_filename, mimetype='text/plain') #'images/user_image_0.obj', mimetype='text/plain')


@app.route('/api/generate_facemask_fit', methods=['GET', 'POST'])
def generate_facemask_fit():
    # Save image sent as GET/POST request
    encoded_image = request.data
    decoded_image = base64.decodestring(encoded_image[22:])
    print('generate_facemask_fit called, directory: ' + os.getcwd())
    
    # Generate 3D models and make fitter-facemask fit
    pretty_obj, original_obj = generate_3d_models(decoded_image)
    
    ## TODO (cdot): Replace (pretty_obj) with output from function generating 
    ## facemask + fit obj
    facemask_fit_filename = (pretty_obj)
    
    # Send fitter back
    return send_file(facemask_fit_filename, mimetype='text/plain') #'images/user_image_0.obj', mimetype='text/plain')
    
def generate_3d_models(decoded_image):
    """
    1) Save image received as GET/POST request
    2) Call 3DDFA to generate 3D model of face
    3) Pass it off to cdot for SolidWorks wizardry
    
    The model files are saved wherever the original image is
    """
    f = open(INPUT_IMAGE_PATH, 'wb')
    f.write(decoded_image)
    f.close()    
    
    # Generate 3d face models
    os.chdir(os.path.join(os.getcwd(), '3DDFA'))
    subprocess.call(f"python main.py -f ../{INPUT_IMAGE_PATH}", shell=True)
    os.chdir('..')
    
    #return app.send_static_file('user_image_0.obj')
    print('Current dir: ' + os.getcwd())
    pretty_obj, original_obj = simplify_obj(OUTPUT_OBJ_PATH)
    
    return pretty_obj, original_obj