from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, create_engine
from sqlalchemy.dialects.mysql import VARCHAR, INTEGER, BIGINT, DOUBLE, DATETIME, TEXT
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

from utils.logger import Logger
logger = Logger.get_logger("db")

class Balance(Base):

    __tablename__ = 'balance'
    id = Column(INTEGER, primary_key=True)
    market = Column(VARCHAR(63))
    coin = Column(VARCHAR(63))
    amount = Column(DOUBLE)
    created_at = Column(DATETIME, default=datetime.datetime.now)
    updated_at = Column(DATETIME, onupdate=datetime.datetime.now)
    date = Column(VARCHAR(63))
    
class Trade(Base):
    __tablename__ = 'trade'
    id = Column(INTEGER, primary_key=True)
    orderid = Column(INTEGER)
    market = Column(VARCHAR(63))
    pair = Column(VARCHAR(63))
    side = Column(VARCHAR(63))
    plan = Column(VARCHAR(63))
    price = Column(DOUBLE)
    amount = Column(DOUBLE)
    deal_amount = Column(DOUBLE)
    is_hedge = Column(INTEGER)
    related_orderid = Column(INTEGER)
    level = Column(VARCHAR(63))
    created_at = Column(DATETIME, default=datetime.datetime.now)
    updated_at = Column(DATETIME, onupdate=datetime.datetime.now)

class Mysql:

    def __init__(self):

        engine = create_engine("mysql+pymysql://root:root@localhost:3306/arbitrage_trade?charset=utf8", pool_size=20, max_overflow=20)
        self.DBSession = sessionmaker(bind=engine)

    def insert_balance(self, balance_list, date):
        session = self.DBSession()
        query = session.query(Balance)
        query_result = query.filter(Balance.date==date)
        if query_result.first() is None:
            for balance in balance_list:
                balance.date = date
                session.add(balance)
            session.commit()
            session.close()
        else:
            print("already have")

    def upsert_trade(self, trade, columns_change=[], columns_not_change=[]):

        session = self.DBSession()
        query = session.query(Trade)
        query_result = query.filter(Trade.orderid==trade.orderid)
        if query_result.first() is None:
            session.add(trade)
            if trade.level == 'low':
                logger.debug("-->[%s][order:%s][limit][%s][%s][price:%s][amount:%s]"%( \
                        trade.market, trade.orderid, trade.side, trade.pair, trade.price, trade.amount))
            else:
                logger.info("-->[%s][order:%s][limit][%s][%s][price:%s][amount:%s]"%( \
                        trade.market, trade.orderid, trade.side, trade.pair, trade.price, trade.amount))

        else:
            columns_update = Trade.__table__.columns.keys()
            if columns_change != []:
                columns_update = columns_change
            elif columns_not_change != []:
                for c in columns_not_change:
                    columns_update.remove(c)
            query_result.update({column: getattr(trade, column) for column in columns_update})
        session.commit()
        session.close()

