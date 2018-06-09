from binance.client import Client

import hmac
import hashlib
import json, requests
import traceback

from config import *
from utils.logger import Logger
logger = Logger.get_logger("market")

from db import Mysql, Trade
db = Mysql()

import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
ex=10

def market_factory(name):
    if name.lower() == 'binance':
        return Binance
    elif name.lower() == 'bibox':
        return Bibox

class Market:

    def __init__(self, product, basecoin):
        self.product = product.upper()
        self.basecoin = basecoin.upper()
        self.feecoin = ""

    @property
    def market_name(self):
        return self.__class__.__name__

    @property
    def standard_pair(self):
        return self.product + "_" + self.basecoin

    def get_profit_ratio(self, side='BUY'):
        """根据仓位确定需要的盈利率系数"""
        balance_position = self.get_balance_position()
        if side == 'SELL':
            balance_position = 1 - balance_position
        if 0 <= balance_position <= 0.1:
            ratio = 1
        elif 0.1 < balance_position <= 0.9:
            ratio = 1.2
        elif 0.9 < balance_position:
            ratio = 5
        return ratio

    def get_fee(self):
        raise NotImplementedError('')
    
    def get_balance_position(self):
        """product的仓位"""
        raise NotImplementedError('')

    def buy_check(self, price, amount):
        basecoin_amount = self.get_balance()['basecoin']
        return basecoin_amount > price * amount

    def sell_check(self, price, amount):
        product_amount = self.get_balance()['product']
        return product_amount > amount

    def buy(self, price, amount, plan, level, is_hedge, orderid=None):
        if level == 'low':
            return 
        trade = Trade(orderid=orderid, market=self.market_name, side='BUY', \
                pair=self.standard_pair, plan=plan, level=level, is_hedge=is_hedge, \
                price=price, amount=amount)
        db.upsert_trade(trade)

    def sell(self, price, amount, plan, level, is_hedge, orderid=None):
        if level == 'low':
            return 
        trade = Trade(orderid=orderid, market=self.market_name, side='SELL', \
                pair=self.standard_pair, plan=plan, level=level, is_hedge=is_hedge, \
                price=price, amount=amount)
        db.upsert_trade(trade)

    def cancel_order(self, orderid):
        trade = Trade(orderid=orderid, deal_amount=0)
        db.upsert_trade(trade, columns_change =['deal_amount'])

    def get_depth(self):
        """ return 
        {'buy_one': {'price': '0.00013777', 'volume': '495.5544'},
         'sell_one': {'price': '0.00013911', 'volume': '2297.409'}}
        """
        raise NotImplementedError('')

    def get_open_orders(self):
        raise NotImplementedError('')

    def clear_open_orders(self):
        raise NotImplementedError('')

    def _get_week_prices(self):
        raise NotImplementedError('')

    def get_order_detail(self):
        raise NotImplementedError('')

    def get_average_price(self):
        closes = self._get_week_prices()
        return sum(closes) / len(closes)

    def get_high_price(self):
        closes = self._get_week_prices()
        return max(closes)

    def get_low_price(self):
        closes = self._get_week_prices()
        return min(closes)


    def clear_open_orders(self):
        orders = [o['orderid'] for o in self.get_open_orders()]
        logger.info("orders before clear: %s"%(orders))
        for order in orders:
            self.cancel_order(order)

        orders = [o['orderid'] for o in self.get_open_orders()]
        logger.info("orders after clear: %s"%(orders))
        return 0 

