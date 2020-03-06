from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from flask_cors import CORS
import requests
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
from unigan.unigan import unigan_bp, hello_bp

# configuration
DEBUG = True

# instatiate app
app = Flask(__name__)
app.config.from_object(__name__)

app.register_blueprint(unigan_bp)
app.register_blueprint(hello_bp)

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

app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["UniGAN_INPUT_FOLDER"] = "static/input_images"
app.config["UniGAN_OUTPUT_FOLDER"] = "static/output/UniGAN_128/samples_testing_2"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "txt"}

@app.route("/unigan", methods=["GET", "POST"])
def unigan():

    """
    user submits an image to a form
    save image to local directory (UniGAN_INPUT_FOLDER)
    run model
    return images

    """
    img_url = request.args.get('img_url')
    if request.method == "POST" or (request.method == "GET" and img_url):
        if request.method == "POST":
            file = request.files["image"]
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], filename))
            python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], filename),
                                                 os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], "flaskapp_img.jpg"))
            stdout = check_output([python_command], shell=True)
            
        else:
            r = requests.get(img_url)
            with open(os.path.join(app.root_path, app.config["UniGAN_INPUT_FOLDER"], "flaskapp_img.jpg"), 'wb') as f:
                f.write(r.content)            
        
        python_command = "CUDA_VISIBLE_DEVICES=0 python /var/www/html/flaskapp_unigan/test.py --experiment_name UniGAN_128 --flask_path /var/www/html/flaskapp_unigan"
        stdout = check_output([python_command], shell=True)

        input = os.path.join(app.config["UniGAN_INPUT_FOLDER"], "flaskapp_img.jpg")
        output = os.path.join(app.config["UniGAN_OUTPUT_FOLDER"], "1.jpg")

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
