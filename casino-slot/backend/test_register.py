import requests
import json

# Test registration endpoint
def test_register():
    url = "http://127.0.0.1:8000/register"
    data = {
        "username": "testuser123",
        "password": "test1234",
        "initial_balance": 100.0
    }
    
    print("Testing registration...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! User ID: {result.get('user_id')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_register()
