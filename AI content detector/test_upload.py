import requests
import sys

if len(sys.argv) < 2:
    print('Usage: python test_upload.py C:\\path\\to\\image.jpg')
    sys.exit(1)

path = sys.argv[1]
try:
    with open(path, 'rb') as f:
        files = {'file': (path.split('\\')[-1], f, 'application/octet-stream')}
        r = requests.post('http://127.0.0.1:5000/api/analyze/image', files=files)
        try:
            print(r.json())
        except Exception:
            print('Status:', r.status_code)
            print(r.text)
except FileNotFoundError:
    print(f'Error: File not found: {path}')
    sys.exit(1)
except requests.exceptions.ConnectionError as e:
    print('Error: Could not connect to backend server at http://127.0.0.1:5000')
    print('Make sure the backend server is running by executing:')
    print('  cd backend && python app.py')
    sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
