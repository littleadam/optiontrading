#!/usr/bin/env python3

#bugs to be fixed
# 1. cancel() : Get order id and parent id properly 
# 2. Check why kite call is not in while loop
# 3. add code for this..trade_start flag will be set if the 1min,5min and 15min lists are full 
# 4. check if kite.TRANSACTION_TYPE_SELL format is required instead of just SELL
# 5. Add order limit to datafile.txt
# 6. make sure ltp is always between the first and second leg and not out of the range
# 7. Init all values to zero in the beginning before while loop
# 8. if countcmpt is zero , if timelimit is hit, do we need to cancel all pending orders ?
# 9. add timeout for complete wait 

# Data structure design
# Incore list structure
# =====================
# <buy_id><sell_id><buy_ltp><sell_ltp><scrip><status>
# for open contracts, one of the ltps will be zero and status will be pending
# if all fields are filled ,strip the <scrip> and <status>; add to 'scrip'.txt file, under <date></date>
# in cancel_or_exit() check if cmpt+pndg = 0 is required 

# lists
# =====
# all generic lists will have elements in the follwing order
# <crudeoil><silver><silverm><goldm><nickel>

import socket
import logging
import time
import datetime
import os
import sys
import pdb
import operator
import csv
import threading
import xml.etree.ElementTree as xml
import requests
import signal

from lxml import etree
from datetime import datetime, timedelta
from time import sleep
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
from bs4 import BeautifulSoup
from random import randint              # added for randint() call
from urllib.request import urlopen      # added for internet connectivity check
from os import path

# Tcp variables
conn            =   None

testmode        =   1           # 0 is for real trading and 1 is for testing with ltp from the internet
debug_flag      =   1
logger          =   None
commoditylist   =   [0]
tickLength      =   0
tickFlag        =   0
order_id        =   1

# check  and delete..these might be unnecesssary
#book keeping variables
offline_orders  =   [0]
completed_ordr  =   [[0]*10 for _ in range(5)]
open_ordr       =   [[0]*10 for _ in range(5)]
countpndg       =   [0] * 5     # +1 for buy and -1 for sell
countcmpt       =   [0] * 5     # +1 for buy and -1 for sell
order_limit     =   [0] * 5
confirm_wait    =   [0] * 5     # Orders placed but still not updated in placed orders list
confirm_wait_t  =   [0] * 5     # Orders placed but still not updated in placed orders list
#order_flag       =   0 # +1 for open,-1 for cancel ,+100 for complete buy ,-100 for complete sell 
trade_flag      =   0
#kite variables
apikey          =   None 
reqtoken        =   None
apisecret       =   None
accesstoken     =   None
closetime       =   0

#variables for commodity fut
instoken        =   [0] * 5
scrip           =   ['0'] * 5
tradingsymbol   =   ['0'] * 5
symbol          =   ['0'] * 5
expiry          =   ['0'] * 5
ltpindex        =   ['0'] * 5
exchange        =   "kite.EXCHANGE_MCX"
quantity        =   1
scripfactor     =   [0.0] * 5
dayloss         =   [0.0] * 5
dayprofit       =   [0.0] * 5
scripactive     =   ['1'] * 5     # 1 indicates,scrip can be traded today .0 indicates,it is blocked 
moneyfactor     =   [0.0] * 5     # Rupees per unit change

#variable for intraday trade
txtype          =   [0] * 5
trigger         =   [0.0] * 5 
trend           =   [0] * 5  #-1 for downtrend and +1 for uptrend
stoploss        =   [0.0] * 5
candleStart     =   [0.0] * 5  # starting candle
candleEnd       =   [0.0] * 5  # ending candle
smallCandle     =   [0] * 5
order_type      =   "kite.ORDER_TYPE_SLM"
variety         =   ['VARIETY_NRML'] * 5
product         =   "MIS"
latest_txnid    =   0
ltp             =   [0.0]*5    
high_ref        =   0 
low_ref         =   0

totalgains      =   [0.0] * 5
counternrml     =   [0] * 5
countermis      =   [0] * 5

tree            =   None
day             =   None
now             =   None
timecounter     =   0
ltp_write       =   0         # SYNC flag for find_ohlc()  
mincount        =   0

onemin          =   [[0.0]*12 for _ in range(5)]
fivemin         =   [[0.0]*12 for _ in range(5)]  
fifteenmin      =   [[0.0]*12 for _ in range(5)]  
thirtymin       =   [[0.0]*12 for _ in range(5)]  
onehour         =   [[0.0]*12 for _ in range(5)]  
refband         =   onemin
refinterval     =   1

# strategies
firstcandle     =   1
sixpm           =   2
eightpm         =   4

bookedprofit    =   [0.0]*5
losscount       =   0
profitcount     =   0
fifteenflag     =   0
xmlfile         =   'accounts.xml'

# Simulation variables 
ltpsim          =   [100.0]*5    
#testltp         =   [[0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1,-0.1],[0],[0]]
testltp         =   [[0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1],[0],[0]]
#testltp         =   [[0.5,0.5,0.5,0.5],[0],[0]]
ltprecall       =   0

def printandlog(string):
    print(string)
    logging.info(string)

def check_internet():
    global testmode
    if(testmode ==0):
        site='https://kite.zerodha.com/'
    elif(testmode == 1):
        site='https://moneycontrol.com/commodity'
    try:
        response = urlopen(site, timeout=10)
        return(1)
    except:
        return(0)

def data_validate(dataval,datatype):
    global countermis
    global counternrml

    logging.info("validating data..")
    if(datatype == 'index'):
        if(dataval<0 and dataval > 5):
            return (0)
    elif(datatype == 'product'):
        if(dataval != 'PRODUCT_NRML' 
                and dataval != 'PRODUCT_MIS' 
                and dataval != 'PRODUCT_CO' 
                and dataval != 'PRODUCT_BO' 
                and dataval != 'PRODUCT_CNC'):
            return (0)
    elif(datatype == 'order'):
        if(counternrml[dataval] >=2 
                or countermis[dataval]>=2 
                or (counternrml[dataval]+
                    countermis[dataval])>2):
            return(0)
    return (1) 

