import requests

with requests.Session() as s:
    res = s.post('http://localhost:5000/login', json={"passkey":"trustme"})
    if res.ok:
        token = res.json()['access_token']
    s.headers.update({'Authorization': 'Bearer %s' % token})

    res = s.get('http://localhost:5000/calculate', json={'Te':300, 'Tc': '400a'})
    if res.ok:
        print(res.json())
    else:
        print(res.text)