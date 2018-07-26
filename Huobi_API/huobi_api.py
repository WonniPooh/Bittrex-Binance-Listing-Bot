import base64
import datetime
import hashlib
import hmac
import json
import urllib3
import urllib

try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse

import urllib3.request
import requests

urllib3.disable_warnings()

MARKET_URL = "https://api.huobi.pro"

class Huobi_API: 
    def __init__(self, access_key, secret_key):
        
        self.name = 'Huobi'
        self.huobi_url = "https://api.huobi.pro"
        self.order_types = ['buy-market', 'sell-market', 'buy-limit', 'sell-limit']

        self.access_key = access_key
        self.secret_key = secret_key
        
        accounts = self.get_accounts()
        
        self.acc_id = None
        self.placed_orders = []
        
        if accounts['status'] == 'ok':
            self.acc_id = accounts['data'][0]['id']
        else:
            print ('Cannnot get account id!')
            #TODO handle error!

        self.balances = self.get_balance()
        
 
    def update_balances(self):
        self.balances = self.get_balance()

    def get_accounts(self):
        path = "/v1/account/accounts"
        params = {}
        return self.api_key_get(params, path)
        
    def get_balance(self):
        url = "/v1/account/accounts/{0}/balance".format(self.acc_id)
        params = {"account-id": self.acc_id}
        balances = self.api_key_get(params, url)

        parsed_asset_balances = {}

        if balances['status'] != 'ok':
            return
        
        for asset_balance in balances['data']['list']:
            if asset_balance['type'] == 'trade':
                parsed_asset_balances[asset_balance['currency']] = asset_balance['balance'] 
        return parsed_asset_balances

    def place_order(self, symbol, amount, type, price=0, source = 'api'):
        """
        :param amount: 
        :param source: 'api'
        :param symbol: 
        :param _type: {buy-market, sell-market, buy-limit, sell-limit}
        :param price: 
        :return: 
        """

        params = {"account-id": self.acc_id,
                  "amount": amount,
                  "symbol": symbol,
                  "type": self.order_types[type],
                  "source": source}
        if price:
            params["price"] = price

        url = '/v1/order/orders/place'
        order_result = self.api_key_post(params, url)
        
        self.placed_orders.insert(0, order_result)
        return order_result

    def cancel_order(self, order_id):
        params = {}
        url = "/v1/order/orders/{0}/submitcancel".format(order_id)
        return self.api_key_post(params, url)

    def order_info(self, order_id):
        params = {}
        url = "/v1/order/orders/{0}".format(order_id)
        return self.api_key_get(params, url)

    def completed_order_info(self, order_id):
        params = {}
        url = "/v1/order/orders/{0}/matchresults".format(order_id)
        return self.api_key_get(params, url)

    def api_key_get(self, params, request_path):
        method = 'GET'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') #'Timestamp': '2017-06-02T06:13:49'
        params.update({'AccessKeyId': self.access_key,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})

        host_name = urlparse(self.huobi_url).hostname
        host_name = host_name.lower()
        params['Signature'] = self.createSign(params, method, host_name, request_path)

        url = self.huobi_url + request_path
        return http_get_request(url, params)

    def api_key_post(self, params, request_path):
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {'AccessKeyId': self.access_key,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': timestamp}

        host_name = urlparse(self.huobi_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = self.createSign(params_to_sign, method, host_name, request_path)
        url = self.huobi_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return http_post_request(url, params)

    def createSign(self, pParams, method, host_url, request_path):
        sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding='UTF8')
        local_secret_key = self.secret_key.encode(encoding='UTF8')

        digest = hmac.new(local_secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

##########################################################################################################

#                                           Extern class api

##########################################################################################################

def get_trade(symbol):
    params = {'symbol': symbol}

    url = MARKET_URL + '/market/trade'
    return http_get_request(url, params)

def get_ticker(symbol):
    params = {'symbol': symbol}

    url = MARKET_URL + '/market/detail/merged'
    return http_get_request(url, params)

def get_detail(symbol):
    params = {'symbol': symbol}

    url = huobi_url + '/market/detail'
    return http_get_request(url, params)

def get_depth(symbol, m_type):
    """
    :param symbol
    :param type: {step0, step1, step2, step3, step4, step5 - precicion of price, 0 -not rounded, 1 - 5 dgts, etc }
    :return:
    """
    params = {'symbol': symbol,
              'type': m_type}

    url = MARKET_URL + '/market/depth'
    return http_get_request(url, params)

def get_kline(symbol, period, size=150):
    """
    :param symbol: naseth - str
    :param period: {1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year } - str
    :param size: [1,2000]
    :return: https://github.com/huobiapi/API_Docs_en/wiki/REST_Reference
    """
    periods = ['1min', '5min', '15min', '30min', '60min', '1day', '1mon', '1week', '1year']

    params = {'symbol': symbol,
              'period': periods[period],
              'size': size}

    url = MARKET_URL + '/market/history/kline'
    return http_get_request(url, params)

def http_get_request(url, params, add_to_headers=None):
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    }
    if add_to_headers:
        headers.update(add_to_headers)
    
    postdata = urllib.parse.urlencode(params)
    response = requests.get(url, postdata, headers=headers, timeout=5) 
    
    try:
        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        print("httpGet failed, detail is:%s,%s" %(response.text, e))
        return


def http_post_request(url, params, add_to_headers=None):
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    response = requests.post(url, postdata, headers=headers, timeout=10)
    try:

        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        print("httpPost failed, detail is:%s,%s" %(response.text,e))
        return




#############################################################################################

#                                   UNUSED:

#############################################################################################

# def orders_list(self, symbol, states, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
#     """
#     :param states:  {pre-submitted, submitted, partial-filled, partial-canceled, filled, canceled}
#     :param types: {buy-market, sell-market, buy-limit, sell-limit}
#     :param direct: {prev，next }
#     """
#     params = {'symbol': symbol,
#               'states': states}

#     if types:
#         params[types] = types
#     if start_date:
#         params['start-date'] = start_date
#     if end_date:
#         params['end-date'] = end_date
#     if _from:
#         params['from'] = _from
#     if direct:
#         params['direct'] = direct
#     if size:
#         params['size'] = size
#     url = '/v1/order/orders'
#     return api_key_get(params, url)

# def orders_matchresults(self, symbol, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
#     """
#     :param types: {buy-market, sell-market, buy-limit, sell-limit}
#     :param direct: {prev，next}
#     """
#     params = {'symbol': symbol}

#     if types:
#         params[types] = types
#     if start_date:
#         params['start-date'] = start_date
#     if end_date:
#         params['end-date'] = end_date
#     if _from:
#         params['from'] = _from
#     if direct:
#         params['direct'] = direct
#     if size:
#         params['size'] = size
#     url = '/v1/order/matchresults'
#     return api_key_get(params, url)



# def withdraw(address, amount, currency, fee=0, addr_tag=""):
#     """
#     :param address_id: 
#     :param amount: 
#     :param currency:btc, ltc, bcc, eth, etc ...(Pro)
#     :param fee: 
#     :param addr-tag:
#     :return: {"status": "ok", "data": 700}
#     """
#     params = {'address': address,
#               'amount': amount,
#               "currency": currency,
#               "fee": fee,
#               "addr-tag": addr_tag}
#     url = '/v1/dw/withdraw/api/create'

#     return api_key_post(params, url)

# def cancel_withdraw(address_id):
#     """
#     :param address_id: 
#     :return: {
#               "status": "ok",
#               "data": 700
#             }
#     """
#     params = {}
#     url = '/v1/dw/withdraw-virtual/{0}/cancel'.format(address_id)

#     return api_key_post(params, url)