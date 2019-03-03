import requests
res = requests.post('http://localhost:5000/login', json={"passkey":"trustme"})
if res.ok:
    token = res.json()['access_token']
else:
    print(res.text)
    quit()

res = requests.get('http://localhost:5000/calculate', json={'Te':300, 'Tc': 400}, headers={'Authorization': 'Bearer %s' % token})
if res.ok:
    print(res)
    print(res.json())
else:
    print(res.text)