# Unigan Flask App Setup
```
Image: Deep Learning AMI (Ubuntu 18.04) Version 26.0
AWS Machine Type: g4dn.xlarge
```

Sample ssh command (update .pem filename & machine name):
```
ssh -i "t2-micro-1.pem" ubuntu@ec2-18-219-63-250.us-east-2.compute.amazonaws.com
```

### install base packages
```
sudo dpkg-reconfigure tzdata # set timezone
sudo apt-get update
apt install apache2 apache2-dev python3 python3-dev python3-pip 
sudo apt-get install libapache2-mod-wsgi-py3
sudo apt install virtualenv
```

### install gsutil
```
sudo apt-get install libwww-perl
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get install apt-transport-https ca-certificates gnupg
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk
gcloud init # to login
```

### Installing cudnn 7.6.5 from tar file (default for machine image is 7.5.x which conflict with tensorflow 1.15).
Instructions at https://docs.nvidia.com/deeplearning/sdk/cudnn-install/index.html#installlinux
```
gsutil cp gs://w210-bucket-1/ubuntu-18.04-resources/cudnn-10.0-linux-x64-v7.6.5.32.tgz .
tar -xzvf cudnn-10.2-linux-x64-v7.6.5.32.tgz
```

Copy the following files into the CUDA Toolkit directory, and change the file permissions.
```
sudo cp cuda/include/cudnn.h /usr/local/cuda/include
sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*
```

### Setup permissions for apache user
```
sudo ln -sT /home/ubuntu/UniGAN/flaskapp_unigan /var/www/html/flaskapp_unigan
sudo groupadd varwwwusers
sudo adduser www-data varwwwusers
sudo chgrp -R varwwwusers /var/www/
sudo chmod -R 760 /var/www/
sudo usermod -a -G varwwwusers ubuntu
```

### Clone repo
```
git clone https://github.com/kszu/UniGAN.git
```

In UniGAN/flaskapp_unigan...
```
virtualenv --python=/usr/bin/python3 v-env3
source v-env3/bin/activate
pip install flask
pip install flask_cors
pip install tensorflow-gpu==1.15
pip install opencv-python
pip install scikit-image
pip install tqdm
pip install oyaml
deactivate
```

In UniGAN/flaskapp_unigan...
```
sudo cp 000-default.conf /etc/apache2/sites-enabled/000-default.conf
sudo cp wsgi.conf /etc/apache2/mods-enabled/wsgi.conf
sudo chmod -R 777 output
cd static
ln -s ../data/zappos_50k/images input_images
ln -s ../output output
```

In UniGAN/flaskapp_unigan/output/UniGAN_128...
```
Upload generator.pb
```

Note: had to modify imlib/dtype.py to get inference working via Flask...
    assert np.min(images)+0.00001 >= min_value and np.max(images)-0.00001 <= max_value, \
        '`images` should be in the range of %s, %f >= %f, %f <= %f!!!' % (l + ',' + r, np.min(images), min_value, np.max(images), max_value)

### Test setup

In UniGAN/flaskapp_unigan...
```
CUDA_VISIBLE_DEVICES=0 python test.py --experiment_name UniGAN_128
```

### Running apache
```
sudo apachectl start (restart)
tail /var/log/apache2/error.log
```

# Misc debugging info

Some third party packages for Python which use C extension modules, and this includes scipy and numpy, will only work in the Python main interpreter and cannot be used in sub interpreters as mod_wsgi by default uses. The result can be thread deadlock, incorrect behaviour or processes crashes. These is detailed in:

http://code.google.com/p/modwsgi/wiki/ApplicationIssues#Python_Simplified_GIL_State_API

The workaround is to force the WSGI application to run in the main interpreter of the process using: WSGIApplicationGroup %{GLOBAL}