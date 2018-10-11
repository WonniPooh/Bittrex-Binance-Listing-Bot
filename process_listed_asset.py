import time
import threading
from threading import Thread

from listed_asset_order_supervisor import *
from market_settings import *

class Listed_Asset_Handler():
    def __init__(self, available_markets):#, cmc_assets):

        #self.cmc_assets = cmc_assets
        self.available_markets = available_markets
        self.lock = threading.Lock()
        self.order_supervisors = []

    def handle_event(self, listed_asset_symbol):
        #Listed asset symbol takes upper, as is from Binance news
        self.lock.acquire()
        #self.clean_supervisors()
    
        markets_to_use = []

        for i in range(len(self.available_markets)):
            if self.available_markets[i].market_api.check_asset_available(listed_asset_symbol) == True:
                markets_to_use.append(self.available_markets[i])                

        # for asset in self.cmc_assets.assets:
        #     if asset.symbol == listed_asset_symbol:
        #         founded_asset = asset
        #         break

        if len(markets_to_use) == 0:
            print ('Asset with symbol', listed_asset_symbol, 'was not founded in available markets assets!')
            self.lock.release()
            return
        else:
            print('Listed_Asset_Handler::handle_event::asset founded!')

        #print('Listed_Asset_Handler::handle_event::markets to use :', markets_to_use[:].market_api.name)

        supervised_order = Listing_Order_Supervisor(listed_asset_symbol, markets_to_use) #self.cmc_assets, founded_asset, markets_to_use)

        self.order_supervisors.insert(0, supervised_order)
        supervised_order.setDaemon(True)
        supervised_order.start()

        print ("Listed asset supervisor started!")
        supervised_order.join() # DELETE IT TEST MODE!!!
#       print ("Order supervisor ended!")

        self.lock.release()

    def clean_supervisors(self):
        for supervisor in self.order_supervisors:
            if supervisor.finished == True:
                self.order_supervisors.remove(supervisor)


#{'OT': 'SELL', 'R': 0.0369021, 'Q': 0.08130079, 'T': 1536152942873}