def time_iterate (lis,interval):
    global mincount
    global ltp 
    global tickLength
    global now 
    global fifteenflag
    global refband
    global refinterval

    if((mincount%interval)==0):
        for i in range(0,tickLength):
            for j in range(0,4):
                lis[i].insert(0,ltp[i])
                lis[i].pop()
        if(interval == refinterval):
            #logging.info("Band array: {}".format(refband[0]))
            #logging.info("Band array: {}".format(refband[1]))
            #logging.info("Band array: {}".format(refband[2]))
            fifteenflag = 1 

def marketdata():
    url = "https://www.mcxindia.com/backpage.aspx/GetMarketWatch"
    headers = { 
        "Host": "www.mcxindia.com",
        "Origin": "https://www.mcxindia.com",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://www.mcxindia.com/market-data/market-watch",
        "Accept": "application/json, text/javascript, */*; q=0.01",  
        }


    resp  = requests.post(url, headers = headers)
    market_data = resp.json()['d']['Data'] 
    return (market_data)

def init_ltp(marketval,index):
    global ltpindex
    global expiry
    global scrip
    global tickLength

    #print(ltpindex," ",len(marketval)," ",tickLength," ",expiry," ",scrip)
    for i in range(0,len(marketval)):
        if(marketval[i]['Symbol'] == str(scrip[index])):
            if(marketval[i]['ExpiryDate'] in str(expiry[index])):
                ltpindex[index] = i
                break

def find_ohlc ():
    global ltp
    global onemin,fivemin,fifteenmin,thirtymin,onehour
    global mincount
    global timecounter
    global ltp_write 

    threading.Timer(60,find_ohlc).start()
    if(mincount>15):
        read_flag  = 1

    ltp_write   = 1
    time_iterate(onehour,60)
    time_iterate(thirtymin,30)
    time_iterate(fifteenmin,15) 
    time_iterate(fivemin,5)    
    time_iterate(onemin,1)
    ltp_write   = 0
    
    mincount = mincount +1
    timecounter = timecounter +1

def trend_valuate (oper,txn,index): 
    global trend
    global txntype
    global trigger 
    global stoploss
    global fivemin,onemin
    
    trend[index]     = 1
    txtype[index]   = txn
    trigger[index]   = refband[index][-3]
    stoploss[index]  = refband[index][-2]
        
    if(oper(fivemin[index][-1],fivemin[index][-4])):
        return 1
    elif(oper(onemin[index][-1], onemin[index][-4])):
        return 1
    return None

def get_trend(index):
    global ltp_write
    global refband

    while(ltp_write == 1):
        dummy   = 0

    if (refband[index][-1] > refband[index][-4]):
        return(trend_valuate(operator.gt,'BUY',index))
    elif (refband[index][-1] < refband[index][-4]):
        return(trend_valuate(operator.lt,'SELL',index))

#new
# curl o/p Format: 55572743,217081,CRUDEOIL20APRFUT,"CRUDEOIL",0,2020-04-20,0,1,1,FUT,MCX-FUT,MCX
def scrip_init ():
    global tradingsymbol
    global exchange
    global symbol
    global scripfactor
    global tree
    global timecounter
    global tickLength
    global scrip
    global expiry
    global dayloss
    global dayprofit
    global order_limit
    
    datafile = datetime.now().strftime('datafile_%d%m%Y.txt')
    if (not path.exists(datafile)):
        logging.info ("Data file does not Exist.Creating a new file")
        os.system("cp datafile.txt "+datafile)
        os.system("chmod 777 "+datafile)
    else:
        logging.info ("datafile Exists")

    #index        = tickLength
    tree         = xml.parse(datafile)
    #scrip[index] = scrip_name.upper()
    marketval = marketdata()
    #print(tickLength)
    for index in range(0,tickLength):
        # get scrip specific data
        instoken[index]     = str(tree.find('scrip/'+scrip[index]+'/instoken').text)
        tradingsymbol[index]= str(tree.find('scrip/'+scrip[index]+'/tradingsymbol').text)
        symbol[index]       = str(tree.find('scrip/'+scrip[index]+'/symbol').text)
        scripfactor[index]  = float(tree.find('scrip/'+scrip[index]+'/scripfactor').text)
        exchange            = str(tree.find('scrip/'+scrip[index]+'/exchange').text)
        expiry[index]       = str(tree.find('scrip/'+scrip[index]+'/expiry').text)
        order_limit[index]  = tree.find('scrip/'+scrip[index]+'/orderlimit').text
        dayloss[index]      = float(tree.find('scrip/'+scrip[index]+'/dayloss').text)
        dayprofit[index]    = float(tree.find('scrip/'+scrip[index]+'/dayprofit').text)
    
        if(scripactive[index] != '0'):
            scripactive[index]  = tree.find('scrip/'+scrip[index]+'/scripactive').text
        moneyfactor[index]  = float(tree.find('scrip/'+scrip[index]+'/profitloss').text)
        
        
        command = "curl \"https://api.kite.trade/instruments\" | grep \"%s2.*FUT\" | sort" %scrip[index]
    
        result  =   None
        try:
            result = os.popen(command).read()
        except Exception as e:
            printandlog ("Exception in reading trade instruments")
    
        #time.sleep(5)    
        #timecounter = 0
        #while(timecounter<5):
            #if(result):
            #    break
        #time.sleep(1)    
        #timecounter = 0
        if(result):
            line = result.split("\n")[0]
            out = line.split(",")
            out[5] = datetime.strptime(out[5],'%Y-%m-%d').strftime('%d%b%Y')
            out[5] = out[5].upper()
            out[3] = out[3][1:-1]
            if(out[3] == scrip[index]):
                instoken[index]     = out[0]
                tradingsymbol[index]= out[2]
            #symbol[index]         = 'MCX:' + tradingsymbol[index]
                symbol[index]       = tradingsymbol[index]
                expiry[index]       = str(out[5])
                #update the datasheet
                tree.find('scrip/'+scrip[index]+'/tradingsymbol').text  = tradingsymbol[index]
                tree.find('scrip/'+scrip[index]+'/symbol').text         = symbol[index]
                tree.find('scrip/'+scrip[index]+'/instoken').text       = instoken[index]
                tree.find('scrip/'+scrip[index]+'/expiry').text         = expiry[index]
                tree.find('scrip/'+scrip[index]+'/dayloss').text        = str(dayloss[index])
                tree.find('scrip/'+scrip[index]+'/scripactive').text    = scripactive[index]
                tree.write(datafile)
        
                init_ltp(marketval,index) 
                #get the trend through first 15 minutes data
    val = get_trend(index)

    return val
