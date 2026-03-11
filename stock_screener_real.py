#!/usr/bin/env python3
"""
股票筛选器 - 使用新浪接口真实数据版本
"""
import sys
import json
from sina_api import SinaStockAPI

class StockScreenerReal:
    def __init__(self):
        self.api = SinaStockAPI()
        self.min_market_cap = 5e9  # 50亿
        self.max_rise_1m = 0.5  # 1月涨幅50%
    
    def filter_market_scope(self, stocks):
        """规则1: 筛选主板"""
        print("\n[规则1] 筛选市场范围（主板）...")
        
        result = []
        for stock in stocks:
            code = stock['code']
            # 主板：60xxxx (上海主板), 000xxx/001xxx (深圳主板)
            if code.startswith('60') or code.startswith('000') or code.startswith('001'):
                result.append(stock)
        
        print(f"  符合条件: {len(result)} 只")
        return result
    
    def calculate_score(self, stock):
        """计算股票得分"""
        score = 0
        signals = []
        
        # 基础分
        score += 5
        signals.append('主板股票')
        
        # 根据涨跌幅判断
        change = stock['change_pct']
        
        if -3 < change < 3:
            score += 5
            signals.append('震荡整理')
        elif change < -5:
            score += 10
            signals.append('超跌反弹机会')
        
        # 成交量判断（简化）
        if stock['volume'] > 10000000:  # 成交量大于1000万
            score += 3
            signals.append('成交活跃')
        
        return score, signals
    
    def screen_stocks(self, limit=30):
        """执行筛选"""
        print("=" * 60)
        print("开始股票筛选（真实数据）...")
        print("=" * 60)
        
        # 获取股票数据
        print("\n获取股票数据...")
        all_stocks = self.api.get_all_stocks()
        
        if not all_stocks:
            print("未获取到股票数据")
            return []
        
        # 规则1: 市场范围
        stocks = self.filter_market_scope(all_stocks)
        
        # 计算得分
        print("\n计算股票得分...")
        results = []
        for stock in stocks:
            score, signals = self.calculate_score(stock)
            results.append({
                'code': stock['code'],
                'name': stock['name'],
                'price': stock['price'],
                'change_pct': stock['change_pct'],
                'score': score,
                'signals': signals
            })
        
        # 按得分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n筛选完成！共 {len(results)} 只符合条件的股票")
        return results[:limit]

def main():
    screener = StockScreenerReal()
    recommendations = screener.screen_stocks(limit=30)
    
    if recommendations:
        print("\n" + "=" * 60)
        print("推荐股票列表 (前30只)")
        print("=" * 60)
        
        for i, stock in enumerate(recommendations, 1):
            print(f"\n{i}. {stock['name']} ({stock['code']})")
            print(f"   价格: ¥{stock['price']:.2f}  涨跌幅: {stock['change_pct']:+.2f}%")
            print(f"   得分: {stock['score']}  信号: {', '.join(stock['signals'])}")
        
        # 保存到文件
        output_file = 'stock_recommendations_real.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")
    else:
        print("\n未找到符合条件的股票")

if __name__ == '__main__':
    main()
