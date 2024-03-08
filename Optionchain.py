import requests
import json

# Get the option chain for INFY next month ,current year contract 
url = "https://api.nseindia.com/option-chain/ohlc/?symbol=INFY&expiry=2023-06-24"
response = requests.get(url)
data = json.loads(response.content)

# Get the call and put options with the highest open interest
call_options = []
put_options = []
for option in data["data"]:
    if option["openInterest"] > 0:
        if option["type"] == "CE":
            call_options.append(option)
        else:
            put_options.append(option)

# Get the call and put premiums
call_premium = call_options[0]["premium"]
put_premium = put_options[0]["premium"]

# Get the lot size
lot_size = data["metadata"]["lotSize"]

# Get the margin amount as per SEBI
margin_amount_call = lot_size * call_premium * 0.2
margin_amount_put = lot_size * put_premium * 0.2

print("Call premium:", call_premium)
print("Put premium:", put_premium)
print("Lot size:", lot_size)
print("Margin amount for selling call option:", margin_amount_call)
print("Margin amount for selling put option:", margin_amount_put)

