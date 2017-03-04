from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_qrcode import QRcode
from flask_login import LoginManager

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config.from_object('config')
db = SQLAlchemy(app)
QRcode(app)
lm = LoginManager()
lm.init_app(app)


from app import views, models, tippage
