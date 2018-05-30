
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
    
        if self.s1(m1_depth, m2_depth, m1_sell_ratio):
            return 
        if self.s2(m1_depth, m2_depth, m1_sell_ratio):
            return 

    def s1(self, m1_depth, m2_depth, m1_buy_ratio, m1_sell_ratio):

        if m1_depth['buy_one']['price'] / m2_depth['sell_one']['price'] > m1_sell_ratio:
            amount = min(m1_depth['buy_one']['amount'], m2_depth['sell_one']['amount'], \
                    self.max_amount)
            self.m1.sell(m1_depth['buy_one']['price'], amount)
            self.m2.buy(m2_depth['sell_one']['price'], amount)
            return True

    def s2(self, m1_depth, m2_depth):

        if m1_depth['sell_one']['price'] / m2_depth['buy_one']['price'] > m1_buy_ratio:
            amount = min(m1_depth['sell_one']['amount'], m2_depth['buy_one']['amount'], \
                    self.max_amount)
            self.m1.buy(m1_depth['sell_one']['price'], amount)
            self.m2.sell(m2_depth['buy_one']['price'], amount)
     
