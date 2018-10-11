import math
import time
import threading
import urllib3
import urllib

import threading
from threading import Thread
from bs4 import BeautifulSoup
#from pyaudio import PyAudio

urllib3.disable_warnings()

class Binance_News(Thread):
    def __init__(self, handler, beep_enabled=True, delay_between_requests = 0.3):

        Thread.__init__(self)
        self.latest_event_url = ''
        self.thread_exit_time = False
        self.beep_enabled = beep_enabled
        self.event_handler = handler 
        self.binance_events_url = 'https://support.binance.com/hc/en-us/sections/115000106672-New-Listings'
        self.delay_between_requests = delay_between_requests

    def run(self):
        waited_event = ['Lists', 'Will List']
        not_waited = 'Trading Pair'
        http = urllib3.PoolManager()
        
        while self.thread_exit_time == False:
            
            try:
                r = http.request('GET', self.binance_events_url)
            except urllib3.exceptions.TimeoutError:
                print('Binance TimeoutError occured')
                continue

            try:
                soup_handler = BeautifulSoup(r.data, "lxml")
            except:
                continue
            
            listed_news = soup_handler.find_all('li', {"class": "article-list-item"})
            
            if len(listed_news) == 0:
                continue

            try:    
                current_top_url = listed_news[0].find('a').get('href')
            except:
                continue

            if(self.latest_event_url == ''):
                print ('Initializing with last event appeared...\n', current_top_url)
                self.latest_event_url = current_top_url

            if(self.latest_event_url != current_top_url):
                self.latest_event_url = current_top_url

                print('Founded smth new!')

                if (listed_news[0].text.find(waited_event[0]) != -1  or \
                    listed_news[0].text.find(waited_event[1]) != -1) and \
                    listed_news[0].text.find(not_waited)      == -1:

                    print('Fonded one we were waiting!!')

                    #if self.beep_enabled == True:
                        #t1 = Thread(target=self.beep_signal, args=())
                        #t1.start()

                    event_name = listed_news[0].text.strip()
                    self.new_event_founded(event_name)  
                else:
                    print('Not one that we are waiting for...((')

            time.sleep(self.delay_between_requests)


    def new_event_founded(self, event_full_name):
        listed_asset_symbol = event_full_name.split('(')[1].split(')')[0]
        print('Newly listed asset symbol :', listed_asset_symbol)
        self.event_handler.handle_event(listed_asset_symbol)

 #   def beep_signal(self):
        #See http://en.wikipedia.org/wiki/Bit_rate#Audio
 #       BITRATE = 16000 #number of frames per second/frameset.      

        #See http://www.phy.mtu.edu/~suits/notefreqs.html
 #       FREQUENCY = 3000.63 #Hz, waves per second, 261.63=C4-note.
 #       LENGTH = 2.5 #seconds to play sound

 #       NUMBEROFFRAMES = int(BITRATE * LENGTH)
 #       RESTFRAMES = NUMBEROFFRAMES % BITRATE
 #       WAVEDATA = ''    

 #       for x in range(NUMBEROFFRAMES):
 #          WAVEDATA += chr(int(math.sin(x / ((BITRATE / FREQUENCY) / math.pi)) * 127 + 128))    

        #fill remainder of frameset with silence
 #       for x in range(RESTFRAMES): 
 #           WAVEDATA += chr(128)

 #       p = PyAudio()
 #       stream = p.open(
 #           format=p.get_format_from_width(1),
 #           channels=1,
 #           rate=BITRATE,
 #           output=True,
 #           )
 #       stream.write(WAVEDATA)
 #       stream.stop_stream()
 #       stream.close()
 #       p.terminate()
