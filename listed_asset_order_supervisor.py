import enum
import json

from Crypto_Asset import *
from Bittrex_API import *
#from Huobi_Ws import *

class Order_Type(enum.Enum):
    Market = 'market'
    Limit   = 'limit'

class Order_Action(enum.Enum):
    Buy = 'buy'   
    Sell = 'sell' 

class Listing_Order_Supervisor(Thread):
    def __init__(self, asset_working_with, markets_to_use): #, cmc_assets):
        Thread.__init__(self)

        self.lock = threading.Lock()
        self.market = markets_to_use[0]                 #TODO FIX for many markets in future!!!
        self.asset_working_with = asset_working_with
        #self.cmc_assets = cmc_assets                   #decide if it is needed
        
        self.time_used = 15
        self.max_candle_percent_size = 0.03
        self.median_price_chage = 1.05
        self.max_price_loss = 0.24
        self.event = threading.Event()
 
    def wait_until_price_update():       
        while self.market.market_api.balances_manager.price_updated == 0:
            time.sleep(0.01)
        self.market.market_api.balances_manager.price_updated = 0

    def run(self):
        start = time.time()                                                                                 #Clean after

        pair = self.market.market_api.get_traiding_pair(self.asset_working_with); 
        analysis_result = self.analyze_market_situation(pair)

        if analysis_result != True:
            print("Dont wanna buy now, we are too late actually :( ")
            return

        if self.market.direct_purchase == False:
            self.sell_initial_asset()

        self.wait_until_price_update()                                                                      #Move inside bittrex api?

        amount_to_invest = self.get_invest_amount()                                                         #TODO check it
        print('Buying listed asset, pair:', pair, 'invested amount:', amount_to_invest)
        invest_order = self.market.market_api.swap_assets('market', 'buy', pair, amount_to_invest)          #TODO buying asset
        
        end = time.time()                                                                                   #Clean after
        print("time elapsed: ", end - start)

        if self.market.market_api.check_order_placement_success(invest_order) != True:
            print ('invest_order placement failure: ', invest_order)
            exit()                                                                                          #TODO Error Hanling!!!

        self.handle_opened_order(invest_order, pair)
        
        #if self.market.return_initial_asset == True:  
        #    self.return_initial_asset()   
                 
    def sell_initial_asset(self):
        print ("Selling initial asset...")
        swap_asset_balance = 0
   
        swap_asset_balance = self.market.market_api.get_asset_balance(self.market.asset_to_swap) #by symbol!
        
        if swap_asset_balance == 0:
            print('Swap asset balance is empty!') #TODO handle Error!
            exit(0)

        print('Asset to swap balance:', swap_asset_balance)
        
        if swap_asset_balance < self.market.amount_to_invest or self.market.amount_to_invest == -1:
            amount_to_sell = swap_asset_balance
        else:
            amount_to_sell = self.market.amount_to_invest
  
        pair = self.market.market_api.get_traiding_pair(self.market.asset_to_swap); 
        print('Asset to swap pair:', pair)
        print ('Asset to swap selling amount:', amount_to_sell)                         #TODO get available precicion + min order value?
  
        swap_order = self.market.market_api.swap_assets('market', 'sell', pair, amount_to_sell)       
    
        if self.market.market_api.check_order_placement_success(swap_order) != True:      #THINK IF NEEDED TO SAVE TIME
            print ('invest_order placement failure: ', swap_order)
            exit()                                                                        #TODO Error Hanling!!!
        
        # order_details = self.market.market_api.get_order_details(swap_order)            #THINK IF NEEDED TO SAVE TIME

        # while self.market.market_api.check_order_open(order_details) == True:           #THINK IF NEEDED TO SAVE TIME
        #     order_details = self.market.market_api.get_order_details(swap_order)
        #     print('waiting sell initial asset order to close')
        #     time.sleep(0.1)

    def get_invest_amount(self):            #TODO replace market_api.balances[self.market.asset_buy_on][1]) on get_balance() call to API
        print('Checking balance...')
        if float(self.market.market_api.balances[self.market.asset_buy_on][1]) < self.market.amount_to_invest or self.market.amount_to_invest == -1:
            return float(self.market.market_api.balances[self.market.asset_buy_on][1])
        else:
            return self.market.amount_to_invest

    def return_initial_asset(self):
  
        #back_swap_order = None
        
        #asset_bought_on_balance = self.market.market_api.balances[self.market.asset_buy_on.upper()][1]
        #second_pair = self.market.asset_to_swap + self.market.asset_buy_on #TODO now its allways like naseth, but theoretically can be smth else and we have to modify pair name 

        #if self.market.amount_to_return == -1:
        time.sleep(10)
        back_swap_order = self.market.market_api.swap_btc_and_usdt('sell')
        print(back_swap_order)
        # else:
        #     returned_asset_current_price = get_ticker(second_pair)
            
        #     if returned_asset_current_price['status'] != 'ok':
        #         print ('Error::', returned_asset_current_price)
        #         return
        #         #TODO hanling ERRORRS!!

        #     returned_asset_current_price = returned_asset_current_price['tick']['data'][0]['price']
        #     amount_to_spend = self.market.amount_to_return * returned_asset_current_price
            
        #     if amount_to_spend > asset_bought_on_balance:
        #         back_swap_order = self.market.market_api.place_order(second_pair, asset_bought_on_balance, Order_Type.Buy_Market.value)
        #     else:
        #         back_swap_order = self.market.market_api.place_order(second_pair, amount_to_spend, Order_Type.Buy_Market.value)
          
