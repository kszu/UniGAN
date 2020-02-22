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

app.config["AttGAN_INPUT_FOLDER"] = "static/input_images/data"
app.config["AttGAN_OUTPUT_FOLDER"] = "static/output/AttGAN_128/samples_testing_2"
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
def logreg_form():

    """
    run simple logistic regression model and return output of model
    """

    if request.method == "POST":
        input = request.form.get("submission")

        model_input = np.array(int(input))
        result = logreg_model.predict(model_input.reshape(-1, 1))

        return render_template("home.html", input=int(model_input), output=int(result))
    else:
        return render_template("home.html", input="", output="")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """
    functioning, but not currently necessary. return url endpoint with uploaded filename.
    """
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/test1", methods=["GET", "POST"])
def test1():

    """
    test calling python script from command line
    """

    if request.method == "GET":
        # py_file = os.path.join(app.root_path, "tmp1.py")
        py_file = os.path.join(app.root_path, "test.py")

        # python_command = "python '{0}'".format(py_file)
        python_command = "CUDA_VISIBLE_DEVICES=0 python {0} --experiment_name AttGAN_128 --flask_path {1}".format(py_file, app.root_path)
        try:
            stdout = check_output([python_command], shell=True)
            return """<title>Success</title>
                      <h1>Images generated!</h1>
                      """
        except subprocess.CalledProcessError as e:
            return "An error occurred while trying to fetch task status updates."
    else:
        return """<title>500 Error</title>
               <h1>Error!</h1>
               <p>Only GET is supported right now</p>""", 500

@app.route('/test2')
def test2():
    input = os.path.join(app.config["AttGAN_INPUT_FOLDER"], "004501.jpg")
    output = os.path.join(app.config["AttGAN_OUTPUT_FOLDER"], "1.jpg")

    if request.method == "GET":
        return render_template("attgan_image.html", input=input, output=output)

@app.route("/image", methods=["GET", "POST"])
def image_transformation():

    """
    user submits an image to a form
    save image to local directory (UPLOAD_FOLDER)
    convert image to grayscale

    """

    if request.method == "POST":
        file = request.files["image"]
        transform_option = request.form.get("transform_option")
        
        if file and allowed_file(file.filename):
            # save original to directory
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"], filename))

            if transform_option == "RGB":
                # read image and transform to grayscale
                im = io.imread(file, plugin="matplotlib")
                im_mod = Image.fromarray(im).convert("L")
                im_mod_filename = "im_mod_rgb_" + filename
            elif transform_option == "Rotate":
                # read image and rotate
                im = io.imread(file, plugin="matplotlib")
                im_mod = Image.fromarray(im).rotate(90)
                im_mod_filename = "im_mod_rotate_" + filename

            im_mod.save(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"], im_mod_filename))

            # define input image and output image prior to returning on webpage
            input = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            output = os.path.join(app.config["UPLOAD_FOLDER"], im_mod_filename)

        return render_template("image.html", input=input, output=output)
    else:
        return render_template("image.html", input="", output="")

@app.route("/attgan", methods=["GET", "POST"])
def attgan():

    """
    user submits an image to a form
    save image to local directory (AttGAN_INPUT_FOLDER)
    run model
    return images

    """

    if request.method == "POST":
        file = request.files["image"]
        transform_option = request.form.get("transform_option")
        
        if file and allowed_file(file.filename):
            # save original to directory
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.root_path, app.config["AttGAN_INPUT_FOLDER"], filename))

            im = io.imread(os.path.join(app.root_path, app.config["AttGAN_INPUT_FOLDER"], filename), plugin="matplotlib")
            if Image.fromarray(im).height > 256:
                resize_factor = Image.fromarray(im).height / 256
            else:
                resize_factor = 1
                
            size = int(np.floor(Image.fromarray(im).width / resize_factor)), int(np.floor(Image.fromarray(im).height / resize_factor))
            im_mod = Image.fromarray(im).resize(size)
            im_mod.save(os.path.join(app.root_path, app.config["AttGAN_INPUT_FOLDER"], "004501.jpg"))

            py_file = os.path.join(app.root_path, "test.py")
            python_command = "CUDA_VISIBLE_DEVICES=0 python {0} --experiment_name AttGAN_128 --flask_path {1}".format(py_file, app.root_path)
            stdout = check_output([python_command], shell=True)

            # define input image and output image prior to returning on webpage
            
            input = os.path.join(app.config["AttGAN_INPUT_FOLDER"], "004501.jpg")
            output = os.path.join(app.config["AttGAN_OUTPUT_FOLDER"], "1.jpg")

        return render_template("attgan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1))
    else:
        return render_template("attgan.html", input="", output="", rand_num="")


if __name__ == "__main__":
    app.run()