#new
def read_credentials ():
    global apikey
    global reqtoken
    global apisecret
    global accesstoken
    global closetime
    tree         = xml.parse("datafile.txt")

    # get credentials
    apikey       = str(tree.find('credentials/apikey').text)
    reqtoken     = str(tree.find('credentials/reqtoken').text)
    apisecret    = str(tree.find('credentials/apisecret').text)
    accesstoken  = str(tree.find('credentials/accesstoken').text)
    closetime    = str(tree.find('credentials/closetime').text)

def socket_init ():
    global s
    host    =   ''        # Symbolic name meaning all available interfaces
    port    =   12345     # Arbitrary non-privileged port
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

def kite_init ():
    global kite
    global logging 
    global rqtkn
    global debug_flag

    data    = None
    kite    = KiteConnect(apikey)
    if(not kite):
        logging.info ("Kite connect failed..Exiting")
        exit()

    if(debug_flag):
        logging.info ("Kite connect is successful")

    url     = kite.login_url()
    print (url)

    reqtoken= raw_input("Enter Request Token:")

    data    = kite.generate_session(reqtoken, api_secret=apisecret)
    if(not data):
        logging.info ("Session gererate call failed..Exiting!")
        exit()
    if(debug_flag):
        printandlog ("session Generation is  successful")

    val     = kite.set_access_token(data[accesstoken])
    if(not val):
        printandlog ("Access token could not be set..Exiting!")
        exit()
    if(debug_flag):
        logging.info ("Access token is set")
    
    tree        = xml.parse("datafile.txt")
    tree.find('credentials/reqtoken').text      = reqtoken
    tree.find('credentials/accesstoken').text   = data[accesstoken]
    tree.write("datafile.txt")
    logging.info ("reqtoken and accesstoken in the Datafile are updated")
    return 1

#new
def add_ele (rootele,newele):
    global xmlfile
    parser = etree.XMLParser(remove_blank_text=True)
    #tree = etree.parse('accounts.xml', parser)
    tree = etree.parse(xmlfile, parser)

    out = rootele.findall('./'+newele)
    if (not out):
        out = etree.SubElement(rootele,newele)
    else :
        out = out[0]

    tree.write(xmlfile, pretty_print=True)
    return out

def update_file (sym,ltp,txntypeval,prod):
    global xmlfile

    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xmlfile, parser)
    day = datetime.today().strftime('%Y%m%d')

    root = tree.getroot()
    daytag = add_ele(root,'day'+day)
    prodtag = add_ele(daytag,prod)
    symboltag = add_ele(prodtag,sym)
    
    leng = len(symboltag.getchildren())
    
    txntypetag = add_ele(symboltag,str(txntypeval)+str(leng+1))

    if(tree.find('day'+day+'/'+prod+'/'+sym+'/'+str(txntypeval)+str(leng+1)).text == None):
        tree.find('day'+day+'/'+prod+'/'+sym+'/'+str(txntypeval)+str(leng+1)).text = str(ltp)
        tree.write(xmlfile, pretty_print=True)
        return 1
    else :
        tree.write(xmlfile, pretty_print=True)
        return 0

def append_to_list(i,lis,liscntr,last_odr,index):
    global testmode

    if (testmode == 0):
        t_txntype           = 'txntype'

    elif (testmode == 1):
        t_txntype           = 5

    if(i[t_txntype] == 'BUY') :
        last_odr.append(1)
        liscntr[index] = liscntr[index]+1
    else:
        last_odr.append(-1)
        liscntr[index] = liscntr[index] - 1
    
    if(lis != [] and completed_ordr != []):
        # dont add but remove if we have a pair for this order     
        if(lis == completed_ordr):
            j = [it for it, lst in enumerate(lis[index]) if it[4] == last_odr[4]*(-1)][0]
            if j:
                completed_ordr[index].remove(j[-1])
            return 1
        if (lis[index] != [0]):
            lis[index].append(last_odr)
        else:
            lis[index][0] = last_odr[:]
        #sort the list based on orderid.
        #This is not necessary now but doing it for future use
        sorted(lis[index], key=operator.itemgetter(1), reverse=True)
        return 0
    return 1

def frame_order(copyitem,index):
    global testmode
    global open_ordr
    global completed_ordr
    global countpndg
    global countcmpt

    ordr                =   []

    if (testmode == 0):
        t_order_id          = 'order_id'
        t_parent_order_id   = 'parent_order_id'
        t_status            = 'status'
        t_txntype           = 'txntype'
        t_average_price     = 'average_price'
        t_product           = 'product'

    elif (testmode == 1):
        t_order_id          = 0
        t_parent_order_id   = 1
        t_status            = 2
        t_txntype           = 5
        t_average_price     = 6
        t_product           = 7

    ordr.append(copyitem[t_order_id])
    ordr.append(copyitem[t_parent_order_id])
    ordr.append(copyitem[t_average_price])
    ordr.append(copyitem[t_txntype])

    if ((copyitem[t_status] == 'TRIGGER PENDING') or (copyitem[t_status] =='OPEN PENDING')):
        append_to_list(copyitem,open_ordr,countpndg,ordr,index)
    elif (copyitem[t_status] == 'COMPLETE'):
        append_to_list(copyitem,completed_ordr,countcmpt,ordr,index)
    ordr.clear()

def update_offline_orders():
    global offline_orders
    global instoken
    
    if (offline_orders[0] != 0):
        for i in range(len(offline_orders)):
            for j in range(len(instoken)):
                if (offline_orders[i][4] == instoken[j]):
                    if(ltp[j] == offline_orders[i][6]):
                        offline_orders[i][2] = 'COMPLETE'
