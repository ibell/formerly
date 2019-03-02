from flask import Flask, request, jsonify
from webui import WebUI # Add WebUI to your imports
app = Flask(__name__)
ui = WebUI(app, debug=True) # Create a WebUI instance

@app.route('/')
def frontend():
    return open('index.html').read()

@app.route('/calculate', methods=['POST'])
def calculate():
    values = request.get_json()
    return jsonify({'COP': float(values['Te']) + float(values['Tc'])})

if __name__ == '__main__':
    ui.run()
    # app.run(host='0.0.0.0', debug=True)