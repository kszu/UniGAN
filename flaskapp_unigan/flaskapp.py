from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, send_file, make_response, send_from_directory
from flask_cors import CORS
from s3_utils import list_files_in_s3, download_file_from_s3, upload_file_to_s3, randomStringDigits, delete_file_in_s3
import requests
import subprocess
from subprocess import Popen, PIPE
from subprocess import check_output
import pandas as pd
import pickle
import sklearn
import numpy as np
import datetime
from PIL import Image
import os, time
from werkzeug.utils import secure_filename
from skimage import io, transform
from unigan.unigan import unigan_bp, hello_bp

import logging
logging.basicConfig(filename='/var/www/html/flaskapp_unigan/debug1.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

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

app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["INPUT_FOLDER"] = "static/input_images"
app.config["OUTPUT_FOLDER_SIMPLE"] = "static/output/UniGAN_128/samples_testing_2"
app.config["OUTPUT_FOLDER_SLIDE"] = "static/output/UniGAN_128/samples_testing_slide" # e.g. Women_-2_2_0.5/1.jpg for subdir/output_file
app.config["OUTPUT_FOLDER_SUBCATS"] = "static/output/UniGAN_128/samples_testing_subcategories_2"
app.config["TEST_LABELS_FOLDER"] = "data/zappos_50k"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "txt"}
S3_BUCKET = "w210-capstone-project"

# define routes
@app.route("/", methods=["GET", "POST"])
def load_home():
    """
    Load home page
    """
    
    return render_template("home.html", input="", output="")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.ico', mimetype='image/vnd.microsoft.icon')

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

@app.route("/storage")
def storage():
    cookie_S3dir = request.cookies.get('cookieS3dir')
    contents = list_files_in_s3(S3_BUCKET, "UniGAN-my-images/" + cookie_S3dir)
    resp = make_response(render_template('storage.html', contents=contents, cookie_val=cookie_S3dir))

    return resp