#new
def on_order_update (ws, data):
    global latest_txnid
    global countpndg
    global countcmpt
    global totalgains
    global counternrml
    global countermis
    global tree
    global testmode
    global scrip
    global offline_orders
    global xmlfile
    global tickLength

    for index in  range(0,tickLength):
        counternrml[index]  = 0
        countermis[index]   = 0
        totalgains[index]   = 0

    if (testmode == 0):
        t_order_id          = 'order_id'
        t_parent_order_id   = 'parent_order_id'
        t_status            = 'status'
        t_instrument_token  = 'instrument_token'
        t_txntype           = 'txntype'
        t_average_price     = 'average_price'
        t_product           = 'product'

        if((not ws) and (not data)) :
            ws.subscribe(token)
            ws.set_mode(kws.MODE_LTP, token)
  
        # Fetch all orders
        val     =   kite.orders()

    elif (testmode == 1):
        t_order_id          = 0
        t_parent_order_id   = 1
        t_status            = 2
        t_instrument_token  = 4
        t_txntype           = 5
        t_average_price     = 6
        t_product           = 7

        # Fetch all orders
        val     =   offline_orders
        #print(val)
    

    # make sure orders are fetched properly
    if(val!=[0] and len(val) != 0):
        # Open order and completed order lists are filled in this function.
        # if the lists are not cleared here, we need to find duplicate entry,
        # sync with completed orders, kite.order() etc.so, clear here itself
        open_ordr.clear()
        completed_ordr.clear()
        
        for i in val:
            # Update only those that are new 
            #print(i[t_order_id])
            #print(latest_txnid)
            #if (i[t_order_id] > int(latest_txnid)): # This is not required now
            if(True):
                latest_txnid = i[t_order_id]
                it = 0
                
                #get trading symbol and place data in the corresponding sublist
                index = [it for it, lst in enumerate(instoken) if str(i[t_instrument_token]) in str(lst)][0]
                it = 0
                
                #print("index :",index)
                if(confirm_wait[index]!=0):
                    # for all orders including cancelled orders ,
                    # check for the order in confirm_wait and remove it
                    subindex = [it for it, lst in enumerate(confirm_wait[index]) if str(i[t_order_id]) in str(lst)][0]
                    if(subindex):
                        confirm_wait[index].remove(subindex)
                        confirm_wait_t[index]   = 0
                    else:
                        confirm_wait_t[index]   = 1
                
                frame_order(i,index)
                #print("status:",i[t_status])
                if (str(i[t_status]) == 'COMPLETE'):
                    #print("order complete")
                    #update counters and calculate total gains
                    if(str(i[t_product]) == 'PRODUCT_NRML'):
                        counternrml[index] = counternrml[index] +1
                    elif(str(i[t_product]) == 'PRODUCT_MIS'):
                        countermis[index] = countermis[index] +1
                    else:
                        string  = "Error in product value "+ str(i[t_product])
                        printandlog(string)
                    
                    if(str(i[t_txntype]) == 'BUY'):
                        totalgains[index] = totalgains[index] - float(i[t_average_price])
                    elif(str(i[t_txntype]) == 'SELL'):
                        totalgains[index] = totalgains[index] + float(i[t_average_price])
                    else:
                        string  = "Error in Transaction type value "+ str(i[t_txntype])
                        printandlog(string)

                    if(open_ordr !=[]):
                        # now check for the order in pending list and remove it
                        subindex = [it for it, lst in enumerate(open_ordr[index]) if str(i[t_order_id]) in str(lst)][0]
                        if(subindex):
                            open_ordr[index].remove(subindex)
                            order_limit[index] = order_limit[index] -1
                            tree.find('scrip/'+scrip[index]+'/orderlimit').text = order_limit[index]
                                                        
                    # Check if this entry is already present in the file.
                    file_update = 1
                    with open(xmlfile) as f:
                        dat = f.read()
                        #if(not dat):
                            #print("No Data")
                        #    if(i[t_order_id] in dat):
                        #        print("orderid present")
                        #    else:
                        #        print("orderid not present")

                        if(str(i[t_order_id]) in f.read()):
                            file_update = 0
                            f.close()
                    if(file_update):
                        # entry not present. update accounts.xml file
                        data = str(i[t_order_id]) +':'+ str(i[t_average_price])
                        val = update_file(scrip[index],i[t_average_price],i[t_txntype],i[t_product])
                        f.close()
        return 1
    else :            
        # Error getting order list from kite. Return none without doing anything
        return None 

def frame_offline_orders(index,tx,product,stat):
    global local_order_id 
    global now
    global order_id
    global tradingsymbol
    global instoken
    global ltp

    orderlocal = [0]

#   0. order_id
    orderlocal[0] = order_id
    order_id = order_id + 1

#   1. parent_order_id
    orderlocal.append(order_id-1)

#   2. status
    orderlocal.append(stat)

#   3. tradingsymbol
    orderlocal.append(tradingsymbol[index])

#   4. instrument_token
    orderlocal.append(instoken[index])

#   5. transaction_type
    orderlocal.append(tx)

#   6. average_price
    orderlocal.append(ltp[index])

#   7. product
    orderlocal.append(product)
    
#   8. order_timestamp
    orderlocal.append(now)
    #print("framed offline orders: ",orderlocal)
    return orderlocal

def band_update(band,index,val):
    if(band[index][0] == 0):    # open
        band[index][0]  = val
    if(band[index][1] < val):   # high
        band[index][1]  = val
    if(band[index][2] > val):   # low
        band[index][2]  = val
    if(band[index][3] != val):  # close
        band[index][3]  = val       

def update_candle():
    global testmode 
    global tickLength
    global tickFlag
    global ltp 
    global onemin
    global fivemin
    global fifteenmin
    global thirtymin
    global onehour
    
    for index in range(0,tickLength):
        band_update(onemin,index,ltp[index]) 
        band_update(fivemin,index,ltp[index]) 
        band_update(fifteenmin,index,ltp[index]) 
        band_update(thirtymin,index,ltp[index]) 
        band_update(onehour,index,ltp[index]) 

def ltp_simulate():
    global tickFlag
    global tickLength
    global ltp
    global testltp
    global ltprecall
    global ltpsim

    threading.Timer(10,ltp_simulate).start()

    for index in range(0,tickLength) :
        ltpsim[index]  = ltpsim[index] + testltp[0][ltprecall]
        ltp[index]  = ltpsim[index]
        if(ltp[index] != 0.0):
            tickFlag = 1
    ltprecall = ltprecall +1

def get_ltp_online():
    global tickFlag
    global tickLength
    global ltpindex
    global ltp

    threading.Timer(20,get_ltp_online).start()
    marketval   = '0'
    marketval   = marketdata()
    if(marketval == '0'):
        printandlog("Could not fetch market data online!")
        return(0)

    for index in range(0,tickLength) :
        ltp[index]  = (float)(marketval[ltpindex[index]]['LTP'])
        if(ltp[index] != 0.0):
            tickFlag = 1
        
