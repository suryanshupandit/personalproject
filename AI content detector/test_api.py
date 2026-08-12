import requests
print('TEST TEXT ->', requests.post('http://127.0.0.1:5000/api/analyze/text', json={'text':'This is a short test article. It has multiple sentences.'}).json())
print('TEST NEWS ->', requests.post('http://127.0.0.1:5000/api/analyze/news', json={'url':'https://www.bbc.com'}).json())
with open('frontend/index.html','rb') as f:
    files={'file':('index.html', f, 'text/html')}
    print('TEST IMAGE ->', requests.post('http://127.0.0.1:5000/api/analyze/image', files=files).json())
