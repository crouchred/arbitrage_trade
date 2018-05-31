import time
from strategy import Strategy
from market import Binance, Bibox
from utils.logger import Logger
logger = Logger.get_logger("app")

class Client:

    def run(self):
        logger.info("start running")
        i = 0 
        while True:
            if i % 100 == 0:
                self.refresh_redis()
                logger.info("%s times to run"%(i))
            self.run_strategy()
            time.sleep(5)
            i += 1

    def refresh_redis(self):
        """刷新redis中的仓位等信息"""
        pass

    def run_strategy(self):
        binance = Binance('EOS', 'BTC')
        bibox = Bibox('EOS', 'BTC')
        s = Strategy(m1=binance, m2=bibox)
        s.allocate_strategy()

if __name__=="__main__":
    client = Client()
    #client.run_strategy()
    client.run()
