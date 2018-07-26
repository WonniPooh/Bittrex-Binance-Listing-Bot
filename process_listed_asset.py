import time
import threading
from threading import Thread

from listed_asset_order_supervisor import *
from market_settings import *

class Listed_Asset_Handler():
    def __init__(self, assets, available_markets):

        self.available_markets = available_markets
        self.lock = threading.Lock()
        self.order_supervisors = []
        self.cmc_assets = assets

    def handle_event(self, listed_asset_symbol):
        self.lock.acquire()
        self.clean_supervisors()
    
        markets_to_use = []
        founded_asset = None

        for i in range(len(self.available_markets)):
            if self.available_markets[i].market_api.check_asset_available(listed_asset_symbol) == True:
                markets_to_use.append(self.available_markets[i])                

        for i in range(self.cmc_assets.assets_num):
            if self.cmc_assets.assets[i].symbol == listed_asset_symbol:
                founded_asset = self.cmc_assets.assets[i]
                break

        if len(markets_to_use) == 0:
            print ('Asset with symbol', listed_asset_symbol, 'was not founded in available markets assets!')
            self.lock.release()
            return
        else:
            print('Listed_Asset_Handler::handle_event::founded_asset :')
            founded_asset.print_all()

        #print('Listed_Asset_Handler::handle_event::markets to use :', markets_to_use[:].market_api.name)

        supervised_order = Listing_Order_Supervisor(self.cmc_assets, founded_asset, markets_to_use)

        print ("Order supervisor created!")

        self.order_supervisors.insert(0, supervised_order)
        supervised_order.setDaemon(True)
        supervised_order.start()

#       print ("Order supervisor started!")
        supervised_order.join() # DELETE IT TEST MODE!!!
#       print ("Order supervisor ended!")

        self.lock.release()

    def clean_supervisors(self):
        for supervisor in self.order_supervisors:
            if supervisor.finished == True:
                self.order_supervisors.remove(supervisor)

