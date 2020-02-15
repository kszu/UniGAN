from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np
from PIL import Image
import os
from werkzeug.utils import secure_filename
from skimage import io, transform

# import matplotlib.pyplot as plt

# configuration
DEBUG = True

# load model
logreg_model = pickle.load(open("model_.pkl", "rb"))

# instatiate app
app = Flask(__name__)
app.config.from_object(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
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


@app.route("/image", methods=["GET", "POST"])
def image_transformation():

    """
    user submits an image to a form
    save image to local directory (UPLOAD_FOLDER)
    convert image to grayscale

    """

    if request.method == "POST":
        file = request.files["image"]

        if file and allowed_file(file.filename):
            # save original to directory
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            # read image and transform to grayscale
            im = io.imread(file, plugin="matplotlib")
            gray = Image.fromarray(im).convert("L")

            # save grayscale
            gray_filename = "gray" + filename
            gray.save(os.path.join(app.config["UPLOAD_FOLDER"], gray_filename))

            # define input image and output image prior to returning on webpage
            input = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            output = os.path.join(app.config["UPLOAD_FOLDER"], gray_filename)

        return render_template("image.html", input=input, output=output)
    else:
        return render_template("image.html", input="", output="")


if __name__ == "__main__":
    app.run()
