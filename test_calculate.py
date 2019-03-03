import requests
res = requests.post('http://localhost:5000/calculate', json={"Te":"42.314", "Tc": "-1000"})
if res.ok:
    print(res.json())
else:
    print(res.text)
    quit()

res = requests.post('http://localhost:5000/sat_table', json={"Tvec":[300,400,500], "fluid":"Water", 'Q':0, 'output_keys':["Dmass","Dmolar"]})
if res.ok:
    print(res.json())
else:
    print(res.text)
    quit()