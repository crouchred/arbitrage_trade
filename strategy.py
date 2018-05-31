import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

class Strategy:

    def __init__(self, m1, m2, min_amount=1, max_amount=5):
        self.m1 = m1
        self.m2 = m2
        self.min_amount = min_amount # 限制于交易所
        self.max_amount = max_amount # 限制于胆子小
        self.skip_price = 0.0001
    
    def get_profit_ratio(self, side='BUY'):
        """根据仓位确定需要的盈利率系数"""
        m1_balance_position = self.m1.get_balance_position()
        m2_balance_position = self.m2.get_balance_position()
        if m1_balance_position > 0.5:
            balance_position = max(m1_balance_position, (1-m2_balance_position))
        elif m1_balance_position < 0.5:
            balance_position = min(m1_balance_position, (1-m2_balance_position))

        if side == 'SELL':
            balance_position = 1 - balance_position
        if 0 <= balance_position <= 0.1:
            ratio = 1
        elif 0.1 < balance_position <= 0.9:
            ratio = 1.2
        elif 0.9 < balance_position:
            ratio = 5
        return ratio

    def get_fee_total(self):
        """当前至少需要达到的盈利率系数"""
        return self.m1.get_fee() + self.m2.get_fee()

    def allocate_strategy(self):

        m1_depth = self.m1.get_depth(self.min_amount)
        m2_depth = self.m2.get_depth(self.min_amount)
        bias = self.m1.get_average_price() / self.m2.get_average_price() - 1 

        # bias梳理: 如果m1价格<m2价格, m1更容易买到product, bias<0, m1_buy_ratio应该变大，使m1更难买到product
        m1_buy_ratio = self.get_fee_total() * self.m1.get_profit_ratio('BUY') - bias + 1 
        m1_sell_ratio = self.get_fee_total() * self.m1.get_profit_ratio('SELL') + bias + 1
    
        StrategyPlanClassList = [StrategyPlan1, StrategyPlan2]
        for StrategyPlanClass in StrategyPlanClassList:
            strategy = StrategyPlanClass(m1=self.m1, m2=self.m2, m1_depth=m1_depth, m2_depth=m2_depth, \
                    m1_buy_ratio=m1_buy_ratio, m1_sell_ratio=m1_sell_ratio, max_amount=self.max_amount, \
                    bias=bias)
            strategy.previous_exe()
            if strategy.do_exe and strategy.check():
                strategy.exe()
                break

class StrategyPlan:

    def __init__(self, **kw):
        self.m1 = kw['m1']
        self.m2 = kw['m2']
        self.m1_depth = kw['m1_depth']
        self.m2_depth = kw['m2_depth']
        self.m1_buy_ratio = kw['m1_buy_ratio']
        self.m1_sell_ratio = kw['m1_sell_ratio']
        self.max_amount = kw['max_amount']
        self.bias = kw['bias']
        self.do_exe = True

    def previous_exe(self):
        order_in_redis = r.get(self.name)
        order_id = order_in_redis['order_id']
        if order_id is None:
            return
        order =  self.origin_market.order_detail(order_id)
        if order['deal_amount'] == 0:
            if self.check():
                self.do_exe = False
            else:
                self.origin_market.cancel_order(order_id)
        else:
            if order['deal_amount'] != order['amount']: # 未完成订单
                self.origin_market.cancel_order(order_id)
            hedge_order_id = self.hedge_market.__getattribute__(\
                    order_in_redis['hedge']['action'])(order_in_redis['hedge']['price'], \
                    min(order['deal_amount'], self.min_amount))
            r.sadd('hedge_order_ids', hedge_order_id)    

    def adjust_amount(self, amount):
        amount = min(amount, self.max_amount)
        amount = int(amount*10) / 10
        return amount

    def previous_exe(self):
        pass

    def check(self):
        raise NotImplementedError('')

    def exe(self):
        raise NotImplementedError('')

