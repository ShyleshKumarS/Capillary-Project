import requests

res = requests.post("http://localhost:8000/query", json={
    "query": "running shoes",
    "command_type": "search"
})
print(res.json())
