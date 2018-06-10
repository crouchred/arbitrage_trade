from db import Mysql, Trade, Balance
from market import market_factory, Binance, Bibox
from utils.timeutils import v_date_current_hyphen
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

from utils.logger import Logger
logger = Logger.get_logger(__file__)

from utils.catch_error import catch_decorator

mysql = Mysql()

@catch_decorator
def auto_close_out():
    # 包含自动平仓及更新所有订单信息
    # is_hedge=2 代表取消了之后重新下单
    session = mysql.DBSession()
    query = session.query(Trade)
    #query_result = query.filter(Trade.is_hedge==1).filter(Trade.updated_at==None)
    query_result = query.filter(Trade.updated_at==None)
    session.close()
    for order_db in query_result:
        the_market = market_factory(order_db.market)(product=order_db.pair.split('_')[0], \
                basecoin=order_db.pair.split('_')[1])
        order_detail = the_market.get_order_detail(order_db.orderid)
        just_close = True if order_detail['amount'] == order_detail['deal_amount'] else False
        the_market.cancel_order(order_db.orderid, order_detail['deal_amount'], just_close)
        if just_close is False and order_db.is_hedge == 1:
            the_market.buy(the_market.get_depth()['sell_one']['price'], \
                    order_detail['amount']-order_detail['deal_amount'], order_db.plan, 'high', 2, order_db.orderid)

@catch_decorator
def record_balance():
    logger.info("start to record balance")
    coins = ['BTC', 'EOS', 'BNB', 'BIX']
    binance_balance = Binance().get_balance_all(coins)
    bibox_balance = Bibox().get_balance_all(coins)
    balances = [Balance(amount=b['amount'], coin=b['coin'], market=b['market']) for b in binance_balance + bibox_balance]
    mysql.insert_balance(balances, date=v_date_current_hyphen)
    logger.info("record balance done")