def on_ticks (ws, ticks):
    global ltp
    global tickLength
    global tickFlag

    # Callback to receive ticks.
    logging.debug("Ticks: {}".format(ticks))
    
    tickLength  = len(ticks)
    for i in range(0,tickLength):
        ltp[i]   = float(ticks[i]['last_price'])
        if(ltp[i] != 0.0):
            tickFlag = 1

def on_connect (ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (CRUDEOILAPR20FUT and SILVERMAPR20FUT here).
    global inst_token

    print(inst_token )
    print( 'subscriptionlist element is ', type(inst_token) )  #to confirm subscriptionlist items are int
    ws.subscribe(inst_token)

    # Set script to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP, [inst_token])

def on_close (ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

def ticker_init ():
    global kws
    # Initialise
    kws = KiteTicker(apikey, accesstoken, debug=True)

    # Assign the callbacks.
    kws.on_ticks        = on_ticks
    kws.on_connect      = on_connect
    kws.on_close        = on_close
    kws.on_order_update = on_order_update

    response = kws.connect( threaded=True, disable_ssl_verification=True, proxy=None)
    logging.info('KWS.connect done')

# remove the entry list from scrip sublist under pending list 
def list_remove (listhead,data):
    index = [it for it, lst in enumerate(listhead) if data in lst]
    listhead.pop(index[0])

# calltype 1 for new order, 2 for modify ,3 for exit and 4 for cancel
def try_order(calltype,content):
    global orderupdate

    ordered_id  = None
    try:
       if(calltype == 1) :
           logging.info("Placing a new order...")
           ordered_id   = kite.place_order(content)
       elif(calltype == 2) :
           logging.info("Modifying an existing order...")
           ordered_id   = kite.modify_order(content)
       elif(calltype == 3) :
           logging.info("Exiting an existing order...")
           ordered_id   = kite.exit_order(content)
       elif(calltype == 4) :
           logging.info("Cancelling an existing order...")
           ordered_id   = kite.cancel_order(content)
       
       #time.sleep(1)
       orderupdate      = orderupdate + 1
       logging.info("Order placed. ID is: {}".format(ordered_id))
    except Exception as e:
       logging.info("Order placement failed: {}".format(e.message))
       #time.sleep(1)
    
    return ordered_id


# item from only pending list can be cancelled.
# Delete from pending_list if 1 is returned
# This is  most likely an EoD closure.Ensure no TRIGGER PENDING order in kite.order()
# argument : item from pending list
def cancel (odr):
    global testmode
    t_order_id          = 0
    t_parent_order_id   = 1
    t_status            = 2
    t_txntype           = 5
    t_average_price     = 6

    if(testmode == 0):
        content = "variety=%s, order_id=%s" %(variety,odr[t_order_id])
        if(odr[1] != 0):
            content = content + "parent_order_id=%s" %odr[t_parent_order_id]
        return(try_order(4,content))
    elif (testmode == 1):
        odr[t_status] = 'CANCELLED'
    return(0)

# item from only pending list can exit.
# check if this triggers on_order_update, if so, no need to do anything
# else delete from pending list 
# argument : item from pending list
def end_order (odr):
    global testmode
    t_order_id          = 0
    t_status            = 2
    t_instrument_token  = 4
    t_average_price     = 6

    if(testmode == 0):
        content = "variety=%s, order_id=%s" %(variety,odr[t_order_id])
        return(try_order(3,content))
    elif (testmode == 1):
        index = [it for it, lst in enumerate(instoken) if odr[t_instrument_token] in lst][0]
        odr[t_status]           = 'COMPLETE'
        odr[t_average_price]    = ltp[index]
    return(0)

# item from only pending list can be modified.
# Delete from pending_list if 1 is returned
# call book keeping if 1 is returned 
# argument : item from pending list,price,trigger_price
def modify (odr,pr,tpr,sl):
    global testmode
    t_order_id          = 0
    t_parent_order_id   = 1
    t_average_price     = 6

    if(testmode == 0):
        content = "variety=%s, order_id=%s, parent_order_id=%s, quantity=None, price=%s, order_type=None, trigger_price=%s, validity=None, disclosed_quantity=None" %(variety[index],odr[t_order_id],odr[t_parent_order_id],pr,tpr)
        return(try_order(2,content))
    elif (testmode == 1):
        odr[t_average_price] = pr
    return(0)

# def       : call_order
# arguments : commodity index, txntype: BUY/SELL
# Function  : wrapper function to place a new order
def call_order (index,txntype,ordertype,product):
    global testmode
    global trigger
    global trend
    global ltp
    global variety 
    global offline_orders

    func_name = sys._getframe().f_code.co_name
    #print("Executing the function "+func_name)

    if (variety[index] == 'VARIETY_CO'):
        sign = 0
    
        if (txntype == 'BUY'):
            sign    = 1
        elif (txntype == 'SELL'):
            sign    = -1
        
        price   = 1 # dummy value...needs to be corrected
        #price       = ltp[index] + float(10*(sign * scripfactor[index]) )
        #trig        = trigger[index]
    
    if (testmode == 0):
        if (variety[index] == 'VARIETY_CO'):
            content = "variety=%s,exchange=%s,tradingsymbol=\"%s\",transaction_type=%s,order_type=ORDER_TYPE_LIMIT,price=%s,trigger_price=trig" %(variety[index],exchange,tradingsymbol[index],txntype,price,trig)
        else:
            content = "variety=VARIETY_REGULAR,exchange=%s,tradingsymbol=\"%s\",transaction_type=%s,order_type=%s,product=%s" %(variety[index],exchange,tradingsymbol[index],txntype,ordertype,product)

        return(try_order(1,content))

    elif (testmode == 1):
        if (variety[index] == 'VARIETY_CO'):
            offline_orders.append(frame_offline_orders(index,txntype,product,'OPEN PENDING'))
            if (txntype == 'BUY'): # place second leg
                offline_orders.append(frame_offline_orders(index,'SELL',product,'TRIGGER PENDING'))
            elif (txntype == 'SELL'): # place second leg
                offline_orders.append(frame_offline_orders(index,'BUY',product,'TRIGGER PENDING'))
        else:
            if(offline_orders != [0]):
                offline_orders.append(frame_offline_orders(index,txntype,product,'COMPLETE'))
            else:
                offline_orders[0] = frame_offline_orders(index,txntype,product,'COMPLETE')[:]

        return (order_id)

def place_second_leg(index):
    global closetime
    # Two possibilities here 
    # i . Time limit (or)
    # ii. second leg order is in pending list 
    for i in open_ordr[index]:
        val = None
        if(now.strftime('%H:%M:%S') >= closetime):
            logging.info ("Trading Time limit reached.exit all pending orders!")
            val = end_order(i)
        else: # Time is okay
            #i[2] is the price and  i[3] is BUY/SELL 
            delta = i[4]*(i[2] - ltp[index])
            # check  for  Rs.500/- difference
            if (delta >= scripfactor[index]):
                modifyprice = (ltp[index]+(i[4]*scripfactor[index]))
                val = modify_order(i[0],modifyprice,1.5*modifyprice)
                if(not val):
                    return None
            elif(delta <0):
                # order gone below stop loss
                # this is less likely to happen
                val = end_order(i)
                if(not val):
                    return (None)
    # call: record keeping here
    return(on_order_update(None,None))

# The strategy is to set stoploss equivalent to Rs.500/-
# and to trail by stoploss equivalent to Rs.500/-  
def strategy5point (index):
        global countcmpt
        global countpndg
        global order_limit
        global closetime
        
        # countcmpt and countpndg can take 0,-1,+1.so,9 combinations here
        if(countcmpt[index] == 0):
        # Two possibilities here 
        # i . Either this is the start of trade (or)
        # ii. All pending trades are closed 
            if(now.strftime('%H:%M:%S') >= closetime):
                logging.info ("Trading Time limit reached.Exit after all orders are closed!")

            elif (order_limit[index] == 0) :
                print ("Order limit reached for %s" %symbol[index])
                exit()
            elif(not countpndg[index]):
                # This for start of the day or when no order is pending
                val = None
                val = get_trend(index)

                if(not val):
                    print ("Could not getting trigger value for %s" %symbol[index])
                    return None

                if(trigger[index] != None):
                    logging.info ("start_trading: calling call_order!") 
                    val = call_order(index,txtype[index],'ORDER_TYPE_LIMIT','PRODUCT_MIS')
                    if(val != None):
                        if(variety != "VARIETY_CO"):
                            print ("Limit order has been placed.Place second leg order!")
                        # place stoploss order
                        # make sure ,first leg order is active
                        # call: record keeping here
                        return(on_order_update(None,None))
                    else: # call_order failed 
                        print ("new order placement failed for %s" %symbol[index])
                        return None
                # if pending orders are present ,two cases
                # if time is reached , calcel all pending orders
                # else adjust the trigger
            elif (countpndg[index]) :# pending list has  members
                return(place_second_leg(index))
        elif (countcmpt[index] != 0):
            if((countpndg[index] == 0) or (countpndg[index]+countcmpt[index] !=0)):
                # place second leg here
                if(countcmpt[index] > 0):
                    trend[index]     = -1
                    txtype[index]   = 'SELL'
                elif(countcmpt[index] < 0):
                    trend[index]     = 1
                    txtype[index]   = 'BUY'

                trigger[index]   = ltp[index] + (trend[index]*scripfactor[index])
                stoploss[index]  = ltp[index] - (trend[index]*scripfactor[index])
                
                #place the second leg order
                val = call_order(index,txtype[index],'ORDER_TYPE_LIMIT','PRODUCT_MIS')
                if(val != None):
                    if(variety != "VARIETY_CO"):
                        print ("Limit order has been placed.Place second leg order!")
                        return(on_order_update(None,None))
                    else: # call_order failed 
                        print ("new order placement failed for %s" %symbol[index])
                        return (None)
                                
            elif(countpndg[index] != 0):        
                return(place_second_leg(index))

# Check if any order is not confirmed
def check_confirm_wait(index):
    global confirm_wait_t
    global confirm_wait

    # if order is placed but confirmation hasnt come,
    # check update order and return 
    if(confirm_wait[index]):
        if(confirm_wait_t[index] >= 20):
            for i in confirm_wait[index]:
                confirm_wait[index].remove(0)
            confirm_wait_t[index]  = 0

        confirm_wait_t[index]   = confirm_wait_t[index] +1
        
        # set total gains to 0 as PL is calculated 
        # afresh everytime on_order_update is called 
        val                     = on_order_update(None,None)

        if(confirm_wait[index]):
            logging.info("Order is in waiting queue.cant place a new order")    
            return (None)

    return(1)

def cancel_or_exit(lis,index):
    global confirm_wait_t
    global confirm_wait
    global countcmpt

    for i in lis:
        val = None
        if(countcmpt[index] == 0) :
            val = cancel(i)
        elif(countcmpt[index] != 0) :
            val = end_order(i)
        confirm_wait[index].append(val)
        confirm_wait_t[index] =  1
    return(0)

# Check if end time is reached.if so,signal to close the trade 
def time_check (index):
    global confirm_wait_t
    global confirm_wait
    global countcmpt
    global countpndg
    global closetime

    if(not check_confirm_wait(index)):
        return (None)

    if((now.strftime('%H:%M:%S') >= closetime) or (order_limit[index] == 0)):
        if((countcmpt[index] == 0) and (countpndg[index] == 0)):
            logging.info ("Trading Time limit reached.No new trade! Exiting")
            return (None)
        elif(countpndg[index] != 0) :
            if(now.strftime('%H:%M:%S') >= closetime) :
                # if timelimit is hit ,cancel or exit
                cancel_or_exit(open_ordr,index)
            return (None)
    return (1)

# modify the order,moving towards ltp
def adjust_open_order(index,high,low):
    global open_ordr

    end     = [it for it, i in open_ordr[index] if ((i[2] - ltp[index])*i[4] <0)]
    cancel_or_exit(end,index)
    
    # add logic to adjust sl based on realtime data

    # adjust trigger to Rs.500 diff with ltp
    adjust  = [it for it, i in open_ordr[index] if ((i[2] - ltp[index])*i[4] > scripfactor[index])]
    trigger = ltp[index]- i[4]* scripfactor[index]
    for lis in adjust:
        modify(lis,trigger+i[4]*0.2*scripfactor[index],trigger,None)
    
    return(0)


# The strategy is to set stoploss equivalent to close price
# of last five minute band and exit if target is hit
def strategy5minband (index,end):
    global countcmpt
    global countpndg
    global totalgains    
    # if time limit is hit,Either cancel,exit order or do nothing
    if(not timecheck(index)):
        return None
    
    # 9 conditions here : countcmpt =[0,1,-1] and countpndg= [0,1,-1] 
    #if((countpndg[index] == 0) or (abs(countcmpt[index]) - abs(countpndg[index])  != 0)) :
        # under this case , only new orders are placed.no other possibility
        # 1. get trend for 30 mins and one hour
        # 2. place order at prev 15min open and second leg at 15min close
        # 3. Update the order list
        #if(countcmpt[index] == 0) :
        # New First leg order has to be placed 
        #elif (countcmpt[index] != 0) :
        # New second leg order has to be placed
    # elif is not used as pending orders went in above case(abs()) are to be processed     
    if(countpndg[index] != 0) :
        adjust_open_order(index)
    
    return(on_order_update(None,None))

def endscripTrade(index):
    global counternrml
    global countermis
    global ltp
    global scrip

    if(counternrml[index]%2 ==1):
        logging.info("**********************************")
        logging.info("ORDER: closing {} NRML SELL for {}".format(scrip[index],ltp[index]))
        logging.info("**********************************")
        return(call_order(index,'SELL','ORDER_TYPE_MARKET','PRODUCT_NRML'))
    if(countermis[index]%2 ==1):
        logging.info("**********************************")
        logging.info("ORDER: closing {} MIS BUY for {}".format(scrip[index],ltp[index]))
        logging.info("**********************************")
        return(call_order(index,'BUY','ORDER_TYPE_MARKET','PRODUCT_MIS'))

def netpl_reached(index):
    global totalgains
    global counternrml
    global countermis
    global dayloss
    global moneyfactor
    global ltp
    global refband
    global bookedprofit

    netpl = 0.0
    
    #print(scrip[index],"band start:" ,refband[index][4]," band end: ",refband[index][7])
    print("nrml count =",counternrml[index],"mis count = ",countermis[index])
    if((counternrml[index] + countermis[index])%2 == 0):
        print("even count")
        netpl = totalgains[index]
    elif((counternrml[index])%2 != 0):
        print("nrml on")
        print(totalgains[index])
        print(ltp[index])
        print(netpl)
        netpl = totalgains[index] + ltp[index]
    elif((countermis[index])%2 != 0):
        print("mis on")
        netpl = totalgains[index] - ltp[index]

    netpl   = float("{:.2f}".format(netpl))
    pl = scrip[index]+":P/L for the day(in Rs.):"+str(netpl * moneyfactor[index])
    print("netpl:",netpl)
    printandlog(pl)
    
    logging.info("gains: {} day loss {} dayprofit {} netpl {}".format(totalgains[index],dayloss[index],dayprofit[index],netpl))
    printandlog("**********************************")
    print("Booked Profit:",bookedprofit[index])
    print("dayloss:",dayloss[index]) 
    if((netpl - bookedprofit[index]) > (-1*(dayloss[index]/2))):
        string = str(scrip[index])+": Step target reached.booking the profit !!"
        printandlog(string)
        cancel_or_exit(open_ordr,index)
        bookedprofit[index]      = netpl
        on_order_update(None,None)
        orderdecision(index)
        return(0)

    if((netpl-bookedprofit[index]) < dayloss[index]):
        string = str(scrip[index])+": Maximum Loss for the scrip has been reached.Exiting this scrip!!"
        printandlog(string)
        scripactive[index]  = '0'
        return(1)

    if(netpl > dayprofit[index]):      
        string = str(scrip[index])+": Maximum profit for the scrip has been reached.Exiting this scrip!!"
        printandlog(string)
        scripactive[index]  = '0'
        return(1)
    return(0)

def orderdecision(index):
    global refband
    global totalgains
    global counternrml
    global countermis
    global now 
    global ltp
    global closetime
    global candleStart
    global candleEnd
    global smallCandle
    global scripfactor
    
    if(now.strftime('%H:%M:%S') >= closetime):
        logging.info ("Trading Time limit reached.Exit after all orders are closed!")
        return(endscripTrade(index))

    if(refband[index][6] != 0.0):
        logging.info("candleEnd {} index {} refband{} close :{}".format(candleEnd[index],index,refband[index],refband[index][7]))
        candleEnd[index] = refband[index][7]
        if(smallCandle[index] != 1):
            candleStart[index] = refband[index][4]
    else:
        logging.info("{}: last candle not updated".format(scrip[index]))
        return(0)
    
    string = "Open price:",str(candleStart[index]),"  Close price:",str(candleEnd[index])
    printandlog(string)
    if(candleEnd[index]>candleStart[index]):
        if(candleEnd[index]-candleStart[index]<scripfactor[index]):
            smallCandle[index] = 1
            return(0)
        else:
            smallCandle[index] = 0

        if(counternrml[index]%2 ==0 ):
            string  = scrip[index] + "ORDER: NRML Buy.Trend Up!"
            printandlog(string)
            return(call_order(index,'BUY','ORDER_TYPE_MARKET','PRODUCT_NRML'))
        elif(countermis[index] %2 ==1):
            # active sell order case
            string  = scrip[index] + "ORDER: MIS Buy to close Sell.Trend reversed Up!"
            printandlog(string)
            return(call_order(index,'BUY','ORDER_TYPE_MARKET','PRODUCT_MIS'))

    elif(candleStart[index]>candleEnd[index]):
        if(candleStart[index]-candleEnd[index]< scripfactor[index]):
            smallCandle[index] = 1
            return(0)
        else:
            smallCandle[index] = 0

        if(countermis[index]%2 ==0):
            # initial condition ,when no order is done
            string  = scrip[index] + "ORDER: MIS Sell.Trend Down!"
            printandlog(string)
            return(call_order(index,'SELL','ORDER_TYPE_MARKET','PRODUCT_MIS'))
        elif(counternrml[index] %2 ==1):
            # active buy order case
            string  = scrip[index] + "ORDER: NRML Sell to close Buy.Trend reversed Down!"
            printandlog(string)
            return(call_order(index,'SELL','ORDER_TYPE_MARKET','PRODUCT_NRML'))
    return(0)

# Nonpositional strategy
#
# Open: if the closing price of the last candle is greater than 
# the closing price of the previous green candle,go for a buy
# else if the closing price of the last candle is lesser than the closing price 
# of the previous red candle ,go for sell
# else if closing price of red candle is below the opening price of previous green
# or vice versa, go for the respective position without closing the previous call
#
# After the above steps,if next candle closes in the same direction as previous ,
# close the opposite side candle.else wait for the next candle
# 
# Close : 1 unit increase 
#
# Starting time : 3rd candle of the day
# End time : till volatility increses , in the evening
# 
# Margin Requirement : 1 NRML buy  + 1 MIS Sell + losses + brokerage   
# Stop loss    :  2 net losses per day
# Stop Gain    : 10 net gains per day
# least Profit : Loss 18 days , Profit 4 days , Net Profit per month 4 Gains
# Least Loss   : Loss 19 days, Profit 3 days , Net loss per month 8 Losses
# Maximum loss : Loss 22 days..44 Losses
#
# Call this function once every 15 minutes from main
def strategyNonPositional():
    global now
    global tickLength
    
    out = 0

    func_name = sys._getframe().f_code.co_name
    for index in  range(0,tickLength):
        out = 1
        logging.info("***********************************")
        if(scripactive[index] !='1'):
            string = scrip[index]+" not active"
            printandlog(string)
            continue
    
        if(not check_confirm_wait(index)):
            string = scrip[index]+" Order Pending"
            printandlog(string)
            continue
        
        if(refband[index][4] == 0.0 or refband[index][7] == 0.0):
            string = scrip[index]+" LTP didn't initiate"
            printandlog(string)
            continue

        if(refband[index][4] == refband[index][7]):
            string = scrip[index]+" LTP didn't change"
            printandlog(string)
            continue
        else:
            logging.info("{} open price:{}  close price:{}".format(scrip[index],refband[index][4],refband[index][7]))
    
        #if (netpl_reached(index)):
         #   print(scrip[index]," Maximum profit loss for the scrip has been reached.Exiting this scrip!!")
         #   logging.info("{} Maximum profit loss for the scrip has been reached.Exiting this scrip!!".format(scrip[index]))
         #   scripactive[index] = '0'
         #   call_scrip()
         #   if(endscripTrade(index)):
         #       continue
    
        out = out + orderdecision(index)
        logging.info("***********************************")

    return(out)

def parse (data):
        global txtype
        global trigger
        global index 

        call_request = data.split("*")
        if(call_request[0] == "S"):
            txtype = "SELL"
        elif(call_request[0] == "B"):
            txtype = "BUY"
        else:
            print ("Error: Invalid Request..Neither BUY nor SELL")
            return  None
        
        trigger = str(call_request[1]) 
        call_order(index,txtype,'ORDER_TYPE_MARKET','PRODUCT_MIS')
        conn.sendall("transaction_type="+txtype+",trigger="+trigger)
        return 1

def call_scrip():
    global tickLength
    global scrip
    
    tickLength = 0
    logging.info("Init Script")
    scrip[0] = 'NATURALGAS'
    tickLength = tickLength +1
    #scrip[1] = 'SILVERM'
    #tickLength = tickLength +1
    #scrip[2] = 'GOLDM'
    #tickLength = tickLength +1
    scrip_init()    

def ctrlchandler(signum, frame):
    global tickLength
    global counternrml
    global countermis
    result = 1

    printandlog ("Ctrl+c from user.Exit after all orders are closed!")
    
    for index in  range(0,tickLength):
        endscripTrade(index)
    sys.exit()

def main ():
    global conn
    global trade_flag
    global now
    global logger
    global debug_flag
    global mincount  
    global tickLength
    global tickFlag
    global testmode
    global fifteenflag
    global closetime
    global xmlfile
    global refinterval
    global scrip
    global scripactive

    now                 = datetime.now()
    LOG_FILENAME        = datetime.now().strftime('logs/logfile_%H%M%S_%d%m%Y.log')
    logger              = logging.getLogger('my-logger')
    logger.propagate    = True
    if(debug_flag):
        logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO) 
    
    signal.signal(signal.SIGINT, ctrlchandler)
    # wait till time hits multiples of 15 minutes
    printandlog("In main function")    
    call_scrip()
    printandlog("starting script run")
    
    if(testmode == 0):
        xmlfile = 'accounts.xml'
        kite_init()
        ticker_init()
        
        # reconcilliation, incase of a restart.else, this will have no effect 
        on_order_update(None,None)
    
    else :              # test mode operation
        xmlfile = 'offlineaccounts.xml'
        printandlog("Getting LTP online")
        get_ltp_online()
        #ltp_simulate()

        printandlog("waiting for tickFlag")
        while(tickFlag != 1):
            time.sleep(1)
            

    printandlog("Reading credentials")
    read_credentials()
    
    now         =  datetime.now()
    while (now.minute%refinterval):
        now     =  datetime.now()
    printandlog("Getting OHLC")
    find_ohlc()
    minCount    = 0
    
    index       = 0
    logging.info("Getting on order flag")
    while (1):
        if(tickFlag):
            update_candle()
            tickFlag = 0

        now = datetime.now()
        if(now.strftime('%H:%M:%S') >= closetime):
            end_trade = True
            logging.info ("Trading Time limit reached.Exit after all orders are closed!")
        
        if(fifteenflag and check_internet()):
            printandlog("***********************************")
            print("Time: ",now.strftime('%H:%M:%S'))
            logging.info("Time: {}".format(now.strftime('%H:%M:%S')))
            #if(strategyNonPositional()):
            #    on_order_update(None,None)
                
            strategyNonPositional()
            for index in  range(0,tickLength):
                if(netpl_reached(index)):
                    call_scrip()
                    if(endscripTrade(index)):
                        continue
            on_order_update(None,None)

            printandlog("***********************************")
            fifteenflag = 0

    #socket_init()
    
    #s.listen(1)
    #conn, addr  = s.accept()

    #while True:
    #    try:
    #        data = conn.recv(1024)
    #        if not data: 
    #            print ("No Data.")
    #            #break
    #            conn.close()
    #        else:
    #            print('Connected by', addr)
    #            print ("Requested: "+data)
    #            parse(data)
                #conn.sendall("Reply from Server: welcome!")
    #    except socket.error:
    #        print ("Socket Error Occured.")
    #        break
        
    #conn.close()

if __name__ == "__main__":
    main()
