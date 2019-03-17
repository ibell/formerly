# Python standard libraries
from functools import wraps
import os
import uuid
import json
import sqlite3
from threading import Thread
import time
import timeit

# Flask-y things
from flask import Flask, request, jsonify, current_app, url_for, render_template
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import safe_str_cmp
from flask_sqlalchemy import SQLAlchemy

# Other libraries
import requests
import CoolProp.CoolProp as CP
import pandas
import pybtex.database.input.bibtex 
import pybtex.plugin
import codecs
import latexcodec
from pybtex.style.formatting import plain

app = Flask(__name__)

# Flask-SQLAlchemy setup
# ----------------------
if os.path.exists('test.db'):
    os.remove('test.db')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # See this: https://gehrcke.de/2015/05/in-memory-sqlite-database-and-flask-a-threading-trap/
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
POLLING_FREQ = 0.001

def set_verify(value):
    global VERIFY
    VERIFY = value

def verification_on():
    return VERIFY

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

@app.route('/push_jobs', methods=['POST'])
@my_jwt_optional
def push_jobs():
    uids = []
    for values in request.get_json():
        uid = str(uuid.uuid1())
        db.session.add(Job(uuid=uid, contents=json.dumps(values)))
        uids.append(uid)
    db.session.commit()
    return jsonify({'uuids': uids})

@app.route('/get_results', methods=['POST'])
@my_jwt_optional
def get_results():
    tic = timeit.default_timer()
    while True:
        # If there are no jobs remaining in the queue,
        # then return the results, otherwise, see if 
        # we have timed out yet
        if not Job.query.all():
            return jsonify({c.uuid: c.result for c in Result.query.all()})
        if timeit.default_timer() - tic > 10:
            raise ValueError()
        time.sleep(0.01)

def greedy_worker():
    """
    A single thread that will sequentially run all the jobs 
    that are queued. It does not share with other possible workers
    """
    while True:
        time.sleep(POLLING_FREQ)
        if Job.query.all():
            for job in Job.query.all():
                try:
                    j = json.loads(job.contents)
                    JSONresult = {'output': float(j['Te']) + float(j['Tc'])}
                    db.session.add(Result(uuid=job.uuid, result=json.dumps(JSONresult)))
                    db.session.delete(job)
                except BaseException as BE:
                    print(job.uuid, job.contents, BE)
            db.session.commit()

@app.route('/flush_results', methods=['POST'])
@my_jwt_optional
def flush_results():
    for r in Result.query.all():
        db.session.delete(r)
    db.session.commit()
    return jsonify({'message':"ok"})

if __name__ == '__main__':
    t = Thread(target=greedy_worker)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', debug=True)