@app.route("/upload", methods=['POST'])
def upload():
    if request.method == "POST":
        f = request.files['file']
        cookie_val = request.cookies.get('somecookiename')

        f.save(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"], f.filename))
        upload_file_to_s3(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"], f.filename), S3_BUCKET, "UniGAN-my-images/"+cookie_val, f.filename)

        return redirect("/storage")
    
@app.route("/delete_image", methods=['GET'])
def delete_image():
    cookie_S3dir = request.cookies.get('cookieS3dir')
    img_arg = request.args.get('image')
    if cookie_S3dir in img_arg:
        delete_file_in_s3(S3_BUCKET, img_arg)

    return redirect("/unigan")
    
@app.route("/unigan", methods=["GET", "POST"])
def unigan():

    """
    user submits an image to a form
    save image to local directory (INPUT_FOLDER)
    run model
    return images

    """
    img_arg = request.args.get('image_url')
    # gender = request.args.get('gender')
    unigan_method = request.args.get('method')
    # shoe_type = request.args.get('shoe_type')
    images = ["sample_shoe1.jpg", "sample_shoe2.jpg", "sample_shoe3.jpg", "sample_shoe4.jpg", "sample_shoe5.jpg", "sample_shoe6.jpg", "sample_shoe7.jpg"]
    images_info = {"sample_shoe1.jpg": ["male", "ankle"], "sample_shoe2.jpg": ["male", "flat"],
                   "sample_shoe3.jpg": ["female", "heel"], "sample_shoe4.jpg": ["female", "flat"], "sample_shoe5.jpg": ["female", "flat"],
                   "sample_shoe6.jpg": ["male", "athletic"], "sample_shoe7.jpg": ["male", "athletic"]}

    if request.method == "POST" or (request.method == "GET" and img_arg):
        cookie_S3dir = request.cookies.get('cookieS3dir')
        
        if request.method == "POST":
            gender = request.form.get('gender')
            unigan_method = request.form.get('method')
            shoe_type = request.form.get('shoe_type')
            file = request.files["image"]
            filename = secure_filename(file.filename)
            filename_root = os.path.splitext(os.path.split(filename)[1])[0]
            filename_ext = os.path.splitext(os.path.split(filename)[1])[1]
            s3_filename = filename_root + "___" + gender + "___" + shoe_type + filename_ext
            file_savepath = os.path.join(app.root_path, app.config["INPUT_FOLDER"], filename)
            file.save(file_savepath)
            make_bg_white(file_savepath, file_savepath)
            cookie_S3dir = request.cookies.get('cookieS3dir')
            img_arg = "UniGAN-my-images/" + cookie_S3dir + "/" + s3_filename
            upload_file_to_s3(os.path.join(app.root_path, app.config["INPUT_FOLDER"], filename), S3_BUCKET, "UniGAN-my-images/"+cookie_S3dir, s3_filename)

            python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["INPUT_FOLDER"], filename),
                                                 os.path.join(app.root_path, app.config["INPUT_FOLDER"], "flaskapp_img.jpg"))
            stdout = check_output([python_command], shell=True)
            
        else:
            if "___" in img_arg:
                img_url = "https://w210-capstone-project.s3.us-east-2.amazonaws.com/" + img_arg
                filename = img_arg.split("/")[2]
                filename_root = os.path.splitext(os.path.split(filename)[1])[0]
                (filename_orig, gender, shoe_type) = filename_root.split("___")
            else:
                img_url = "http://unigan.io/static/input_images/" + img_arg
                gender = images_info[img_arg][0]
                shoe_type = images_info[img_arg][1]

            app.logger.info(img_url, gender, shoe_type)
            r = requests.get(img_url)
            with open(os.path.join(app.root_path, app.config["INPUT_FOLDER"], "flaskapp_img.jpg"), 'wb') as f:
                f.write(r.content)

        # Ensure my_images contains latest uploaded file
        my_images = list_files_in_s3(S3_BUCKET, "UniGAN-my-images/" + cookie_S3dir)

        if unigan_method == "gender":
            if gender == "female":
                # gender_label = "flaskapp_img.jpg -1 1 -1"
                python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "female_img_test_label.txt"),
                                                     os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label.txt"))
            else: # male
                # gender_label = "flaskapp_img.jpg 1 -1 -1"
                python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "male_img_test_label.txt"),
                                                     os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label.txt"))
        
            stdout = check_output([python_command], shell=True)

            labels = ["Original", "Reconstructed", "Male", "Unisex", "Female"]
            python_command = "CUDA_VISIBLE_DEVICES=0 python /var/www/html/flaskapp_unigan/test.py --experiment_name UniGAN_128 --flask_path /var/www/html/flaskapp_unigan"
            stdout = check_output([python_command], shell=True)
    
            date_time_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            input_newname = "flaskapp_img-" + date_time_str + ".jpg"
            output_newname = "1-" + date_time_str + ".jpg"
            python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["INPUT_FOLDER"], "flaskapp_img.jpg"),
                                                 os.path.join(app.root_path, app.config["INPUT_FOLDER"], input_newname))
            stdout = check_output([python_command], shell=True)
            python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["OUTPUT_FOLDER_SIMPLE"], "1.jpg"),
                                                 os.path.join(app.root_path, app.config["OUTPUT_FOLDER_SIMPLE"], output_newname))
            stdout = check_output([python_command], shell=True)
    
            input = os.path.join(app.config["INPUT_FOLDER"], input_newname)
            output = os.path.join(app.config["OUTPUT_FOLDER_SIMPLE"], output_newname)
    
            resp = make_response(render_template("unigan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1),
                                                 img_width=640, labels=labels, images=images, my_images=my_images, last_image=img_arg, model_type="gender"))
            return resp
        elif "slide" in unigan_method:

            slide_option = unigan_method.split("-")[1]
            if 'Men' in slide_option or 'Women' in slide_option:
                test_script = 'test_slide.py'
                if gender == "female":
                    # gender_label = "flaskapp_img.jpg -1 1 -1"
                    python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "female_img_test_label.txt"),
                                                         os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label.txt"))
                else: # male
                    # gender_label = "flaskapp_img.jpg 1 -1 -1"
                    python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "male_img_test_label.txt"),
                                                         os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label.txt"))
        
                stdout = check_output([python_command], shell=True)
            else:
                test_script = 'test_slide_subcategories.py'
                if shoe_type == "ankle":
                    python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "ankle_test_label.txt"),
                                                         os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
                elif shoe_type == "athletic":
                    python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "athletic_test_label.txt"),
                                                         os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
                elif shoe_type == "boot":
                    python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "boot_test_label.txt"),
                                                         os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
                elif shoe_type == "flat":
                    python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "flat_test_label.txt"),
                                                         os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
                elif shoe_type == "heel":
                    python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "heel_test_label.txt"),
                                                         os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))

                stdout = check_output([python_command], shell=True)

            labels = ["Original", "Less", "", "", "", "← Intensity →", "", "", "", "More"]

            python_command = "CUDA_VISIBLE_DEVICES=0 python /var/www/html/flaskapp_unigan/%s --test_att_name %s --test_int_min -2 --test_int_max 2 --test_int_step 0.5 --experiment_name UniGAN_128 --flask_path /var/www/html/flaskapp_unigan" % (test_script, slide_option)
            stdout = check_output([python_command], shell=True)
            input = os.path.join(app.config["INPUT_FOLDER"], "flaskapp_img.jpg")
            output = os.path.join(app.config["OUTPUT_FOLDER_SLIDE"], "%s_-2_2_0.5/1.jpg" % slide_option)
            resp = make_response(render_template("unigan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1),
                                                 img_width=1280, labels=labels, images=images, my_images=my_images, last_image=img_arg, model_type=unigan_method))
            return resp
        elif unigan_method == "category":
            if shoe_type == "ankle":
                python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "ankle_test_label.txt"),
                                                     os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
            elif shoe_type == "athletic":
                python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "athletic_test_label.txt"),
                                                     os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
            elif shoe_type == "boot":
                python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "boot_test_label.txt"),
                                                     os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
            elif shoe_type == "flat":
                python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "flat_test_label.txt"),
                                                     os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))
            elif shoe_type == "heel":
                python_command = "cp {0} {1}".format(os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "heel_test_label.txt"),
                                                     os.path.join(app.root_path, app.config["TEST_LABELS_FOLDER"], "test_label_subcategories.txt"))

            stdout = check_output([python_command], shell=True)

            labels = ["Original", "Reconstructed", "Ankle", "Athletic", "Boot", "Flat", "Heel"]
            python_command = "CUDA_VISIBLE_DEVICES=0 python /var/www/html/flaskapp_unigan/test_subcategories.py --experiment_name UniGAN_128 --flask_path /var/www/html/flaskapp_unigan"
            stdout = check_output([python_command], shell=True)
            input = os.path.join(app.config["INPUT_FOLDER"], "flaskapp_img.jpg")
            output = os.path.join(app.config["OUTPUT_FOLDER_SUBCATS"], "1.jpg")

            resp = make_response(render_template("unigan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1), img_width=896,
                                                 labels=labels, images=images, my_images=my_images, last_image=img_arg, model_type="category"))
            return resp
    else:
        # set cookie for s3 directory
        cookie_S3dir = request.cookies.get('cookieS3dir')

        labels = ["Original", "Reconstructed", "Male", "Unisex", "Female"]
        input = os.path.join(app.config["INPUT_FOLDER"], "no_image.jpg")
        output = os.path.join(app.config["INPUT_FOLDER"], "no_image.jpg")
    
        if cookie_S3dir is None:
            resp = make_response(render_template("unigan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1), img_width=640,
                                                 labels="", images=images, my_images="", last_image="", model_type=""))
            resp.set_cookie('cookieS3dir', randomStringDigits(8))
        else:
            my_images = list_files_in_s3(S3_BUCKET, "UniGAN-my-images/" + cookie_S3dir)
            resp = make_response(render_template("unigan.html", input=input, output=output, rand_num=np.random.randint(low=1, high=100000, size=1), img_width=640,
                                                 labels="", images=images, my_images=my_images, last_image="", model_type=""))

        return resp

def make_bg_white(input_image, output_image):
    img = Image.open(input_image).convert('RGB')
    arr = np.array(np.asarray(img))
    img.close()

    R = [(0,240),(0,240),(0,240)]
    red_range = np.logical_and(R[0][0] < arr[:,:,0], arr[:,:,0] < R[0][1])
    green_range = np.logical_and(R[1][0] < arr[:,:,0], arr[:,:,0] < R[1][1])
    blue_range = np.logical_and(R[2][0] < arr[:,:,0], arr[:,:,0] < R[2][1])
    valid_range = np.logical_and(red_range, green_range, blue_range)

    arr[np.logical_not(valid_range)] = 255

    outim = Image.fromarray(arr)
    outim.save(output_image)
    
if __name__ == "__main__":
    app.run()
