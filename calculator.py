from flask import Flask, request, jsonify, current_app, url_for, render_template
app = Flask(__name__)
import CoolProp.CoolProp as CP

@app.route('/')
def frontend():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    values = request.get_json()
    return jsonify({'COP': float(values['Te']) + float(values['Tc'])})

@app.route('/sat_table', methods=['POST'])
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