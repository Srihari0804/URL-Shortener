import requests

# Define the endpoint (localhost)
url = "http://localhost:8000/urls/me"

# Your API key
api_key = "url_EVlOwRRQ1ApoaprBs4SJFfb0cz7ejlsO01tRNlqh4iE"

# Headers with API key
headers = {
    "API-Key": api_key,   # Common pattern
    # or sometimes: "x-api-key": api_key
}

# Optional payload (if sending data)
"""payload = {
    "message": "Hello from client"
}
"""
i = 1
while True:
    # Send get request
    response = requests.get(url, headers=headers)
    print(i)
    i += 1

    if response.status_code != 200:
        # Print response
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)
        break