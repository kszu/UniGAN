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

import logging
logging.basicConfig(filename='/var/www/html/flaskapp_unigan/debug1.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# imports for running test.py (UniGAN app)
import imlib as im
import pylib as py
import tensorflow as tf
import tflib as tl
import tqdm
import data
import module

# configuration
DEBUG = True
os.environ["CUDA_PATH"] = "/usr/local/cuda"

py.arg('--flask_path', default='/var/www/html/flaskapp_unigan')
py.arg('--img_dir', default='./data/zappos_50k/images')
py.arg('--test_label_path', default='./data/zappos_50k/test_label.txt')
py.arg('--test_int', type=float, default=2)
py.arg('--experiment_name', default='UniGAN_128')
args_ = py.args()

# output_dir
output_dir = os.path.join(args_.flask_path, py.join('output', args_.experiment_name))

# save settings
args = py.args_from_yaml(py.join(output_dir, 'settings.yml'))
args.__dict__.update(args_.__dict__)

# others
n_atts = len(args.att_names)

sess = tl.session()
sess.__enter__()  # make default

# ==============================================================================
# =                               data and model                               =
# ==============================================================================

# data
flask_img_dir = os.path.join(args.flask_path, args.img_dir)
flask_test_label_path = os.path.join(args.flask_path, args.test_label_path)
test_dataset, len_test_dataset = data.make_celeba_dataset(flask_img_dir, flask_test_label_path, args.att_names, args.n_samples,
                                                          load_size=args.load_size, crop_size=args.crop_size,
                                                          training=False, drop_remainder=False, shuffle=False, repeat=None)
test_iter = test_dataset.make_one_shot_iterator()


# ==============================================================================
# =                                   graph                                    =
# ==============================================================================

def sample_graph():
    # ======================================
    # =               graph                =
    # ======================================

    if not os.path.exists(py.join(output_dir, 'generator.pb')):
        # model
        Genc, Gdec, _ = module.get_model(args.model, n_atts, weight_decay=args.weight_decay)

        # placeholders & inputs
        xa = tf.placeholder(tf.float32, shape=[None, args.crop_size, args.crop_size, 3])
        b_ = tf.placeholder(tf.float32, shape=[None, n_atts])

        # sample graph
        x = Gdec(Genc(xa, training=False), b_, training=False)
    else:
        # load freezed model
        with tf.gfile.GFile(py.join(output_dir, 'generator.pb'), 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            tf.import_graph_def(graph_def, name='generator')

        # placeholders & inputs
        xa = sess.graph.get_tensor_by_name('generator/xa:0')
        b_ = sess.graph.get_tensor_by_name('generator/b_:0')

        # sample graph
        x = sess.graph.get_tensor_by_name('generator/xb:0')

    # ======================================
    # =            run function            =
    # ======================================

    save_dir = '%s/output/%s/samples_testing_%s' % (args.flask_path, args.experiment_name, '{:g}'.format(args.test_int))
    py.mkdir(save_dir)

    def run():
        cnt = 0
        for _ in tqdm.trange(len_test_dataset):
            # data for sampling
            xa_ipt, a_ipt = sess.run(test_iter.get_next())
            b_ipt_list = [a_ipt]  # the first is for reconstruction
            for i in range(n_atts):
                tmp = np.array(a_ipt, copy=True)
                tmp[:, i] = 1 - tmp[:, i]   # inverse attribute
                tmp = data.check_attribute_conflict(tmp, args.att_names[i], args.att_names)
                b_ipt_list.append(tmp)

            x_opt_list = [xa_ipt]
            for i, b_ipt in enumerate(b_ipt_list):
                b__ipt = (b_ipt * 2 - 1).astype(np.float32)  # !!!
                if i > 0:   # i == 0 is for reconstruction
                    b__ipt[..., i - 1] = b__ipt[..., i - 1] * args.test_int
                x_opt = sess.run(x, feed_dict={xa: xa_ipt, b_: b__ipt})
                x_opt_list.append(x_opt)
            sample = np.transpose(x_opt_list, (1, 2, 0, 3, 4))
            sample = np.reshape(sample, (sample.shape[0], -1, sample.shape[2] * sample.shape[3], sample.shape[4]))

            for s in sample:
                cnt += 1
                im.imwrite(s, '%s/%d.jpg' % (save_dir, cnt))

    return run

sample = sample_graph()

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
    app.logger.info("n_atts:", n_atts)
    
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
        
        # python_command = "CUDA_VISIBLE_DEVICES=0 python /var/www/html/flaskapp_unigan/test.py --experiment_name UniGAN_128 --flask_path /var/www/html/flaskapp_unigan"
        # stdout = check_output([python_command], shell=True)
        sample()

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
