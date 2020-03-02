from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from flask_cors import CORS
import subprocess
from subprocess import Popen, PIPE
from subprocess import check_output
import pandas as pd
import pickle
import sklearn
import numpy as np
from PIL import Image
import os
from werkzeug.utils import secure_filename
from skimage import io, transform

# import matplotlib.pyplot as plt

# configuration
DEBUG = True

# load model
# logreg_model = pickle.load(open("model_.pkl", "rb"))

# instatiate app
app = Flask(__name__)
app.config.from_object(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["UniGAN_INPUT_FOLDER"] = "static/input_images"
app.config["UniGAN_OUTPUT_FOLDER"] = "static/output/UniGAN_128/samples_testing_2"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "txt"}

# define user defined functions
def allowed_file(filename):
    """
    read and test for allowed file types
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# define routes
@app.route("/", methods=["GET", "POST"])
def load_home():
    """
    Load home page
    """
    
    return render_template("home.html", input="", output="")


@app.route("/unigan", methods=["GET", "POST"])
def unigan():

    """
    user submits an image to a form
    save image to local directory (UniGAN_INPUT_FOLDER)
    run model
    return images

    """

    if request.method == "POST":
        file = request.files["image"]
        transform_option = request.form.get("transform_option")
        
        if file and allowed_file(file.filename):
            # save original to directory
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], filename))
            
            python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], filename),
                                                 os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], "flaskapp_img.jpg"))
            stdout = check_output([python_command], shell=True)
            
            # im = io.imread(os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], filename), plugin="matplotlib")
            # resize_factor = 1
            # size = int(np.floor(Image.fromarray(im).width / resize_factor)), int(np.floor(Image.fromarray(im).height / resize_factor))
            # im_mod = Image.fromarray(im).resize(size)
            # im_mod.save(os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], "flaskapp_img.jpg"))

            py_file = os.path.join(app.root_path, "test.py")
            # python_command = "CUDA_VISIBLE_DEVICES=0 python {0} --experiment_name UniGAN_128 --flask_path {1}".format(py_file, app.root_path)
            # python_command = "CUDA_VISIBLE_DEVICES=0 python /var/www/html/flaskapp/test.py --experiment_name AttGAN_128 --flask_path /var/www/html/flaskapp"
            # app.logger.info(python_command)
            # stdout = check_output([python_command], shell=True)

            python_command = "CUDA_VISIBLE_DEVICES=0 python /var/www/html/flaskapp_unigan/test.py --experiment_name UniGAN_128 --flask_path /var/www/html/flaskapp_unigan"
            app.logger.info(python_command)
            stdout = check_output([python_command], shell=True)

            # define input image and output image prior to returning on webpage
            
            input = os.path.join(app.config["UniGAN_INPUT_FOLDER"], "flaskapp_img.jpg")
            output = os.path.join(app.config["UniGAN_OUTPUT_FOLDER"], "1.jpg")

            app.logger.info(input)
            app.logger.info(output)

        return render_template("unigan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1))
    else:
        input = os.path.join(app.config["UniGAN_INPUT_FOLDER"], "flaskapp_img.jpg")
        output = os.path.join(app.config["UniGAN_OUTPUT_FOLDER"], "1.jpg")

        return render_template("unigan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1))

@app.route("/what_is_unigan", methods=["GET"])
def load_what_is_unigan():
    """
    Load what is UniGAN page
    """

    return render_template("what_is_unigan.html")

@app.route("/team", methods=["GET"])
def load_team():
    """
    Load team page
    """

    return render_template("team.html")

@app.route("/how_it_works", methods=["GET"])
def load_how_it_works():
    """
    Load how it works page
    """

    return render_template("how_it_works.html")

if __name__ == "__main__":
    app.run()
