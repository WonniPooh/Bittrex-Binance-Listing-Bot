import json
from bittrex_websocket.websocket_client import BittrexSocket

class Bittrex_Balance_Manager(BittrexSocket):
    def __init__(self, current_balances):
        BittrexSocket.__init__(self)
        
        self.current_balances = current_balances
        self.updates_nounce = 0
        self.price_updated = 0
        
    def on_private(self, msg):
        try:
            if msg['N'] <= self.updates_nounce:
                return

            # "d" = "Delta", "c" = "Currency" "b" = "Balance" "a" = "Available"
            try:
                currency_balance_changed = msg['d']['c']
                self.current_balances[currency_balance_changed][0] = msg['d']['b']
                self.current_balances[currency_balance_changed][1] = msg['d']['a'] 
                self.price_updated = 1
                print(currency_balance_changed, "balance updated")
            except:
                print('Not balance-change message: ', msg)
        
        except Exception as e:
            print(e)