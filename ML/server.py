from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import base64
import subprocess
import os
from simplify_obj_to_stl import simplify_obj
from stl_construction import construct_fitter
import shutil

app = Flask(__name__, static_url_path='/images') 
CORS(app)

DATA = 'data'
COUNTER_FILE_NAME = 'counter.txt'
INPUT_IMAGE_NAME = 'user_image.jpg'
OUTPUT_OBJ_NAME = 'user_image_0.obj'


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
    
    
#     if IMAGES in os.listdir():
#         shutil.rmtree(IMAGES)
#         os.mkdir(IMAGES)
    with open(COUNTER_FILE_NAME, 'r+t') as counterFile:
        counter = int(counterFile.read()) + 1
        os.mkdir(f'data/{counter}')
        with open(f'data/{counter}/user_image.jpg', 'wb') as imageFile:
            # save file to data/{counter}/user_image.jpg
            imageFile.write(decoded_image)
        counterFile.seek(0)
        counterFile.write(str(counter))
        ## TODO: Dump terminal log to user's folder
       
    # Generate 3d face models
    os.chdir(os.path.join(os.getcwd(), '3DDFA'))
    subprocess.call(f"python main.py -f ../data/{counter}/user_image.jpg | tee ../data/{counter}/log.txt", shell=True)
    os.chdir('..') # change back to root directory
    
    
    #return app.send_static_file('user_image_0.obj')
#     print('Current dir: ' + os.getcwd())
    pretty_obj, original_obj = simplify_obj(f"data/{counter}/{OUTPUT_OBJ_NAME}")
    
    return pretty_obj, original_obj