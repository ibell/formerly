from functools import wraps
import os
import uuid
import json
import sqlite3
from threading import Thread
import time

from flask import Flask, request, jsonify, current_app, url_for, render_template
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import safe_str_cmp
import requests

import CoolProp.CoolProp as CP
import pandas

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

if os.path.exists('temp.db'):
    os.remove('temp.db')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # See this: https://gehrcke.de/2015/05/in-memory-sqlite-database-and-flask-a-threading-trap/
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String)
    contents = db.Column(db.String)
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String)
    result = db.Column(db.String)
db.create_all()

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = os.urandom(20)
jwt = JWTManager(app)

VERIFY = os.environ.get('JWT_VERIFY', False)
MASTER_KEY = os.urandom(20)
POLLING_FREQ = 0.1

def set_verify(value):
    global VERIFY
    VERIFY = value

def verification_on():
    return VERIFY

import pybtex.database.input.bibtex 
import pybtex.plugin
import codecs
import latexcodec

from pybtex.style.formatting import plain
plain_style = plain.Style()
style = pybtex.plugin.find_plugin('pybtex.style.formatting', 'plain')()
backend = pybtex.plugin.find_plugin('pybtex.backends', 'html')()
parser = pybtex.database.input.bibtex.Parser()
with codecs.open("CoolPropBibTeXLibrary.bib", encoding="latex") as stream:
    data = parser.parse_stream(stream)

# BibTeX_key = 'Span-BOOK-2000'
# e = list(plain_style.format_entries([data.entries[BibTeX_key]]))[0]
# print(e.text.render(backend))

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

##########################################################
##################     ROUTES     ########################
##########################################################

@app.route('/')
def frontend():
    return render_template('index.html')

@app.route('/calculate', methods=['POST','GET'])
@my_jwt_optional
def calculate():
    values = request.get_json()
    return jsonify({'COP': float(values['Te']) + float(values['Tc'])})

@app.route('/pandas_table', methods=['POST','GET'])
@my_jwt_optional
def pandas_table():
    return pandas.DataFrame({'odds \(O\)':[1,3,5,7,9],'evens \(E\)':[2,4,6,8,10]}).to_html(index=False)

@app.route('/get_bib_html', methods=['POST'])
@my_jwt_optional
def get_bib_html():
    values = request.get_json()
    BibTeX_key = values['key']
    e = data.entries[BibTeX_key]
    e = list(plain_style.format_entries([e]))[0]
    o = str(e.text.render(backend))
    return o

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

##########################################################
##################  JOB QUEUEING  ########################
##########################################################

@app.route('/push_job', methods=['POST'])
@my_jwt_optional
def push_job():
    values = request.get_json()
    uid = str(uuid.uuid1())
    db.session.add(Job(uuid=uid, contents=json.dumps(values)))
    db.session.commit()
    return jsonify({'uuid': uid})

def _push_job_result(uid, JSONresult):
    print('pushing result: ', uid)
    try:
        job = Job.query.filter_by(uuid=uid).first()
        db.session.add(Result(uuid=uid, result=json.dumps(JSONresult)))
        db.session.delete(job)
        db.session.commit()
    except sqlite3.IntegrityError as IE:
        print(IE)

@app.route('/get_results', methods=['POST'])
@my_jwt_optional
def get_results():
    return jsonify({c.uuid:c.result for c in Result.query.all()})

def greedy_worker():
    """
    A single thread that will sequentially run all the jobs that are queued.
    It does not share with other possible workers
    """
    while True:
        time.sleep(POLLING_FREQ)
        jobs = Job.query.all()
        for job in jobs:
            try:
                j = json.loads(job.contents)
                _push_job_result(job.uuid, {'output': float(j['Te'])+float(j['Tc'])})
            except BaseException as BE:
                print(BE)

if __name__ == '__main__':
    t = Thread(target=greedy_worker)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', debug=True)
