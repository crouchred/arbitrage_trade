from binance.client import Client

import hmac
import hashlib
import json, requests

from config import *


class Market:

    def __init__(self, product, basecoin):
        self.product = product.upper()
        self.basecoin = basecoin.upper()

    def get_balance_position(self):
        """product的仓位"""
        raise NotImplementedError('')

    def buy(self):
        raise NotImplementedError('')

    def sell(self):
        raise NotImplementedError('')

    def cancel_order(self):
        raise NotImplementedError('')

    def get_depth(self):
        raise NotImplementedError('')

    def get_average_price(self):
        raise NotImplementedError('')

    def list_order(self):
        raise NotImplementedError('')

    def clear_open_orders(self):
        raise NotImplementedError('')

class Binance(Market):
    def __init__(self, product, basecoin):
        super().__init__(product, basecoin)
        self.client = Client(binance_api_key, binance_secret_key, {'proxies': proxies})
        self.trade_pair = self.product + self.basecoin

    def list_order(self):
        pass

    def get_depth(self):
        depth = self.client.get_order_book(self.trade_pair)
        result = depth # todo 
        return result

class Bibox(Market):
    def __init__(self, product, basecoin):
        super().__init__(product, basecoin)
        self.trade_pair = self.product + "_" + self.basecoin
        self.uri = "https://api.bibox.com/v1"

    def __getSign(self, data,secret):
        result = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.md5).hexdigest()
        return result

    def __doApiRequestWithApikey(self, url, cmds):
        s_cmds = json.dumps(cmds)
        sign = self.__getSign(s_cmds, bibox_secret_key)
        r = requests.post(url, data={'cmds': s_cmds, 'apikey': bibox_api_key,'sign':sign}, \
                proxies=proxies)
        return json.loads(r.text)['result'][0]['result']

    def __post_order(self, order_side, price, amount, order_type=2):
        """
        order_side: //交易方向，1-买，2-卖
        order_type,     //交易类型，1-市价单，2-限价单
        """
        url = "https://api.bibox.com/v1/orderpending"
        cmds = [
            {
                'cmd':"orderpending/trade",
                'body':{
                    'pair': self.trade_pair,
                    'account_type': 0,
                    'order_type': order_type,
                    'order_side':order_side,
                    'pay_bix': 1,
                    'price': price,
                    'amount': amount,
                    'money': price*amount
                }
            }
        ]
        data = self.__doApiRequestWithApikey(url,cmds)
        return data

    def buy(self, price, amount):
        return self.__post_order(1, price, amount)

    def sell(self, price, amount):
        return self.__post_order(2, price, amount)

    def cancel_order(self, order_id):
        url = "https://api.bibox.com/v1/orderpending"
        cmds = [
                {
                    'cmd': 'orderpending/cancelTrade',
                    'body': {
                        'orders_id': order_id
                        }
                    }
                ]
        data =  self.__doApiRequestWithApikey(url,cmds)
        #return  todo

    def list_order(self):
        url = "https://api.bibox.com/v1/orderpending"
        cmds = [
                {
                    'cmd': 'orderpending/orderPendingList',
                    'body': {
                        '[pair]': [self.trade_pair],
                        '[account_type]': [0],
                        'page': 1,
                        'size': 100,
                        '[coin_symbol]': self.product,
                        '[currency_symbol]': self.basecoin,
                        '[order_side]': [1,2]
                        }
                    }
                ]
        data =  self.__doApiRequestWithApikey(url,cmds)
        return [i['id'] for i in data['items']]

    def get_balance_position(self):
        url = "https://api.bibox.com/v1/transfer"
        cmds = [
                {
                    'cmd': 'transfer/assets',
                    'body': {
                        'select': 1
                        }
                    }
                ]
        data =  self.__doApiRequestWithApikey(url,cmds)
    
        basecoin_balance = 0
        product_balance = 0 

        for asset in data['assets_list']:
            if asset['coin_symbol'] == self.basecoin:
                basecoin_balance = float(asset['CNYValue'])
            elif asset['coin_symbol'] == self.product:
                product_balance = float(asset['CNYValue'])

        return product_balance / (product_balance + basecoin_balance)

    def __get_week_prices(self):
        """过去一周的每小时close价格"""
        url = "https://api.bibox.com/v1/mdata?cmd=kline&pair={trade_pair}&period=1hour&size=168" \
                .format(trade_pair=self.trade_pair)
        r = requests.get(url, proxies=proxies)
        data = json.loads(r.text)
        closes = [float(i['close']) for i in data['result']]
        return closes

    def get_average_price(self):
        closes = self.__get_week_prices()
        return sum(closes) / len(closes)

    def get_high_price(self):
        closes = self.__get_week_prices()
        return max(closes)

    def get_low_price(self):
        closes = self.__get_week_prices()
        return min(closes)

    def get_depth(self):
        """ return 
        {'buy_one': {'price': '0.00013777', 'volume': '495.5544'},
         'sell_one': {'price': '0.00013911', 'volume': '2297.409'}}
        """
        url = "https://api.bibox.com/v1/mdata?cmd=depth&pair={trade_pair}&size=10"\
                .format(trade_pair=self.trade_pair)
        r = requests.get(url, proxies=proxies)
        data = json.loads(r.text)
        buy_one = data['result']['bids'][0]
        sell_one = data['result']['asks'][0]

        buy_one['price'] = float(buy_one['price'])
        buy_one['volume'] = float(buy_one['price'])
        sell_one['price'] = float(buy_one['price'])
        sell_one['volume'] = float(buy_one['price'])

        return {'buy_one': buy_one, 'sell_one': sell_one}

    def clear_open_orders(self):
        orders = self.list_order()
        print("orders before clear: %s"%(orders))
        for order in orders:
            self.cancel_order(order)
        print("orders after clear: %s"%(self.list_order()))

if __name__=="__main__":
    a = Bibox('EOS', 'BTC')
    a.clear_open_orders()

