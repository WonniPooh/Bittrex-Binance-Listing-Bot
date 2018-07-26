import websocket
import gzip
import time
import enum
import threading
from threading import Thread

class Candle_Time(enum.Enum):
    One_Min = 0
    Five_Min = 1
    Thirty_Min = 2
    Hour = 3
    Day = 4
    Mounth = 5
    Week = 6
    Year = 7
    

class Depth_Type(enum.Enum):
    First = 0
    Second = 1
    Third = 2
    Fourth = 3
    Fifth = 4
    Sixth = 5


class Huobi_WS_Type(enum.Enum):
    Kline = 0
    Depth = 1
    Trade = 2
    Detail = 3


class Huobi_WS(Thread):
    def __init__(self, pair, m_type, depth_type = 0, kline_period = 0):
        Thread.__init__(self)
        
        self.pair = pair
        self.served_type = m_type
        self.kline_period = kline_period
        self.depth_type = depth_type
        
        self.served_types = [self.get_kline_msg, self.get_depth_msg, self.get_trade_detail_msg, self.get_market_detail_msg]            
        self.subscribers = []
        self.data = ''
        
        self.beginning = '{\"sub" : \"market.'
        self.kline = '.kline.'
        self.kline_periods = ['1min\", ', '5min\", ', '15min\", ', '30min\", ', '60min\", ',\
                              '1day\", ', '1mon\", ', '1week\", ', '1year\", ']
        self.kline_id = '\"id\": \"id1'
        
        self.depth = '.depth.'
        self.depth_types = ['step0\", ', 'step1\", ', 'step2\", ', 'step3\", ', 'step4\", ', 'step5\", ']
        self.depth_id = '\"id\": \"id2'
        
        self.trade_detail = '.trade.detail\", '
        self.trade_id = '\"id\": \"id3'
        
        self.market_detail = '.detail\", '
        self.market_id = '\"id\": \"id4'

        self.formed_id = self.form_id()
        self.ws_initial_msg = self.served_types[m_type]()
        
    def get_kline_msg(self):

        return self.beginning + self.pair + self.kline + self.kline_periods[self.kline_period] + self.kline_id + str(self.formed_id) + '\"}'

    def get_depth_msg(self):

        return self.beginning + self.pair + self.depth + self.depth_types[self.depth_type] + self.depth_id + str(self.formed_id) + '\"}'

    def get_trade_detail_msg(self):

        return self.beginning + self.pair + self.trade_detail + self.trade_id + str(self.formed_id) + '\"}'

    def get_market_detail_msg(self):

        return self.beginning + self.pair + self.market_detail + self.market_id + str(self.formed_id) + '\"}'

    
    def form_id(self):
        result = ''
        for i in self.pair:
            result += str(ord(i) - ord('A'))
        return result

    def add_subscriber(self, subscriber):
        self.subscribers.append(subscriber)

    def delete_subscriber(self, subscriber):
        try:
            self.subscribers.remove(subscriber)
        except ValueError:
            print ("Huobi_WS::delete_subscriber::No such subscriber, cant remove!")

    def run(self):
        ws = self.connect_ws()
        ws.send(self.ws_initial_msg)

        while(1):
            try:
                compressData = ws.recv()
            except ConnectionResetError or TimeoutError:
                ws = connect_ws()
                ws.send(self.ws_initial_msg)

            self.data = gzip.decompress(compressData).decode('utf-8')

            if self.data[:7] == '{"ping"':
                ts = self.data[8:21]
                pong='{"pong":'+ts+'}'
                ws.send(pong)
            else:
                for subscriber in self.subscribers:
                    subscriber.set()

               # print(self.data, '\n\n')


    def connect_ws(self):
        iters = 10
        for i in range(iters):
            try:
                ws = websocket.create_connection("wss://api.huobi.pro/ws")
                break
            except ConnectionResetError:
                print('connect ws error,retry...')
                time.sleep(1)
                if i == iters - 1:
                    print ('Cannot reconnect!')
                    return None
        return ws