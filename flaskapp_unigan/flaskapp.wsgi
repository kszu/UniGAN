import os, sys
PROJECT_DIR = '/var/www/html/flaskapp_unigan'
sys.path.insert(0, PROJECT_DIR)

def execfile(filename):
    globals = dict( __file__ = filename )
    exec( open(filename).read(), globals )

activate_this = os.path.join( PROJECT_DIR, 'v-env3/bin', 'activate_this.py' )
execfile( activate_this )

from flaskapp import app as application
