from flask import Flask, request, jsonify, current_app, url_for, render_template
app = Flask(__name__)

@app.route('/')
def frontend():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    values = request.get_json()
    return jsonify({'COP': float(values['Te']) + float(values['Tc'])})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)