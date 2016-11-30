# -*- coding: utf8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))

import ConfigParser
Config = ConfigParser.ConfigParser()
Config.read('config.ini')

CSRF_ENABLED = True
SECRET_KEY = Config.get('CoinStream','secret_key')

# Streamlabs Keys, These are only for the testapp, replace when in production
STREAMLABS_CLIENT_ID = Config.get('CoinStream','streamlabs_client_id')
STREAMLABS_CLIENT_SECRET = Config.get('CoinStream','streamlabs_client_secret')
COINSTREAM_REDIRECT_URI = Config.get('CoinStream', 'redirect_uri')

SQLALCHEMY_DATABASE_URI = ('sqlite:///' + os.path.join(basedir, 'app.db') +
                                       '?check_same_thread=False')

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

