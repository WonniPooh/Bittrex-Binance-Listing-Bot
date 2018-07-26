
import time
import os
import urllib.request
import urllib3
import json
import threading
from threading import Thread
from bs4 import BeautifulSoup

urllib3.disable_warnings()

class CMC_Assets(Thread):
    def __init__(self, assets_num):
        Thread.__init__(self)
        self.assets_num = assets_num
        self.lock = threading.Lock()
        self.thread_exit_time = False
        self.assets = self.load_assets(assets_num) 
    
    def find_asset(self, asset_symbol):
        asset_symbol = asset_symbol.upper()
        for asset in self.assets:
            if asset.symbol == asset_symbol:
                return asset

    def get_avg_change(self):
        avg_change = 0
        for i in range(self.assets_num):
            avg_change += self.assets[i].daily_change
        avg_change /= self.assets_num
        return avg_change
    
    def run(self):
        iters = int(self.assets_num / 100) + (not not self.assets_num % 100) + 1
        http = urllib3.PoolManager()
        
        while(self.thread_exit_time == False):

            for i in range(1, iters):
                try:
                    r = http.request('GET', 'https://coinmarketcap.com/' + str(i))
                except urllib3.exceptions.TimeoutError:
                    print('CMC update exception!')
                    continue

                soup_handler = BeautifulSoup(r.data, "lxml")
                market_list = soup_handler.find_all('tr')
                inside_iters = 101

                if i == iters - 1:
                    inside_iters = self.assets_num % 100 + 1

                for j in range(1, inside_iters):
                    
                    try:
                        market_data = market_list[j].find_all('td')
                    except IndexError:
                        break

                    index = (i-1)*100 + j-1

                    self.lock.acquire()
                    self.assets[index].cap = int(market_data[2].text.strip()[1:].replace(',', ''))
                    self.assets[index].daily_change = float(market_data[6].text.strip()[:-1])
                    self.assets[index].price = float(market_data[3].text.strip()[1:])
                    self.lock.release()
            
            time.sleep(300)

        self.thread_exit_time == False
        
    def load_assets(self, assets_amount):
        assets = []

        http = urllib3.PoolManager()
        r = http.request('GET', 'https://s2.coinmarketcap.com/generated/search/quick_search.json')
        parsed_json = json.loads(r.data)
        
        for i in range(assets_amount):
            print('loading assets: ', i)
            current_asset = Crypto_Asset()
            current_asset.name = parsed_json[i]["name"]
            current_asset.symbol = parsed_json[i]["symbol"]
            current_asset.rank = parsed_json[i]["rank"]
            current_asset.slug = parsed_json[i]["slug"]
            current_asset.id = parsed_json[i]["id"]

            try:
                r = http.request('GET', 'https://coinmarketcap.com/currencies/' + current_asset.slug)
            except urllib3.exceptions.TimeoutError:
                continue

            assets.append(current_asset)
            soup_handler = BeautifulSoup(r.data, "lxml")
            market_list = soup_handler.find_all('tr')
        
            for j in range(1, len(market_list)):
                
                market_data = market_list[j].find_all('td')
                market_name = market_data[1].text.strip()
                pairs_array = assets[i].markets.get(market_name)

                if pairs_array == None:
                    assets[i].markets[market_name] = []
                    pairs_array = assets[i].markets.get(market_name)

                pairs_array.append(market_data[2].text.strip())
            
        return assets

class Crypto_Asset:
    def __init__(self):
        self.name = ''
        self.symbol = ''
        self.rank = -1
        self.id = -1
        self.slug = ''
        self.markets = {}
        self.cap = 0.0
        self.price = 0.0
        self.daily_change = 0.0  
    
    def print_all(self):
        print ('Name:', self.name)
        print ('Symbol:', self.symbol)
        print ('Rank:', self.rank)
        print ('ID:', self.id)
        print ('Slug:', self.slug)
        print ('Cap:', self.cap)
        print ('Price:', self.price )
        print ('Change:', self.daily_change, "%")
        
