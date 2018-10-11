class Market_Settings:
    def __init__(self, market_api, asset_buy_on, stop_loss_percent=0.055, stop_profit_percent=-1, amount_to_invest=-1, asset_to_swap=None, direct_purchase=True,
                return_initial_asset=False, price_growth_limit=0, price_drop_limit=0, amount_to_return=0, min_stop_perc_profit=0.095):
        
        self.market_api           = market_api
        self.asset_to_swap        = asset_to_swap
        self.asset_buy_on         = asset_buy_on
        self.return_initial_asset = return_initial_asset
                
        self.price_growth_limit = price_growth_limit
        self.price_drop_limit   = price_drop_limit
        
        self.direct_purchase  = direct_purchase
        self.amount_to_invest = amount_to_invest
        self.amount_to_return = amount_to_return            #whole balance = -1; N = N or less, depend on balance
        
        self.min_stop_perc_profit = min_stop_perc_profit
        self.stop_profit_percent  = stop_profit_percent
        self.stop_loss_percent    = stop_loss_percent



