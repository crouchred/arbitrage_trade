class Strategy:

    def __init__(self, m1, m2, min_amount=1, max_amount=5):
        self.m1 = m1
        self.m2 = m2
        self.min_amount = min_amount # 限制于交易所
        self.max_amount = max_amount # 限制于胆子小

    def get_fee_total(self):
        """当前至少需要达到的盈利率系数"""
        return self.m1.get_fee() + self.m2.get_fee()

    def allocate_strategy(self):

        m1_depth = self.m1.get_depth(self.min_amount)
        m2_depth = self.m2.get_depth(self.min_amount)

        m1_buy_ratio = self.get_fee_total() * self.m1.get_profit_ratio('BUY') + 1
        m1_sell_ratio = self.get_fee_total() * self.m1.get_profit_ratio('SELL') + 1
    
        StrategyPlanClassList = [StrategyPlan1, StrategyPlan2]
        for StrategyPlanClass in StrategyPlanClassList:
            strategy = StrategyPlanClass(m1=self.m1, m2=self.m2, m1_depth=m1_depth, m2_depth=m2_depth, \
                    m1_buy_ratio=m1_buy_ratio, m1_sell_ratio=m1_sell_ratio, max_amount=self.max_amount)
            if strategy.check():
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

    def adjust_amount(self, amount):
        amount = min(amount, self.max_amount)
        amount = int(amount*10) / 10
        return amount

    def check(self):
        raise NotImplementedError('')

    def exe(self):
        raise NotImplementedError('')

class StrategyPlan1(StrategyPlan):

    def check(self):
        return self.m1_depth['buy_one']['price'] / self.m2_depth['sell_one']['price'] > self.m1_sell_ratio

    def exe(self):
        amount = min(self.m1_depth['buy_one']['amount'], self.m2_depth['sell_one']['amount'])
        amount = self.adjust_amount(amount)
        self.m1.sell(self.m1_depth['buy_one']['price'], amount)
        self.m2.buy(self.m2_depth['sell_one']['price'], amount)

class StrategyPlan2(StrategyPlan):

    def check(self):
        return self.m2_depth['buy_one']['price'] / self.m1_depth['sell_one']['price'] > self.m1_buy_ratio

    def exe(self):
        amount = min(self.m1_depth['buy_one']['amount'], self.m2_depth['sell_one']['amount'])
        amount = self.adjust_amount(amount)
        self.m1.buy(self.m1_depth['sell_one']['price'], amount)
        self.m2.sell(self.m2_depth['buy_one']['price'], amount)

     
