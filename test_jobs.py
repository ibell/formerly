import requests
import time
import timeit
N = 100
url = 'http://localhost:5000'
tic = timeit.default_timer()
for i in range(N):
    res = requests.post('http://localhost:5000/push_job', json={"Te":"42.314", "Tc": "-1000"})
    if res.ok:
        jj = res.json()
        uid = jj['uuid']
    else:
        print(res.text)
        quit()

toc = timeit.default_timer()
print((toc-tic)/N, 's per request')

tic = timeit.default_timer()
res = requests.post(url+'/push_jobs', json=[{"Te":42.314, "Tc": -1000}]*N)
if res.ok:
    jj = res.json()
    uid = jj['uuids']
else:
    print(res.text)
    quit()
toc = timeit.default_timer()
print((toc-tic), 's to post jobs')

tic = timeit.default_timer()
res = requests.post(url+'/get_results')
if res.ok:
    jj = res.json()
    print(len(jj))
    # for k, v in jj.items():
    #     print(k, v)
else:
    print(res.text)
    quit()

# res = requests.post(url + '/flush_results')

toc = timeit.default_timer()
print((toc-tic), 'to get results')