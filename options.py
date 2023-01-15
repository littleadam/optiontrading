#!/usr/bin/env python3

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0'
}

params = (
    ('symbol', 'NIFTY'),
)

response = requests.get('https://nseindia.com/api/option-chain-indices', headers=headers, params=params)
j = response.json()
strikePrice = j['records']['underlyingValue']
strikePrice = strikePrice
atm = int(round(strikePrice,-2))
datum = j['records']['data']
#print (datum[1]['PE']['strikePrice'])
loop = [i for i,e in enumerate(datum) if(e['strikePrice'] == atm)]
for i in loop:
    peLtp = int(j['records']['data'][i]['PE']['lastPrice']) 
    ceLtp = int(j['records']['data'][i]['CE']['lastPrice'])
    rangeval = peLtp + ceLtp 
    if(rangeval !=0 or peLtp !=0 and ceLtp !=0):
        print("*******************************************************")
        print("Strike Price:",j['records']['data'][i]['CE']['strikePrice'])
        print("Expiry Date:",j['records']['data'][i]['CE']['expiryDate'])
        print("PE LTP:",j['records']['data'][i]['PE']['lastPrice'])
        print("CE LTP:",j['records']['data'][i]['CE']['lastPrice'])
        print("No Loss Zone:",strikePrice-rangeval," to ",strikePrice+rangeval," Bandwidth: ",rangeval)
        print("*******************************************************")