class Binance(Market):
    def __init__(self, product="", basecoin=""):
        super().__init__(product, basecoin)
        self.client = Client(binance_api_key, binance_secret_key, {'proxies': proxies})
        self.trade_pair = self.product + self.basecoin
        self.feecoin = "BNB"

    def get_fee(self):
        return 0.0005

    def get_order_detail(self, orderid):
        order = self.client.get_order(
            symbol=self.trade_pair,
            orderId=orderid)
        return {'orderid': float(orderid),
                'side': order['side'],
                'price': float(order['price']),
                'time': order['time'],
                'amount': float(order['origQty']),
                'deal_amount': float(order['executedQty'])
                }

    def get_balance_all(self, coins):
        result = []
        for coin in coins:
            tmp = self.client.get_asset_balance(asset=coin)
            if tmp is not None:
                result.append({'market':'binance', 'coin': coin, 'amount': float(tmp['free']) + float(tmp['locked'])})
        return result

    def get_balance(self):
        binance_balance = r.get("binance_balance")
        if binance_balance:
            return json.loads(binance_balance)
        logger.debug("binance balance expire")

        result = self.client.get_asset_balance(asset=self.basecoin)
        basecoin_amount = float(result['free']) + float(result['locked'])
        result = self.client.get_asset_balance(asset=self.product)
        product_amount = float(result['free']) + float(result['locked'])
        result = self.client.get_asset_balance(asset=self.feecoin)
        feecoin_amount = float(result['free']) + float(result['locked'])

        result = {'product': product_amount, 'basecoin': basecoin_amount, 'feecoin': feecoin_amount}
        r.set("binance_balance", json.dumps('result'), ex=ex)
        return result

    def get_balance_position(self):
        binance_balance_position = r.get("binance_balance_position")
        if binance_balance_position:
            return float(binance_balance_position)
        logger.debug("binance balance position expire")

        result = self.client.get_asset_balance(asset=self.basecoin)
        basecoin_amount = float(result['free']) + float(result['locked'])
        result = self.client.get_asset_balance(asset=self.product)
        product_amount = float(result['free']) + float(result['locked'])

        depth = self.get_depth()
        price = (depth['buy_one']['price'] + depth['sell_one']['price'])/2

        result = product_amount*price / (product_amount*price+basecoin_amount)
        r.set("binance_balance_position", result, ex=ex)
        return result

    def get_open_orders(self):
        orders = self.client.get_open_orders(symbol=self.trade_pair)
        result = []
        for order in orders:
            result.append({
                    'orderid': order['orderId'],
                    'side': order['side'],
                    'price': float(order['price']),
                    'time': order['time'],
                    'amount': float(order['origQty']),
                    'deal_amount': float(order['executedQty'])
                    })
        return result

    def buy(self, price, amount, plan, level, is_hedge):
        order = self.client.order_limit_buy(symbol=self.trade_pair, \
            quantity=amount, price=price)
        orderid = order['orderId']
        super().buy(price, amount, plan, level, is_hedge, orderid=orderid)
        return orderid

    def sell(self, price, amount, plan, level, is_hedge):
        order = self.client.order_limit_buy(symbol=self.trade_pair, \
            quantity=amount, price=price)
        order = self.client.order_limit_sell(
            symbol=self.trade_pair,
            quantity=amount,
            price=price)
        orderid = order['orderId']
        super().sell(price, amount, plan, level, is_hedge, orderid=orderid)
        return orderid

    def cancel_order(self, orderid):
        result = self.client.cancel_order(
            symbol=self.trade_pair,
            orderId=orderid)
        logger.debug("-->[binance][cancel][%s][order:%s]"%(self.trade_pair, orderid))
        super().cancel_order(orderid=orderid)
        return 0

    def get_depth(self, min_amount=0):
        depth = self.client.get_order_book(symbol=self.trade_pair)

        bids = [i for i in depth['bids'] if float(i[1])>=min_amount][0]
        asks = [i for i in depth['asks'] if float(i[1])>=min_amount][0]

        buy_one = {'price': float(bids[0]), 'amount': float(bids[1])}
        sell_one = {'price': float(asks[0]), 'amount': float(asks[1])}
        return {'buy_one': buy_one, 'sell_one': sell_one}

    def _get_week_prices(self):
        data = self.client.get_klines(symbol=self.trade_pair, interval=Client.KLINE_INTERVAL_1HOUR)[-72:-1]
        closes = [float(i[4]) for i in data]
        return closes

