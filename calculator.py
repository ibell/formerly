from functools import wraps
import os

from flask import Flask, request, jsonify, current_app, url_for, render_template
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import safe_str_cmp

import CoolProp.CoolProp as CP

app = Flask(__name__)

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = os.urandom(20)
jwt = JWTManager(app)

VERIFY = os.environ.get('JWT_VERIFY', False)
MASTER_KEY = os.urandom(20)

def set_verify(value):
    global VERIFY
    VERIFY = value

def verification_on():
    return VERIFY

# Provide a method to create access tokens. The create_access_token()
# function is used to actually generate the token, and you can return
# it to the caller however you choose.
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    values = request.get_json()
    passkey = values.get('passkey', None)

    if passkey != MASTER_KEY and not safe_str_cmp(passkey.encode('utf-8'), 'trustme'.encode('utf-8')):
        return jsonify({"msg": "Bad passkey"}), 401

    # Identity can be any data that is json serializable
    access_token = create_access_token(identity='indubitably')
    return jsonify(access_token=access_token), 200

def my_jwt_optional(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if verification_on():
            verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper

@app.route('/')
def frontend():
    return render_template('index.html')

@app.route('/calculate', methods=['POST','GET'])
@my_jwt_optional
def calculate():
    values = request.get_json()
    return jsonify({'COP': float(values['Te']) + float(values['Tc'])})

@app.route('/sat_table', methods=['POST'])
@my_jwt_optional
def sat_table():
    values = request.get_json()
    
    Tvec = values['Tvec']
    Q = values['Q']

    # Setup
    fluid = values['fluid']
    backend = values.get('backend', 'HEOS')
    AS = CP.AbstractState(backend, fluid)

    # Map output string keys to enumerated keys 
    output_keys = values['output_keys']
    ikeys = {skey: CP.get_parameter_index(skey) for skey in output_keys}

    # Calculate the outputs
    outputs = {}
    for T in Tvec:
        AS.update(CP.QT_INPUTS, 0, T)
        for output_key in output_keys:
            val = AS.keyed_output(ikeys[output_key])
            if output_key in outputs:
                outputs[output_key].append(val)
            else:
                outputs[output_key] = [val]

    return jsonify(outputs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
