# Unigan Flask App Setup
```
Image: Deep Learning AMI (Ubuntu 18.04) Version 26.0
AWS Machine Type: g4dn.xlarge
```

### EC2 Instance Security Setup (Inbound)
|Type|Protocol|Port Range|Source|
|:--:|:------:|:--------:|:----:|
|HTTP|TCP|80|0.0.0.0/0|
|HTTP|TCP|80|::/0|
|SSH|TCP|22|0.0.0.0/0|
|Custom TCP Rule|TCP|5000|0.0.0.0/0|
|Custom TCP Rule|TCP|5000|::/0|
|HTTPS|TCP|443|0.0.0.0/0|
|HTTPS|TCP|443|::/0|

### Sample ssh command (update .pem filename & machine name):
```
ssh -i "t2-micro-1.pem" ubuntu@ec2-18-219-63-250.us-east-2.compute.amazonaws.com
```

### install base packages
```
sudo dpkg-reconfigure tzdata # set timezone to Los Angeles
sudo apt-get update
sudo apt install apache2 apache2-dev python3 python3-dev python3-pip 
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
gcloud init # to login (set default zone to us-west-b)
```

### Installing cudnn 7.6.5 from tar file (default for machine image is 7.5.x which conflict with tensorflow 1.15).
Instructions at https://docs.nvidia.com/deeplearning/sdk/cudnn-install/index.html#installlinux
```
gsutil cp gs://w210-bucket-1/ubuntu-18.04-resources/cudnn-10.0-linux-x64-v7.6.5.32.tgz .
tar xzvf cudnn-10.0-linux-x64-v7.6.5.32.tgz
```

Copy the following files into the CUDA Toolkit directory, and change the file permissions.
```
sudo cp cuda/include/cudnn.h /usr/local/cuda/include
sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*
```

### Clone repo
```
git clone https://github.com/kszu/UniGAN.git
```

### Setup permissions for apache user
```
sudo ln -sT /home/ubuntu/UniGAN/flaskapp_unigan /var/www/html/flaskapp_unigan
sudo groupadd varwwwusers
sudo adduser www-data varwwwusers
sudo chgrp -R varwwwusers /var/www/
sudo chmod -R 760 /var/www/
sudo chmod 777 /var/www/
sudo chmod 777 /var/www/html
sudo chmod 777 /var/www/html/flaskapp_unigan/static/input_images
sudo chmod 777 /var/www/html/flaskapp_unigan/static/input_images/flaskapp_img.jpg
sudo usermod -a -G varwwwusers ubuntu
```

### In UniGAN/flaskapp_unigan...
```
virtualenv --python=/usr/bin/python3 v-env3
source v-env3/bin/activate
pip install flask flask_cors tensorflow-gpu==1.15 opencv-python scikit-image tqdm oyaml
deactivate
```

### In UniGAN/flaskapp_unigan...
```
sudo cp 000-default.conf /etc/apache2/sites-enabled/000-default.conf
sudo cp wsgi.conf /etc/apache2/mods-enabled/wsgi.conf
mkdir static; cd static
ln -s ../data/zappos_50k/images input_images
ln -s ../output output
sudo chmod -R 777 output
```

### In UniGAN/flaskapp_unigan/output/UniGAN_128 upload generator.pb...
```
Example:
cd ~/UniGAN/flaskapp_unigan/output/UniGAN_128
gsutil cp gs://w210-bucket-1/UniGAN-models/generator_20200218.pb .
mv generator_20200218.pb generator.pb
```

Note: had to modify imlib/dtype.py to get inference working via Flask...
    assert np.min(images)+0.00001 >= min_value and np.max(images)-0.00001 <= max_value, \
        '`images` should be in the range of %s, %f >= %f, %f <= %f!!!' % (l + ',' + r, np.min(images), min_value, np.max(images), max_value)

### Test setup

In ~/UniGAN/flaskapp_unigan...
```
source v-env3/bin/activate
CUDA_VISIBLE_DEVICES=0 python test.py --experiment_name UniGAN_128
deactivate
```

### Running apache
```
sudo apachectl restart
tail /var/log/apache2/error.log
```

# Misc debugging info

Some third party packages for Python which use C extension modules, and this includes scipy and numpy, will only work in the Python main interpreter and cannot be used in sub interpreters as mod_wsgi by default uses. The result can be thread deadlock, incorrect behaviour or processes crashes. These is detailed in:

http://code.google.com/p/modwsgi/wiki/ApplicationIssues#Python_Simplified_GIL_State_API

The workaround is to force the WSGI application to run in the main interpreter of the process using: WSGIApplicationGroup %{GLOBAL}