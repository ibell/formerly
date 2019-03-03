import requests
res = requests.post('http://localhost:5000/login', json={"username":"user1"})
if res.ok:
    token = res.json()['access_token']
else:
    print(res.text)
    quit()

res = requests.post('http://localhost:5000/protected', headers={'Authorization': 'JWT %s' % token})
if res.ok:
    print(res)
else:
    print(res.text)