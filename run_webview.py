from threading import Thread, Lock
import logging
import webview
import requests
from time import sleep
import os
import sys
from flask_seasurf import SeaSurf

here = os.path.dirname(__file__)
logger = logging.getLogger(__name__)

from calculator import app, set_verify, verification_on
set_verify(True)

def run_server():
    """ This will run in its own thread """
    app.root_path = here
    app.run(host="127.0.0.1", port=23948, threaded=True)
    csrf = SeaSurf(app)

def load_window():
    # Load our page in the webview
    webview.load_url("http://127.0.0.1:23948", uid='master')

    # Now we retrieve the JWT token from the web service, and set it in the 
    # window's javascript dict
    res = requests.post('http://localhost:23948/login', json={"passkey":"trustme"})
    if res.ok:
        token = res.json()['access_token']
    else:
        print(res.text())
        quit()

    # Store the JWT token in the webview
    webview.evaluate_js('pywebview = {{authToken: "{token:s}"}};'.format(token=token))

    # Double-check we get back the right token
    token_chk = webview.evaluate_js('pywebview.authToken')
    if token_chk != token:
        raise KeyError("JWT tokens didn't match")

def url_ok(url, port):
    from http.client import HTTPConnection
    try:
        conn = HTTPConnection(url, port)
        conn.request("GET", "/")
        r = conn.getresponse()
        return r.status == 200
    except:
        logger.exception("Server not started")
        return False

if __name__ == '__main__':
    logger.debug("Starting server")
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    logger.debug("Checking server")
    
    while not url_ok("127.0.0.1", 23948):
        sleep(0.1)

    logger.debug("Server started")
    t = Thread(target=load_window)
    t.daemon = True
    t.start()
    
    uid = webview.create_window("Formerly",
        min_size=(640, 480),
        debug = True
    )
    sys.exit()