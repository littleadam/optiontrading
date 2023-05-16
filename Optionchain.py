import requests

# Endpoint for fetching the option chain
url = "https://www.nseindia.com/api/option-chain-equity?symbol=INFY"

# Make the request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # The response body contains the option chain data
    data = response.json()

    # Print the option chain data
    print(data)
else:
    print("Request failed with status code:", response.status_code)
