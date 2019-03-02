from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/')
def frontend():
    return open('index.html').read()

@app.route('/calculate', methods=['POST'])
def calculate():
    values = request.get_json()
    return jsonify({'COP': float(values['Te']) + float(values['Tc'])})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)