from __future__ import print_function
from pprint import pprint
from dotenv import load_dotenv, find_dotenv
from flask import Flask
from data_utilities import data_controller_bp
from auth_utilities import auth_controller_bp

load_dotenv(find_dotenv())

app = Flask(__name__)
app.register_blueprint(data_controller_bp)
app.register_blueprint(auth_controller_bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
