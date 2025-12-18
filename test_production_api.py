"""
Quick API Test Script
"""

import requests
import json

API_URL = "http://localhost:8000"

# Test health
print("Testing /health...")
resp = requests.get(f"{API_URL}/health")
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}\n")

# Test recommend
print("Testing /recommend...")
payload = {
    "query": "Need Java developers with strong teamwork skills",
    "top_k": 20,
    "final_count": 10
}

resp = requests.post(
    f"{API_URL}/recommend",
    json=payload
)

print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Got {len(data['recommended_assessments'])} recommendations\n")
    
    for i, assess in enumerate(data['recommended_assessments'][:3], 1):
        print(f"{i}. {assess['name']}")
        print(f"   Type: {assess['test_type']}")
        print(f"   Duration: {assess['duration']} min")
        print(f"   URL: {assess['url']}\n")
else:
    print(f"Error: {resp.text}")
