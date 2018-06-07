from db import Mysql, Trade, Balance
from market import market_factory, Binance, Bibox
from utils.timeutils import v_date_current_hyphen

mysql = Mysql()

def auto_close_out():
    session = mysql.DBSession()
    query = session.query(Trade)
    query_result = query.filter(Trade.is_hedge==1).filter(Trade.updated_at==None)
    session.close()
    for order in query_result:
        the_market = market_factory(order.market)(product=order.pair.split('_')[0], \
                basecoin=order.pair.split('_')[1])
        order_detail = the_market.get_order_detail(order.orderid)
        the_market.cancel_order(order.orderid)
        the_market.buy(the_market.get_depth()['sell_one']['price'], order.amount, order.plan, 'high', 1)

def record_balance():
    coins = ['BTC', 'EOS', 'BNB', 'BIX']
    binance_balance = Binance().get_balance_all(coins)
    bibox_balance = Bibox().get_balance_all(coins)
    balances = [Balance(amount=b['amount'], coin=b['coin'], market=b['market']) for b in binance_balance + bibox_balance]
    mysql.insert_balance(balances, date=v_date_current_hyphen)

