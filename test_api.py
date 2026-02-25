import requests
import json

url = "http://localhost:5000/api/plan"
headers = {"Content-Type": "application/json"}
data = {
    "task": "测试任务",
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")