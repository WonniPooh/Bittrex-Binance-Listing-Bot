import urllib3.request
import json
import sys
import datetime
import time

import threading
from threading import Thread

from binance_check import *
from Bittrex_API import *
from Crypto_Asset import *
from market_settings import *
from process_listed_asset import *

#from listed_asset_order_supervisor import * 

urllib3.disable_warnings()


def my_main():

    print('Initializing CMC connection...')
    assets = CMC_Assets(300)
    assets.setDaemon(True)
    assets.start()
    print('Done.')


    print('Connecting to Bittrex...')
    bittrex_handler = Bittrex_Api() 
    #huobi_handler = Huobi_API(access, secret) 
    bittrex_settings = Market_Settings(bittrex_handler,  asset_buy_on='BTC', stop_profit_percent=1.24, direct_purchase=False, asset_to_swap='USDT', amount_to_invest=950)
    print('Done')

    available_markets = [bittrex_settings]

    listing_handler = Listed_Asset_Handler(assets, available_markets)
    #listing_handler.handle_event('XRP')
#    print('Creating an order...')
#    listing_handler.handle_event('TRX')
#    print('Done! Good job!')

    #print ('Starting to look at Binance...')
    news = Binance_News(listing_handler, beep_enabled = False)

    news.setDaemon(True)
    news.start()
    news.join()

my_main()