class StrategyPlan1(StrategyPlan):

    def check(self):
        """m1的买单>m2的卖单"""
        return self.m1_depth['buy_one']['price'] / self.m2_depth['sell_one']['price'] > self.m1_sell_ratio

    def exe(self):
        amount = min(self.m1_depth['buy_one']['amount'], self.m2_depth['sell_one']['amount'])
        amount = self.adjust_amount(amount)
        print("bias: %s"%(self.bias))
        self.m1.sell(self.m1_depth['buy_one']['price'], amount)
        self.m2.buy(self.m2_depth['sell_one']['price'], amount)

class StrategyPlan2(StrategyPlan):

    def check(self):
        """m2的买单>m1的卖单"""
        return self.m2_depth['buy_one']['price'] / self.m1_depth['sell_one']['price'] > self.m1_buy_ratio

    def exe(self):
        amount = min(self.m1_depth['buy_one']['amount'], self.m2_depth['sell_one']['amount'])
        amount = self.adjust_amount(amount)
        print("bias: %s"%(self.bias))
        self.m1.buy(self.m1_depth['sell_one']['price'], amount)
        self.m2.sell(self.m2_depth['buy_one']['price'], amount)

class StrategyPlan3(StrategyPlan):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.name = 'plan3'
        self.origin_market = self.m1
        self.hedge_market = self.m2

    def check(self):
        """m1的卖单>m2的卖单"""
        return self.m1_depth['sell_one']['price'] / self.m2_depth['sell_one']['price'] > self.m1_sell_ratio

    def exe(self):
        amount = self.m2_depth['sell_one']['amount']
        amount = self.adjust_amount(amount)
        order_id = self.m1.sell(self.m1_depth['sell_one']['price']-self.skip_price, amount)
        r.set(self.name, {'order_id':'order_id', 'hedge':{'price': self.m2_depth['sell_one']['price'], 'action':'sell'}})    

class StrategyPlan4(StrategyPlan):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.name = 'plan4'
        self.origin_market = self.m2
        self.hedge_market = self.m1

    def check(self):
        """m2的卖单>m1的卖单"""
        return self.m2_depth['sell_one']['price'] / self.m1_depth['sell_one']['price'] > self.m1_buy_ratio

    def exe(self):
        amount = self.m1_depth['sell_one']['amount']
        amount = self.adjust_amount(amount)
        order_id = self.m2.sell(self.m2_depth['sell_one']['price']-self.skip_price, amount)
        r.set(self.name, {'order_id':'order_id', 'hedge':{'price': self.m1_depth['sell_one']['price'], 'action':'sell'}})    

class StrategyPlan5(StrategyPlan):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.name = 'plan5'
        self.origin_market = self.m1
        self.hedge_market = self.m2

    def check(self):
        """m1的买单<m2的买单"""
        return self.m2_depth['buy_one']['price'] / self.m1_depth['buy_one']['price'] > self.m1_buy_ratio

    def exe(self):
        amount = self.m2_depth['buy_one']['amount']
        amount = self.adjust_amount(amount)
        order_id = self.m1.buy(self.m1_depth['buy_one']['price']+self.skip_price, amount)
        r.set(self.name, {'order_id':'order_id', 'hedge':{'price': self.m2_depth['buy_one']['price'], 'action':'buy'}})    

class StrategyPlan6(StrategyPlan):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.name = 'plan6'
        self.origin_market = self.m2
        self.hedge_market = self.m1

    def check(self):
        """m1的买单>m2的买单"""
        return self.m1_depth['buy_one']['price'] / self.m2_depth['buy_one']['price'] > self.m1_sell_ratio

    def exe(self):
        amount = self.m1_depth['buy_one']['amount']
        amount = self.adjust_amount(amount)
        order_id = self.m2.buy(self.m2_depth['buy_one']['price']+self.skip_price, amount)
        r.set(self.name, {'order_id':'order_id', 'hedge':{'price': self.m1_depth['buy_one']['price'], 'action':'sell'}})    


