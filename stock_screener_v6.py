#!/usr/bin/env python3
"""
股票筛选器 - 规则1+2+3+4+5+6+7+8+9+10（完整版）
"""
import sys
import json
from tencent_api import TencentStockAPI
from sina_financial_api import SinaFinancialAPI
from sina_history_api import SinaHistoryAPI
from eastmoney_shareholder_api import EastmoneyShareholderAPI
from eastmoney_announcement_api import EastmoneyAnnouncementAPI
from shareholding_change_analyzer import ShareholdingChangeAnalyzer
from volume_analyzer import VolumeAnalyzer

class StockScreenerReal:
    def __init__(self):
        self.tencent_api = TencentStockAPI()
        self.sina_financial_api = SinaFinancialAPI()
        self.sina_history_api = SinaHistoryAPI()
        self.eastmoney_shareholder_api = EastmoneyShareholderAPI()
        self.eastmoney_announcement_api = EastmoneyAnnouncementAPI()
        self.shareholding_change_analyzer = ShareholdingChangeAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
    
    def get_all_stocks(self):
        """获取所有主板股票"""
        print("获取股票数据...")
        stocks = []
        
        # 上海主板 600000-603999（先测试100只）
        for i in range(600000, 600100):
            code = f'{i:06d}'
            stock = self.tencent_api.get_stock_info(code)
            if stock and stock['name']:
                stocks.append(stock)
                if len(stocks) % 10 == 0:
                    print(f"  已获取 {len(stocks)} 只...")
        
        return stocks
    
    def filter_market_scope(self, stocks):
        """筛选市场范围"""
        print("\n[筛选] 市场范围...")
        
        result = []
        for stock in stocks:
            code = stock['code']
            # 主板：60xxxx (上海主板), 000xxx/001xxx (深圳主板)
            if code.startswith('60') or code.startswith('000') or code.startswith('001'):
                stock['market'] = '主板'
                result.append(stock)
        
        print(f"  符合条件: {len(result)} 只（主板）")
        return result
    
    def calculate_score(self, stock):
        """计算股票得分"""
        score = 0
        signals = []
        
        # 规则1: 主板 +5分
        if stock.get('market') == '主板':
            score += 5
            signals.append('主板')
        
        # 规则2: 市值评分
        market_cap = stock.get('market_cap', 0)
        if 50 <= market_cap < 100:
            score += 5
            signals.append('市值50-100亿')
        elif 100 <= market_cap < 300:
            score += 8
            signals.append('市值100-300亿')
        elif 300 <= market_cap < 600:
            score += 12
            signals.append('市值300-600亿')
        elif 600 <= market_cap < 1500:
            score += 15
            signals.append('市值600-1500亿')
        elif 1500 <= market_cap < 5000:
            score += 17
            signals.append('市值1500-5000亿')
        elif 5000 <= market_cap < 15000:
            score += 20
            signals.append('市值5000-15000亿')
        elif market_cap >= 15000:
            score += 15
            signals.append('市值15000亿以上')
        elif market_cap < 50:
            signals.append(f'市值{market_cap:.0f}亿(不符合)')
        
        # 规则3: 财报增长评分
        try:
            financial_data = self.sina_financial_api.get_financial_data(stock['code'])
            if financial_data:
                growth_analysis = self.sina_financial_api.analyze_growth(financial_data)
                score += growth_analysis['score']
                signals.extend(growth_analysis['signals'])
        except:
            pass
        
        # 规则4: 历史价格回调分析
        try:
            drawdown_analysis = self.sina_history_api.analyze_drawdown(stock['code'], stock['price'])
            score += drawdown_analysis['score']
            signals.extend(drawdown_analysis['signals'])
        except:
            pass
        
        # 规则6: 近1月涨幅限制
        try:
            monthly_gain_analysis = self.sina_history_api.analyze_monthly_gain(stock['code'], stock['price'])
            score += monthly_gain_analysis['score']
            signals.extend(monthly_gain_analysis['signals'])
        except:
            pass
        
        # 规则7: 重大风险公告（带缓存）
        try:
            risk_analysis = self.eastmoney_announcement_api.analyze_risk_announcements(stock['code'])
            score += risk_analysis['score']
            signals.extend(risk_analysis['signals'])
        except:
            pass
        
        # 规则8: 减持判断
        try:
            # 获取历史数据用于判断价格位置
            history_data = self.sina_history_api.get_history_data(stock['code'])
            reduction_analysis = self.shareholding_change_analyzer.analyze_reduction(
                stock['code'], stock['price'], history_data
            )
            score += reduction_analysis['score']
            signals.extend(reduction_analysis['signals'])
        except:
            pass
        
        # 规则9: 增持/回购信号
        try:
            increase_analysis = self.shareholding_change_analyzer.analyze_increase(stock['code'])
            score += increase_analysis['score']
            signals.extend(increase_analysis['signals'])
        except:
            pass
        
        # 规则10: 底部放量突破
        try:
            volume_analysis = self.volume_analyzer.analyze_bottom_breakout(stock['code'], stock['price'])
            score += volume_analysis['score']
            signals.extend(volume_analysis['signals'])
        except:
            pass
        
        # 规则5: 股东人数变化（带缓存）
        try:
            shareholder_analysis = self.eastmoney_shareholder_api.analyze_shareholder_change(stock['code'])
            score += shareholder_analysis['score']
            signals.extend(shareholder_analysis['signals'])
        except:
            pass
        
        # 根据涨跌幅判断
        change = stock['change_pct']
        
        if -3 < change < 3:
            score += 5
            signals.append('震荡整理')
        elif change < -5:
            score += 10
            signals.append('超跌反弹机会')
        
        # 成交量判断
        if stock['volume'] > 100000:
            score += 3
            signals.append('成交活跃')
        
        return score, signals
    
    def screen_stocks(self, limit=30):
        """执行筛选"""
        print("=" * 60)
        print("开始股票筛选（规则1-10完整版）...")
        print("=" * 60)
        
        # 获取股票数据
        all_stocks = self.get_all_stocks()
        
        if not all_stocks:
            print("未获取到股票数据")
            return []
        
        # 筛选市场范围
        stocks = self.filter_market_scope(all_stocks)
        
        # 计算得分
        print("\n计算股票得分（含财报+历史价格+股东人数+近1月涨幅+风险公告+减持/增持+底部放量分析）...")
        results = []
        for idx, stock in enumerate(stocks):
            score, signals = self.calculate_score(stock)
            results.append({
                'code': stock['code'],
                'name': stock['name'],
                'price': stock['price'],
                'change_pct': stock['change_pct'],
                'market_cap': stock['market_cap'],
                'market': stock.get('market', '未知'),
                'score': score,
                'signals': signals
            })
            
            # 每10只显示进度
            if (idx + 1) % 10 == 0:
                print(f"  已处理 {idx + 1}/{len(stocks)} 只...")
        
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
            print(f"\n{i}. {stock['name']} ({stock['code']}) [{stock['market']}]")
            print(f"   价格: ¥{stock['price']:.2f}  涨跌幅: {stock['change_pct']:+.2f}%")
            print(f"   市值: {stock['market_cap']:.2f}亿")
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
