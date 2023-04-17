import datetime
from nsepy import get_history
import numpy as np

# specify the symbol and get the expiry date
symbol = 'NIFTY'
expiry_date = None
expiry_input = input("Enter the expiry month number (e.g. 4 for April) or week number (e.g. 4 for the fourth week): ")

if len(expiry_input) == 1:
    # assume week number
    expiry_year = datetime.date.today().year
    week_number = int(expiry_input)
    expiry_date = datetime.datetime.strptime(f'{expiry_year}-W{week_number}-3', "%Y-W%W-%w").date()
else:
    # assume month number
    expiry_month = int(expiry_input)
    expiry_year = datetime.date.today().year if expiry_month >= datetime.date.today().month else datetime.date.today().year + 1
    expiry_date = datetime.date(expiry_year, expiry_month, 27)

# fetch the index data for the expiry date
nifty_data = get_history(symbol=symbol, start=expiry_date, end=expiry_date, index=True)

# extract the index value
index_value = nifty_data['Close'][0]

# calculate N1 and N2
N1 = np.round(index_value / 100) * 100  # round to nearest 100
N2 = 0.33 * N1

# get the list of available strike prices for the expiry date
strike_prices = np.array(nifty_data.index)

# find the two OTM strike prices, one below N2 and one above N2
idx = np.abs(strike_prices - N2).argmin()
N2_idx = np.where(strike_prices == strike_prices[idx])[0][0]
N2_idx_left = N2_idx - 1
N2_idx_right = N2_idx + 1
N2_strike_price = strike_prices[N2_idx]
N3_strike_price = strike_prices[N2_idx_right] if N2_strike_price < N2 else strike_prices[N2_idx_left]
N4_strike_price = 2 * N2_strike_price - N1

print(f"The Nifty ATM strike price for the expiry date {expiry_date} is: {N1}")
print(f"The first OTM strike price for the expiry date {expiry_date} is: {N3_strike_price}")
print(f"The second OTM strike price for the expiry date {expiry_date} is: {N4_strike_price}")
