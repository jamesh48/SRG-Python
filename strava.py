from __future__ import print_function
import os
from pprint import pprint
from dotenv import load_dotenv, find_dotenv
from flask import Flask
from data_utilities import data_controller_bp
from auth_utilities import auth_controller_bp
from flask_cors import CORS

load_dotenv(find_dotenv())

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.register_blueprint(data_controller_bp)
app.register_blueprint(auth_controller_bp)


@app.route('/srg/healthcheck', methods=["GET"])
def return_healthy():
    return 'healthy!'


if __name__ == '__main__':
    env = os.environ.get('FLASK_ENVIRONMENT')
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'

    if env == 'production':
        from waitress import serve
        serve(app, host="0.0.0.0", port=4000)
    else:
        app.run(host="0.0.0.0", port=4000, debug=debug_mode, use_reloader=debug_mode)
