import requests
res = requests.post('http://localhost:5000/calculate', json={"Te":"42.314", "Tc": "-1000"})
if res.ok:
    print(res.json())