class Bibox(Market):
    def __init__(self, product="", basecoin=""):
        super().__init__(product, basecoin)
        self.trade_pair = self.product + "_" + self.basecoin
        self.uri = "https://api.bibox.com/v1"
        self.feecoin = "BIX"

    def get_fee(self):
        return 0.0005


    def __getSign(self, data,secret):
        result = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.md5).hexdigest()
        return result

    def __doApiRequestWithApikey(self, url, cmds):
        s_cmds = json.dumps(cmds)
        sign = self.__getSign(s_cmds, bibox_secret_key)
        r = requests.post(url, data={'cmds': s_cmds, 'apikey': bibox_api_key,'sign':sign}, \
                proxies=proxies)
        try:
            return json.loads(r.text)['result'][0]['result']
        except Exception:
            traceback.print_exc()

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

    def get_order_detail(self, orderid):
        url = "https://api.bibox.com/v1/orderpending"
        cmds = [
                {
                    'cmd': 'orderpending/order',
                    'body': {
                        'id': orderid
                        }
                    }
                ]
        order =  self.__doApiRequestWithApikey(url,cmds)
        return {
                'orderid': float(orderid),
                'amount': float(order['amount']),
                'deal_amount': float(order['deal_amount']),
                'side': 'BUY' if order['order_side']==1 else 'SELL',
                'time': order['createdAt'],
                'price': float(order['price'])
                }

    def buy(self, price, amount, plan, level, is_hedge):
        orderid = self.__post_order(1, price, amount)
        super().buy(price, amount, plan, level, is_hedge, orderid=orderid)
        return orderid

    def sell(self, price, amount, plan, level, is_hedge):
        orderid = self.__post_order(2, price, amount)
        super().sell(price, amount, plan, level, is_hedge, orderid=orderid)
        return orderid

    def cancel_order(self, orderid):
        url = "https://api.bibox.com/v1/orderpending"
        cmds = [
                {
                    'cmd': 'orderpending/cancelTrade',
                    'body': {
                        'orders_id': orderid
                        }
                    }
                ]
        data =  self.__doApiRequestWithApikey(url,cmds)
        logger.debug("-->[bibox][cancel][%s][order:%s]"%(self.trade_pair, orderid))
        super().cancel_order(orderid=orderid)
        return 0

    def get_open_orders(self):
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
        orders = data['items']
        result = []
        for order in orders:
            result.append({
                'orderid': order['id'],
                'side': 'BUY' if order['order_side']==1 else 'SELL',
                'price': float(order['price']),
                'time': order['createdAt'],
                'amount': float(order['amount']),
                'deal_amount': float(order['deal_amount'])
                })
        return result 

    def get_balance_all(self, coins):
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
        result = []
        for asset in data['assets_list']:
            if asset['coin_symbol'] in coins:
                result.append({'market': 'bibox', 'coin': asset['coin_symbol'], 'amount': float(asset['balance'])})
        return result

    def get_balance(self):

        bibox_balance= r.get("bibox_balance")
        if bibox_balance:
            return json.loads(bibox_balance)
        logger.debug("bibox balance expire")

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
        for asset in data['assets_list']:
            if asset['coin_symbol'] == self.basecoin:
                basecoin_amount = float(asset['balance'])
            elif asset['coin_symbol'] == self.product:
                product_amount = float(asset['balance'])
            elif asset['coin_symbol'] == self.feecoin:
                feecoin_amount = float(asset['balance'])
        result = {'product': product_amount, 'basecoin': basecoin_amount, 'feecoin': feecoin_amount}
        r.set("bibox_balance", json.dumps(result), ex=ex)
        return result

    def get_balance_position(self):
        bibox_balance_position = r.get("bibox_balance_position")
        if bibox_balance_position:
            return float(bibox_balance_position)
        logger.debug("bibox balance position expire")

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

        result = product_balance / (product_balance + basecoin_balance)
        r.set("bibox_balance_position", result, ex=ex)
        return result

    def _get_week_prices(self):
        """过去一周的每小时close价格"""
        url = "https://api.bibox.com/v1/mdata?cmd=kline&pair={trade_pair}&period=1hour&size=72" \
                .format(trade_pair=self.trade_pair)
        for _ in range(3):
            r = requests.get(url, proxies=proxies)
            if r.text != '':
                break
                time.sleep(2)
        data = json.loads(r.text)
        closes = [float(i['close']) for i in data['result']]
        return closes

    def get_depth(self, min_amount=0):
        url = "https://api.bibox.com/v1/mdata?cmd=depth&pair={trade_pair}&size=10"\
                .format(trade_pair=self.trade_pair)
        r = requests.get(url, proxies=proxies)
        data = json.loads(r.text)
        bids = data['result']['bids']
        asks = data['result']['asks']

        buy_one = [i for i in bids if float(i['volume'])>=min_amount][0]
        sell_one = [i for i in asks if float(i['volume'])>=min_amount][0]

        buy_one['price'] = float(buy_one['price'])
        buy_one['amount'] = float(buy_one['volume'])
        buy_one.pop('volume')
        sell_one['price'] = float(sell_one['price'])
        sell_one['amount'] = float(sell_one['volume'])
        sell_one.pop('volume')

        return {'buy_one': buy_one, 'sell_one': sell_one}

if __name__=="__main__":
    bibox = Bibox('EOS', 'BTC')
#    print(bibox.get_order_detail(594940813))
#    print(bibox.get_average_price())
#    print(bibox.get_depth())
    print(bibox.get_balance())
    print(bibox.get_balance_position())
#    print(bibox.get_open_orders())
#    print(bibox.clear_open_orders())
#
    print("bibox<------->binance")
    binance = Binance('EOS', 'BTC')
#    print(binance.get_order_detail(56126001))
#    print(binance.get_average_price())
#    print(binance.get_depth())
    print(binance.get_balance())
    print(binance.get_balance_position())
#    print(binance.get_open_orders())
#    print(binance.clear_open_orders())
#
