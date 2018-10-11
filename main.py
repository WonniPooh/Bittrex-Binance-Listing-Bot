import urllib3.request
import json
import sys
import datetime
import time

import threading
from threading import Thread

from binance_check import *
from Bittrex_API import *
from market_settings import *
from process_listed_asset import *
from Bittrex_Balance_Manager import *

# from Crypto_Asset import *

urllib3.disable_warnings()


def my_main():

    # print('Initializing CMC connection...')
    # assets = CMC_Assets(300)
    # assets.setDaemon(True)
    # assets.start()
    # print('Done.')


    print('Connecting to Bittrex...')
    bittrex_handler = Bittrex_Api()
    
    bittrex_settings = Market_Settings(bittrex_handler, return_initial_asset=True,  asset_buy_on='BTC', stop_profit_percent=1.13, 
                                       direct_purchase=False, asset_to_swap='TUSD', amount_to_invest=150)
    print('Done')

    available_markets = [bittrex_settings]
    listing_handler = Listed_Asset_Handler(available_markets) #assets)
    
    # time.sleep(15)
    # listing_handler.handle_event('XRP')
    # print('Creating an order...')
    # listing_handler.handle_event('TRX')
    # print('Done! Good job!')

    print ('Starting to look at Binance...')
    news = Binance_News(listing_handler, beep_enabled = False, delay_between_requests = 0.08)

    news.setDaemon(True)
    news.start()
    news.join()

my_main()