##############################################################################################################################################

##############################################################################################################################################

    def handle_opened_order(self, invest_order, pair):

        invest_order_details = self.market.market_api.get_order_details(invest_order)
        invest_price = self.market.market_api.get_order_price(invest_order_details)

        self.wait_until_price_update()

        sell_order_info = self.market.market_api.swap_assets('limit', 'sell', pair, -1, invest_price * 1.13)    #TODO self.market.stop_profit_percent

        if self.market.market_api.check_order_placement_success(sell_order_info) != True:
            print ('sell order error!! Returned: ', sell_order_info)

        order_details = self.market.market_api.get_order_details(sell_order_info)

        while self.market.market_api.check_order_open(order_details) == True:
            order_details = self.market.market_api.get_order_details(sell_order_info)
            print('waiting order to close')
            time.sleep(5)

        # sell_opened_order_info = self.market.market_api.conditional_order(action='sell', pair, quantity=-1, price=invest_price*0.94, condition='LESS_THAN', invest_price*0.96)

        # if self.market.market_api.check_order_placement_success(sell_opened_order_info) != True:
        #     print('sell_opened_order failure:', sell_opened_order_info)
        #     exit()

        # order_details = self.market.market_api.get_order_details(sell_opened_order_info)
        # max_price = 0

        # while self.market.market_api.check_order_open(order_details) == True:
            
        #     currrent_price = self.market.market_api.get_ticker(pair, 'oneMin')['result'][0]['H']
            
        #     if max_price < current_price:
        #         if current_price - max_price > 0.01*invest_price:
        #             self.market.market_api.cancel_order(sell_opened_order_info)
        #             sell_opened_order_info = self.market.market_api.conditional_order(action='sell', pair, quantity=-1, price=invest_price*(0.95 + invest_price/current_price - 1), 
        #                                                                               condition='LESS_THAN', invest_price*(0.96 + invest_price/current_price - 1))

        #         max_price = current_price

        #     order_details = self.market.market_api.get_order_details(sell_opened_order_info)
        #     print('waiting order to close')
        #     time.sleep(0.5)
  
            # current_price = parsed_json['tick']['close']


            # if current_price > max_price:
            #     max_price = current_price

            # if parsed_json['tick']['high'] > max_price:
            #     max_price = parsed_json['tick']['high']

            # if current_price <= invest_price * (1 - self.market.stop_loss_percent) and current_price >= invest_price * (1 - self.market.stop_loss_percent - 0.02):
            #     print (self.market.market_api.place_order(symbol, amount_to_sell, Order_Type.Sell_Limit.value, current_price * 0.995))
            #     break

            # if current_price < max_price and current_price >= invest_price * (1 + self.market.min_stop_perc_profit):
                
            #     if max_price - current_price >= (max_price - invest_price) * self.max_price_loss:
            #         print (self.market.market_api.place_order(symbol, amount_to_sell, Order_Type.Sell_Limit.value, current_price * 0.99))
            #         break

            # if self.market.stop_profit_percent != -1:
            #     if current_price >= invest_price * (1 + self.market.stop_profit_percent):
            #         print (self.market.market_api.place_order(symbol, amount_to_sell, Order_Type.Sell_Limit.value, current_price * 0.99))
            #         break

            # print('current_price:', current_price, 'initial price:', invest_price, 'max_price:', max_price)

    def analyze_market_situation(self, pair):

        market_ok = True
        current_price = self.market.market_api.get_current_price(pair)
        sorted_order_prices = self.market.market_api.get_completed_orders(pair)
        sorted_order_prices.sort()

        median_price = sorted_order_prices[int(len(sorted_order_prices)/2)]
        max_price = sorted_order_prices[-1]
        min_price = sorted_order_prices[0]

        if max_price - min_price > median_price * 0.07:
            market_ok = market_ok and False
            print("max_price - min_price > median_price * 0.07 : ", max_price - min_price, median_price * 0.07)
            
        if current_price > median_price * 1.035:
            market_ok = market_ok and False
            
        print('Desision:', market_ok, '\nMedian price:', median_price, '\n Current price:', current_price, '\n Max price what is ok is', median_price * 1.035)

        return market_ok

    # def round_amount_to_sell(self, asset, amount):
    #     asset_dollar_price = float(asset.price) 

    #     multiplyer = 10
    #     counter = 1
    #     new_amount = 0

    #     print ('Amount before rounding:', amount)

    #     while 1:
    #         if asset_dollar_price / multiplyer < 0.1:
    #             print('Precision:', counter - 1, 'Asset $ price:', asset_dollar_price)
    #             new_amount = self.round_down(float(amount), counter - 1)
    #             break 
    #         else:
    #             multiplyer = multiplyer * 10
    #             counter += 1

    #     print ('Rounded amount:', new_amount)

    #     return new_amount

    # def round_down(self, num, prec):
    #     if isinstance(num, float):
    #         s = str(num)
    #         return float(s[:s.find('.') + prec + 1])
    #     else:
    #         raise ValueError