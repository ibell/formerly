import requests
import time
import timeit
N = 100
tic = timeit.default_timer()
for i in range(100):
    res = requests.post('http://localhost:5000/push_job', json={"Te":"42.314", "Tc": "-1000"})
    if res.ok:
        jj = res.json()
        uid = jj['uuid']
    else:
        print(res.text)
        quit()

toc = timeit.default_timer()
print(toc-tic, 's elapsed')
time.sleep(1)

res = requests.post('http://localhost:5000/get_results')
if res.ok:
    jj = res.json()
    for k, v in jj.items():
        print(k, v)
else:
    print(res.text)
    quit()