import unittest
import time

from market import Bibox, Binance

class TestMarketBaseMixin():
        
    def __init__(self):
        raise NotImplementedError('')
        #self.min_amount = 0
        #self.client = SomeClass('EOS', 'BTC', self.min_amount)

    def test_balance(self):
        balance = self.client.get_balance()
        print("balance: %s"%(balance))

    def test_balance_position(self):
        balance = self.client.get_balance_position()
        print("balance position: %s"%(balance))
        self.assertTrue(0<= balance <= 1)

    def test_depth(self):
        depth = self.client.get_depth()
        self.assertTrue(depth['buy_one']['price']>0)
        self.assertTrue(depth['sell_one']['price']>0)

    def test_average_price(self):
        average_price = self.client.get_average_price()
        print("average price: %s"%(average_price))
        self.assertTrue(average_price>0)

    def test_buy(self):

        low = self.client.get_low_price()
        print("low price: %s"%(low))
        orderid =  self.client.buy(low, self.min_amount, 'test', 'low', 0, 12345)
        time.sleep(0.5)
        orders = [o['orderid'] for o in self.client.get_open_orders()]
        self.assertTrue(orderid in orders)
        orderid =  self.client.cancel_order(orderid)
        self.assertFalse(orderid in orders)

    def test_sell(self):
        high = self.client.get_high_price()
        print("high price: %s"%(high))
        orderid =  self.client.sell(high, self.min_amount, 'test', 'low', 0)
        orders = [o['orderid'] for o in self.client.get_open_orders()]
        time.sleep(0.5)
        self.assertTrue(orderid in orders)
        orderid =  self.client.cancel_order(orderid)
        self.assertFalse(orderid in orders)

    def test_depth(self):
        depth = self.client.get_depth(min_amount=self.min_amount)
        self.assertTrue(depth['sell_one']['price']>depth['buy_one']['price'])
        self.assertTrue(depth['sell_one']['amount']>self.min_amount)
        self.assertTrue(depth['buy_one']['amount']>self.min_amount)

class TestBibox(unittest.TestCase, TestMarketBaseMixin):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.min_amount = 0.1
        self.client = Bibox('EOS', 'BTC')
        print("Here is bibox")

class TestBinance(unittest.TestCase, TestMarketBaseMixin):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.min_amount = 1
        self.client = Binance('EOS', 'BTC')
        print("Here is binance")

if __name__=="__main__":
    unittest.main()
