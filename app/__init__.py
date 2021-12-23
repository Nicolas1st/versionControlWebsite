from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_bootstrap import Bootstrap
from os import environ

app = Flask(__name__)
user = environ['version_control_database_user']
password = environ['version_control_database_user_password']
host = environ['version_control_database_host']
name = environ['version_control_database_name']

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{user}:{password}@{host}/{name}'
app.config['SECRET_KEY']='LongAndRandomSecretKey'
app.config['UPLOAD_FOLDER'] = '/home/nicolas/Desktop/dirdir/'
app.config['MAX_CONTENT_PATH'] = 1073741824
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
bootstrap = Bootstrap(app)

from app import views
