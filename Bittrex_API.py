import time
import hmac
import urllib3.request
import json
import hashlib
from Bittrex_Balance_Manager import *
from bittrex_websocket import OrderBook


class Bittrex_Api():
    def __init__(self):

        self.main_adress = 'https://bittrex.com/api/v1.1/'
        self.private_key = '17f88028747144948b216d6c5e2f1a9c'
        
        self.public_key = 'b5f96df3b6d6409c903c0c9a300b1cc1'
        self.ticks_perionds = ['oneMin', 'fiveMin', 'thirtyMin', 'Hour', 'Day']
        
        self.balances = {}
        self.update_balances()

        self.markets = {}
        self.update_markets()
        
        self.btc_tickers = self.get_btc_pairs()
        self.btc_tickers.append('USDT-BTC')

        self.ws_orderbook_class = OrderBook()
        self.ws_orderbook_class.subscribe_to_exchange_deltas(self.btc_tickers)

        self.balances_manager = Bittrex_Balance_Manager(self.balances)
        self.balances_manager.authenticate(self.public_key, self.private_key)

    def get_btc_pairs(self):
        pairs_list = list(self.markets.values())
        btc_pairs_only = []

        for pairs in pairs_list:
            for pair in pairs:
                if pair[1] == True and pair[0] == 'BTC':
                    btc_pairs_only.append(pair[2])

        return btc_pairs_only

    def get_nounce(self):
        return '&nonce=' + str(int(time.time() * 1000))
    
    def update_markets(self): 
    #{ primary_asset: [(secondary_asset(BTC\ETH), is_available, market_name), ...] ... }
    
        assets_dict = {}
        http = urllib3.PoolManager()
        r = http.request('GET', 'https://bittrex.com/api/v1.1/public/getmarkets')

        parsed_json = json.loads(r.data)

        for i in range(len(parsed_json['result'])):

            market_currency = parsed_json['result'][i]['MarketCurrency'] 
            base_currency = parsed_json['result'][i]['BaseCurrency']
            is_active = parsed_json['result'][i]['IsActive']
            market_name = parsed_json['result'][i]['MarketName']

            if(market_currency in assets_dict):
                m_list = assets_dict[market_currency]
                m_list.append((base_currency, is_active, market_name))
            else:
                assets_dict[market_currency] = [(base_currency, is_active, market_name)] 
        self.markets = assets_dict

    def check_asset_available(self, asset_symbol):
        try:
            self.markets[asset_symbol.upper()]
        except:
            return False
        return True
        
    def update_balances(self):
        get_balances = 'account/getbalances?'
        
        request_to_make = self.main_adress + get_balances + 'apikey=' + self.public_key + self.get_nounce()
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        parsed_json = json.loads(r.data)
                        
        for i in range(len(parsed_json['result'])):
            self.balances[parsed_json['result'][i]['Currency']] = [parsed_json['result'][i]['Balance'], 
                                                                   parsed_json['result'][i]['Available']]
        
    def limit_deal(self, deal_type, market, quantity, rate):
        limit = 'market/'
        
        request_to_make = self.main_adress  + limit + deal_type + 'limit?' + 'apikey=' + self.public_key + \
                          self.get_nounce() + '&market=' + market + '&quantity=' + str(quantity) + '&rate=' + str(rate) 
                
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        parsed_json = json.loads(r.data)
        return parsed_json
        
    def get_ticker(self, market):#, interval):
        get_ticker = 'https://bittrex.com/api/v1.1/public/getticker?market='
        
        request_to_make = get_ticker + market #+ '&tickInterval=' + interval
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make)
        
        parsed_json = json.loads(r.data)
        return parsed_json
    
    def get_ticks(self, market, interval):
        get_ticks = 'https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName='
        
        request_to_make = get_ticks + market + '&tickInterval=' + interval
        
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        parsed_json = json.loads(r.data)
        return parsed_json
          
    def swap_assets(self, order_type, action, pair, amount = -1, price = None):
    #amount allways only of secondary asset

    #Primary asset(base) is first in the pair. Ex: BTC-XRP, BTC is primary
    #buy  - q-ty of 2-ry asset to buy;      We have primary asset, wanna to get secondary
    #sell - q-ty of 2-ry asset to sell;     We have secondary asset, wanna to get primary
    #rate = 2ry price in $ / primry asset price in $.
        order_id = None
        possible_amount = None
    
        if action == 'buy':
            possible_amount = self.balances[pair.split('-')[0]][1]      #amount currently is in primary asset
        else:
            possible_amount = self.balances[pair.split('-')[1]][1]      #amount currently is in secondary (as we need to post in query) asset
        
        if amount == -1 or \
        (action == 'sell' and amount > possible_amount) or \
        (action == 'buy'  and order_type == 'limit' and amount > possible_amount / price):
            amount = possible_amount

        amount = amount - 0.003 * amount

        if order_type == 'limit':
            order_id = self.limit_deal(action, pair, str(amount), str(price))
            return order_id
        
        order_book = self.ws_orderbook_class.get_order_book(pair)
        
        total_amount = 0
        order_rate = 0
        order_id = None

        if action == 'buy':
            for order in order_book['S']:
                try:
                    order_rate = order['R']
                except:
                    order_rate = order['P']

                total_amount += order['Q'] * order_rate             # In example N ETH * 0.03 (0.03 BTC for one ETH) = actual amount of BTC in order, and buyin we spend primary asset 

                if total_amount >= amount:
                    break

        if action == 'sell':
            for order in order_book['Z']:
                try:
                    order_rate = order['R']
                except:
                    order_rate = order['P']
                total_amount += order['Q']

                if total_amount >= amount:
                    break
                    
        if action == 'buy':
            amount = amount/order_rate

        print('Amount: ', amount, 'Rate: ', order_rate)
        order_id = self.limit_deal(action, pair, str(amount), str(order_rate))   
        
        return order_id
        
    def get_asset_balance(self, asset_symbol):     
        try:
            current_balance = float(self.balances[asset_symbol.upper()][1]) # [1] for 'Available', [0] for absolute
        except KeyError:
            current_balance = 0
        return current_balance

    def get_traiding_pair(self, asset_symbol):
        return self.markets[asset_symbol.upper()][0][2]    #fix? [0] - BTC pair

    def get_current_price(self, pair):
        current_price = None

        try:
            current_price = self.ws_orderbook_class.get_order_book(pair)['f'][0]['R']
        except:
            current_price = self.ws_orderbook_class.get_order_book(pair)['f'][0]['P']
        return current_price

    def get_candles(self, pair, timestamp, candles_count):
        candles = self.get_ticks(pair, timestamp) # TODO 'oneMin')

        if candles['success'] != True:
            print ('Error::get_candles status:', candles)
            exit()                                          #TODO

        candles_amount = len(candles['result'])
        
        if(candles_count > candles_amount):
            candles_count = candles_amount

        asked_candles = candles['result'][-candles_count:]
        
        return asked_candles

    def get_candle_data(self, candle, data_type): #data type - close/open/high/low/time/volume
        
        if data_type == 'close':
            return candle['C']
        
        if data_type == 'open':
            return candle['O']
        
        if data_type == 'high':
            return candle['H']
        
        if data_type == 'low':
            return candle['L']
        
        if data_type == 'time':
            return candle['T']
        
        if data_type == 'volume':
            return candle['V']

    def get_completed_orders(self, pair):
        orders = []
        asset_order_book = self.ws_orderbook_class.get_order_book(pair)

        for ended_order in asset_order_book['f']:
            try:
                orders.append(ended_order['R'])
            except KeyError:
                orders.append(ended_order['P'])
                
        return orders 

    def get_order_details(self, order_info):
        order_uuid = order_info['result']['uuid']
        get_order = 'account/getorder?'
        
        request_to_make = self.main_adress + get_order + 'apikey=' + self.public_key + \
                          self.get_nounce() + '&uuid=' + order_uuid 
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        parsed_json = json.loads(r.data)
        return parsed_json

    def check_order_placement_success(self, order_info):
        return order_info['success']

    def get_order_price(self, order_details):
        return float(order_details['result']['PricePerUnit'])

    def check_order_open(self, order_details):
        return order_details['result']['IsOpen']

    def cancel_order(self, order_info):
        order_uuid = order_info['result']['uuid']

        cancel_order = 'https://bittrex.com/api/v2.0/key/market/TradeCancel?'# orderid=xxxx
        
        request_to_make = cancel_order + 'apikey=' + self.public_key +\
                          self.get_nounce() + '&orderid=' + order_uuid 
        
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('POST', request_to_make, headers = {'apisign': signature.hexdigest()})
    
        try:
            parsed_json = json.loads(r.data)
        except:
            print('Error! ', r.data)

        if parsed_json['success'] != True:
            print('Error cancelling order: ', parsed_json['message'])

        return parsed_json['success']

    def conditional_order(self, action, pair, quantity, price, condition, target):
