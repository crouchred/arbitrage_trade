import unittest

from utils.market import Bibox, Binance

class TestMarketBaseMixin():
        
    def setUp(self):
        raise NotImplementedError('')
        #self.client = SomeClass('EOS', 'BTC')

    def test_balance(self):
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
        order_id =  self.client.buy(low, 0.01)
        orders = self.client.list_order()
        self.assertTrue(order_id in orders)
        order_id =  self.client.cancel_order(order_id)
        self.assertFalse(order_id in orders)

    def test_sell(self):
        high = self.client.get_high_price()
        print("high price: %s"%(high))
        order_id =  self.client.sell(high, 0.01)
        orders = self.client.list_order()
        self.assertTrue(order_id in orders)
        order_id =  self.client.cancel_order(order_id)
        self.assertFalse(order_id in orders)

class TestBiboxUtil(unittest.TestCase, TestMarketBaseMixin):
        
    def setUp(self):
        self.client = Bibox('EOS', 'BTC')

if __name__=="__main__":
    unittest.main()
