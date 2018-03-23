# -*- coding: utf8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))
configfile = os.path.join(basedir, 'config.ini')

import configparser
Config = configparser.ConfigParser()
Config.read(configfile)

CSRF_ENABLED = True
SECRET_KEY = Config.get('GroestlTip','secret_key')

# Streamlabs Keys, These are only for the testapp, replace when in production
STREAMLABS_CLIENT_ID = Config.get('GroestlTip','streamlabs_client_id')
STREAMLABS_CLIENT_SECRET = Config.get('GroestlTip','streamlabs_client_secret')
GROESTLTIP_REDIRECT_URI = Config.get('GroestlTip', 'redirect_uri')

SQLALCHEMY_DATABASE_URI = ('sqlite:///' + os.path.join(basedir, 'app.db') +
                                       '?check_same_thread=False')

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

