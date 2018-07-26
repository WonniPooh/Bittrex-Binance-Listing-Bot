import enum
import json
from Crypto_Asset import *
from huobi_api import *
from Huobi_Ws import *

class Order_Type(enum.Enum):
    Market = 'market'
    Limit   = 'limit'

class Order_Action(enum.Enum):
    Buy = 'buy'   
    Sell = 'sell' 

class Listing_Order_Supervisor(Thread):
    def __init__(self, cmc_assets, asset_working_with, markets_to_use):
        Thread.__init__(self)

        self.lock = threading.Lock()
        self.market = markets_to_use[0]                 #TODO FIX for many markets in future!!!
        self.asset_working_with = asset_working_with
        self.cmc_assets = cmc_assets
        
        self.time_used = 15
        self.max_candle_percent_size = 0.05
        self.median_price_chage = 1.07
        self.max_price_loss = 0.24
        self.event = threading.Event()
        
        self.ws_class = None

    def run(self):

        amount_to_invest = 0
        invest_order = None

        if self.market.direct_purchase == False:
            amount_to_invest = self.sell_initial_asset()
        else:
            amount_to_invest = self.check_if_balance_is_enough()

        pair = self.asset_working_with.symbol.lower() + self.market.asset_buy_on #TODO same as above

        self.ws_class = Huobi_WS(pair, Huobi_WS_Type.Kline.value)
        self.ws_class.setDaemon(True)
        self.ws_class.start()

        print ('Buying listed asset, pair:', pair, 'invested amount:', amount_to_invest)

        analysis_result = self.analyze_market_situation(pair)
        print('Listing_Order_Supervisor::analysis_result:', analysis_result)

        if analysis_result == True:
            invest_order = self.market.market_api.place_order(pair, amount_to_invest, Order_Type.Buy_Market.value)

            if invest_order['status'] != 'ok':
                print (invest_order)
                #TODO Error Hanling!!!
            else:
                self.handle_opened_order(invest_order, pair)
                self.market.market_api.update_balances()  

            if self.market.return_initial_tokens == True:         
                return_initial_asset()   
        else:
            print("Dont wanna buy now, we are too late actually :( ")

    def sell_initial_asset(self):
        print ("Selling initial asset...")
        swap_asset_balance = 0
        
        try:
            swap_asset_balance = float(self.market.market_api.balances[self.market.asset_to_swap])
        except KeyError:
            print('Swap asset balance is empty. ')
            
        print('Balance:', swap_asset_balance)
        sell_amount = 0 
        
        if swap_asset_balance == 0:
            exit(0)

        if swap_asset_balance < self.market.amount_to_invest or self.market.amount_to_invest == -1:
            sell_amount = swap_asset_balance
        else:
            sell_amount = self.market.amount_to_invest

        cmc_asset_struct = self.cmc_assets.find_asset(self.market.asset_to_swap)
        print('Asset to sell cmc :', cmc_asset_struct.name)

        sell_amount = self.round_amount_to_sell(cmc_asset_struct, sell_amount)

        print ('Selling amount:', sell_amount)
    
        #pair = self.market.asset_to_swap + self.market.asset_buy_on     #TODO now its allways like naseth, but theoretically can be smth else and we have to modify pair name
        self.market.market_api.update_markets()
        pair = self.market.market_api.markets[self.market.asset_to_swap.upper()][0][2]

        print('Sending initital asset, pair:', pair)
        swap_order = self.market.market_api.place_order(pair, sell_amount, Order_Type.Sell_Market.value)
    
        self.market.market_api.update_balances()

        if swap_order['status'] != 'ok':
            print(swap_order)
            #TODO Error Hanling!!!!

        order_results = self.market.market_api.completed_order_info(swap_order['data'])            
        amount_to_invest = float(order_results['data'][0]['filled-amount']) * float(order_results['data'][0]['price']) 

        cmc_asset_struct = self.cmc_assets.find_asset(self.market.asset_buy_on)
        amount_to_invest = self.round_amount_to_sell(cmc_asset_struct, amount_to_invest)

        return amount_to_invest


    def check_if_balance_is_enough(self):
        print('Checking balance...')
        if float(self.market.market_api.balances[self.market.asset_buy_on]) < self.market.amount_to_invest or self.market.amount_to_invest == -1:
            return float(self.market.market_api.balances[self.market.asset_buy_on])
        else:
            return self.market.amount_to_invest

    def return_initial_asset(self):
  
        back_swap_order = None
        
        asset_bought_on_balance = self.market.market_api.balances[self.market.asset_buy_on]
        second_pair = self.market.asset_to_swap + self.market.asset_buy_on #TODO now its allways like naseth, but theoretically can be smth else and we have to modify pair name
            
        if self.market.amount_to_return == -1:
            back_swap_order = self.market.market_api.place_order(second_pair, asset_bought_on_balance, Order_Type.Buy_Market.value)
        else:
            returned_asset_current_price = get_ticker(second_pair)
            
            if returned_asset_current_price['status'] != 'ok':
                print ('Error::', returned_asset_current_price)
                return
                #TODO hanling ERRORRS!!

            returned_asset_current_price = returned_asset_current_price['tick']['data'][0]['price']
            amount_to_spend = self.market.amount_to_return * returned_asset_current_price
            
            if amount_to_spend > asset_bought_on_balance:
                back_swap_order = self.market.market_api.place_order(second_pair, asset_bought_on_balance, Order_Type.Buy_Market.value)
            else:
                back_swap_order = self.market.market_api.place_order(second_pair, amount_to_spend, Order_Type.Buy_Market.value)


    def analyze_market_situation(self, symbol):
        
        market_ok = False

        current_price = get_trade(symbol)
        if current_price['status'] != 'ok':
            print ('Error::cant get current price:', current_price)
            #TODO hanling ERRORRS!!

        current_price = current_price['tick']['data'][0]['price']

        minute_candles = get_kline(symbol, Candle_Time.One_Min.value)

        if minute_candles['status'] != 'ok':
            print ('Error::analyze_market_situation::minute_candles status:', minute_candles)
            #TODO fix it somehow???

        candles = minute_candles['data']

        biggest_candle = self.find_biggest_candle(candles)
        
        if biggest_candle[1] < self.max_candle_percent_size * current_price:
            market_ok = True
        else:
            market_ok = False
        
        print ('Candles observation result:', market_ok, '\n Max candle:', biggest_candle[1], '\n 5prc of current price:', self.max_candle_percent_size * current_price)

        median_price = self.find_median_price(candles)

        if current_price < median_price * self.median_price_chage:
            market_ok = market_ok and True
        else:
            market_ok = market_ok and False

        print('Desision:', market_ok, '\nMedian price:', median_price, '\n Current price:', current_price, '\n Max price what is ok is', median_price * self.median_price_chage)

        return market_ok
        

    def find_median_price(self, candles):
        list_search_in = []
        
        for i in range(self.time_used):
            list_search_in.insert(0, candles[i]['close'])
        
        list_search_in.sort()

        print('Listing_Order_Supervisor::find_median_price :', list_search_in[int(self.time_used / 2)])

        return list_search_in[int(self.time_used / 2)]


    def find_biggest_candle(self, candles):
        
        winner = float(candles[0]['close'] - candles[0]['open'])
        winner_index = 0
        
        for i in range(self.time_used):
            if float(candles[i]['close'] - candles[i]['open']) >= winner:
                winner_index = i 
                winner = float(candles[i]['close'] - candles[i]['open'])

        print('Listing_Order_Supervisor::find_biggest_candle :', candles[winner_index])

        return (winner_index, winner)
            
        
    def handle_opened_order(self, invest_order, symbol):

        invest_order_info = self.market.market_api.completed_order_info(invest_order['data'])
        #check? 

        #  File "/usr/lib64/python3.6/threading.py", line 916, in _bootstrap_inner
        #     self.run()
        #   File "/home/aserbin/Code/List_bot/listed_asset_order_supervisor.py", line 62, in run
        #     self.handle_openswap_asset_balanceed_order(invest_order, pair)
        #   File "/home/aserbin/Code/List_bot/listed_asset_order_supervisor.py", line 200, in handle_opened_order
        #     invest_price = float(invest_order_info['data'][0]['price'])
        # TypeError: 'NoneType' object is not subscriptable



        invest_price = float(invest_order_info['data'][0]['price'])

        max_price = 0

        amount_to_sell = float(invest_order_info['data'][0]['filled-amount'])

        amount_to_sell =  self.round_amount_to_sell(self.asset_working_with, amount_to_sell)

        if amount_to_sell == 0:
            return

        print('I will sell this amount of asset:', amount_to_sell)

        self.ws_class.add_subscriber(self.event)

        while True:

            self.event.clear()
            self.event.wait()
           
            parsed_json = json.loads(self.ws_class.data)
                    
            current_price = parsed_json['tick']['close']


            if current_price > max_price:
                max_price = current_price

            if parsed_json['tick']['high'] > max_price:
                max_price = parsed_json['tick']['high']

            if current_price <= invest_price * (1 - self.market.stop_loss_percent) and current_price >= invest_price * (1 - self.market.stop_loss_percent - 0.02):
                print (self.market.market_api.place_order(symbol, amount_to_sell, Order_Type.Sell_Limit.value, current_price * 0.995))
                break

            if current_price < max_price and current_price >= invest_price * (1 + self.market.min_stop_perc_profit):
                
                if max_price - current_price >= (max_price - invest_price) * self.max_price_loss:
                    print (self.market.market_api.place_order(symbol, amount_to_sell, Order_Type.Sell_Limit.value, current_price * 0.99))
                    break

            if self.market.stop_profit_percent != -1:
                if current_price >= invest_price * (1 + self.market.stop_profit_percent):
                    print (self.market.market_api.place_order(symbol, amount_to_sell, Order_Type.Sell_Limit.value, current_price * 0.99))
                    break

            print('current_price:', current_price, 'initial price:', invest_price, 'max_price:', max_price)

        self.ws_class.delete_subscriber(self.event)


    def round_amount_to_sell(self, asset, amount):
        asset_dollar_price = float(asset.price) 

        multiplyer = 10
        counter = 1
        new_amount = 0

        print ('Amount before rounding:', amount)

        while 1:
            if asset_dollar_price / multiplyer < 0.1:
                print('Precision:', counter - 1, 'Asset $ price:', asset_dollar_price)
                new_amount = round_down(float(amount), counter - 1)
                break 
            else:
                multiplyer = multiplyer * 10
                counter += 1

        print ('Rounded amount:', new_amount)

        return new_amount

def round_down(num, prec):
    if isinstance(num, float):
        s = str(num)
        return float(s[:s.find('.') + prec + 1])
    else:
        raise ValueError