import requests

with requests.Session() as s:
    res = s.post('http://localhost:23948/login', json={"passkey":"trustme"})
    if res.ok:
        token = res.json()['access_token']
    else:
        print(res.text())
        quit()
    s.headers.update({'Authorization': 'Bearer %s' % token})

    res = s.get('http://localhost:23948/calculate', json={'Te':300, 'Tc': '400'})
    if res.ok:
        print(res.json())
    else:
        print(res.text)