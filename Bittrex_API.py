import time
import hmac
import urllib3.request
import json
import hashlib

class Bittrex_Api:
    def __init__(self):
        self.main_adress = 'https://bittrex.com/api/v1.1/'
        
        self.private_key = '17f88028747144948b216d6c5e2f1a9c'
        self.public_key = 'b5f96df3b6d6409c903c0c9a300b1cc1'
        self.ticks_perionds = ['oneMin', 'fiveMin', 'thirtyMin', 'Hour', 'Day']
        
        self.balances = {}
        self.markets = {}
        
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
        self.update_markets()
        try:
            self.markets[asset_symbol]
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
    
    def get_order(self, order_uuid):
        get_order = 'account/getorder?'
        
        request_to_make = self.main_adress + get_order + 'apikey=' + self.public_key + \
                          self.get_nounce() + '&uuid=' + order_uuid 
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        parsed_json = json.loads(r.data)
        return parsed_json
    
    def limit_deal(self, deal_type, market, quantity, rate):
        limit = 'market/'
        
        request_to_make = self.main_adress  + limit + deal_type + 'limit?' + 'apikey=' + self.public_key + \
                          self.get_nounce() + '&market=' + market + '&quantity=' + str(quantity) + '&rate=' + str(rate) 
                
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        parsed_json = json.loads(r.data)
        return parsed_json
    
    def get_order_book(self, market, deal_type = 'both'):
        get_order_book = 'public/getorderbook?'
        
        request_to_make = self.main_adress  + get_order_book + 'apikey=' + self.public_key + \
                          self.get_nounce() + '&market=' + market + '&type=' + deal_type
        
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
        parsed_json = json.loads(r.data)
        return parsed_json
    
    def get_ticker(self, market):
        get_ticker = 'public/getticker?'
        
        request_to_make = self.main_adress  + get_ticker + 'apikey=' + self.public_key + \
                          self.get_nounce() + '&market=' + market
        
        signature = hmac.new(self.private_key.encode(), request_to_make.encode(), hashlib.sha512)
        
        http = urllib3.PoolManager()
        r = http.request('GET', request_to_make, headers = {'apisign': signature.hexdigest()})
        
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
          
    def swap_btc_and_usdt(self, action, amount=-1):
        #action == buy btc(amount usdt to spend) \ sell btc(amount btc to spend)

        self.update_balances()

        if amount == -1:
            if action == 'sell':
                amount = self.balances['BTC'][1]
            else:
                amount = self.balances['USDT'][1] #[0] for balance, 1 for available

        
        if action == 'buy':
            order_book = self.get_order_book(market = 'USDT-BTC', deal_type = 'sell')
        else:
            order_book = self.get_order_book(market = 'USDT-BTC', deal_type = 'buy')
        
        total_amount = 0
        order_rate = 0
        order_id = None

        for i in range(len(order_book['result'])):
            
            if action == 'buy':
                total_amount += order_book['result'][i]['Quantity'] * order_book['result'][i]['Rate']
                order_rate = order_book['result'][i]['Rate']
                if total_amount > amount:
                    break

            if action == 'sell':
                total_amount += order_book['result'][i]['Quantity']
                order_rate = order_book['result'][i]['Rate']
                if total_amount > amount:
                    break

        if action == 'buy':
            order_id = self.limit_deal('buy', 'USDT-BTC', str(amount/order_rate - 0.003 * amount/order_rate), str(order_rate))
        else:
            order_id = self.limit_deal('sell', 'USDT-BTC', str(amount), str(order_rate))
        
        return order_id
    
    def swap_btc_asset(self, order_type, action, pair, price = None, amount = -1):
        #buy - spend btc to buy asset == buy n asset using x btc
        #sell - sell asset, easy one
        order_id = None
        
        self.update_balances()

        if amount == -1:
            if action == 'buy':
                amount = self.balances['BTC'][1]
            else:
                amount = self.balances[pair.split('-')[1]][1]
        
        if order_type == 'limit':

            if action == 'buy':
                amount_to_buy = amount / price - 0.003 * amount / price
                if amount_to_buy > self.balances['BTC'][1]:
                    amount_to_buy = self.balances['BTC'][1] / price - 0.003 * self.balances['BTC'][1] / price
                order_id = self.limit_deal('buy', pair, amount_to_buy, price)
            else:
                order_id = self.limit_deal('sell', pair, amount - 0.003*amount, price)

            return order_id
        
        if action == 'buy':
            order_book = self.get_order_book(market = pair, deal_type = 'sell')
        else:
            order_book = self.get_order_book(market = pair, deal_type = 'buy')
        
        total_amount = 0
        order_rate = 0
        order_id = None

        for i in range(len(order_book['result'])):
            
            if action == 'buy':
                total_amount += order_book['result'][i]['Quantity'] * order_book['result'][i]['Rate']
                order_rate = order_book['result'][i]['Rate']
                if total_amount > amount:
                    break

            if action == 'sell':
                total_amount += order_book['result'][i]['Quantity']
                order_rate = order_book['result'][i]['Rate']
                if total_amount > amount:
                    break

        print(amount/order_rate, amount, order_rate)
                    
        if action == 'buy':
            order_id = self.limit_deal('buy', pair, str(amount/order_rate - 0.003 * amount/order_rate), str(order_rate))
        else:
            order_id = self.limit_deal('sell', pair, str(amount- 0.003 * amount), str(order_rate))
        
        return order_id
        