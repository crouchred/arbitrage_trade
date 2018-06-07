from db import Mysql, Trade
from market import market_factory

mysql = Mysql()

def auto_close_out():
    session = mysql.DBSession()
    query = session.query(Trade)
    query_result = query.filter(Trade.is_hedge==1).filter(Trade.updated_at==None)
    session.close()
    for order in query_result:
        the_market = market_factory(order.market])
        order_detail = the_market.get_order_detail(order.orderid)
        the_market.cancel_order(order.orderid)
        the_market.buy(the_market.get_depth()['sell_one']['price'], order.amount, order.plan, 'high', 1)

