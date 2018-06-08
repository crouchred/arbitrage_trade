import time
from strategy import Strategy
from market import Binance, Bibox

from utils.logger import Logger
logger = Logger.get_logger("app")
import traceback
import schedule
from cronjob import record_balance, auto_close_out

class Client:

    def run(self):

        schedule.every(5).seconds.do(self.run_strategy)
        schedule.every().day.at("06:55").do(record_balance)
        schedule.every().day.at("05:55").do(auto_close_out)

        while True:
            schedule.run_pending()
            time.sleep(1)

    def run_strategy(self):
        binance = Binance('EOS', 'BTC')
        bibox = Bibox('EOS', 'BTC')
        s = Strategy(m1=binance, m2=bibox)
        s.allocate_strategy()

if __name__=="__main__":
    client = Client()
    #client.run_strategy()
    client.run()