#       MarketName=USDT-BTC&OrderType=LIMIT&Quantity=0.00050000&Rate=7500.00000000
#       &TimeInEffect=GOOD_TIL_CANCELLED&ConditionType=LESS_THAN&Target=7600
#       GREATER_THAN \ LESS_THAN
      
        if action == 'buy':
            conditional_order = 'https://bittrex.com/api/v2.0/key/market/TradeBuy?'
        
        if action == 'sell':
            conditional_order = 'https://bittrex.com/api/v2.0/key/market/TradeSell?'

        if quantity == -1:
            if action == 'buy':
                quantity = self.balances['BTC'][1]
            else:
                quantity = self.balances[pair.split('-')[1]][1]

        if action == 'buy':
            quantity_with_commision = quantity / price - 0.003 * quantity / price
            if quantity_with_commision > self.balances['BTC'][1]:
                quantity_with_commision = self.balances['BTC'][1] / price - 0.003 * self.balances['BTC'][1] / price
        else:
            quantity_with_commision = quantity - 0.003*quantity

        request_to_make = conditional_order + 'apikey=' + self.public_key + self.get_nounce() + '&MarketName=' +\
                          pair + '&OrderType=LIMIT&Quantity=' + str(quantity_with_commision) + '&Rate=' + str(price) +\
                          '&TimeInEffect=GOOD_TIL_CANCELLED&ConditionType=' + condition + '&Target=' + str(target)        
                
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('POST', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        try:
            parsed_json = json.loads(r.data)
        except:
            print('conditional_order fatal error: ', r.data)
            exit()
        return parsed_json