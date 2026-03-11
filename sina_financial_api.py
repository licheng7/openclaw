#!/usr/bin/env python3
"""
新浪财报 API - 获取财务数据
"""
import requests
import re

class SinaFinancialAPI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://finance.sina.com.cn',
        }
    
    def get_financial_data(self, code):
        """获取财报数据（最近8个季度）"""
        url = f'http://money.finance.sina.com.cn/corp/go.php/vFD_ProfitStatement/stockid/{code}/ctrl/part/displaytype/4.phtml'
        
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'gb2312'
            
            if r.status_code == 200:
                text = r.text
                
                # 提取报告期
                periods = re.findall(r'(\d{4}-\d{2}-\d{2})', text)
                valid_periods = []
                for p in periods:
                    if (p.endswith('-03-31') or p.endswith('-06-30') or 
                        p.endswith('-09-30') or p.endswith('-12-31')):
                        if p not in valid_periods and p >= '2023-01-01':
                            valid_periods.append(p)
                
                valid_periods.sort(reverse=True)
                
                # 提取营业收入
                revenue_match = re.search(r'一、营业收入</a></td>((?:<td[^>]*>[\d,.-]+</td>\s*)+)', text)
                revenues = []
                if revenue_match:
                    revenues = re.findall(r'<td[^>]*>([\d,.-]+)</td>', revenue_match.group(1))
                
                # 提取净利润
                profit_match = re.search(r'净利润</a></td>((?:<td[^>]*>[\d,.-]+</td>\s*)+)', text)
                profits = []
                if profit_match:
                    profits = re.findall(r'<td[^>]*>([\d,.-]+)</td>', profit_match.group(1))
                
                # 组合数据
                result_data = []
                for i in range(min(len(valid_periods), len(revenues), len(profits), 8)):
                    result_data.append({
                        'period': valid_periods[i],
                        'revenue': float(revenues[i].replace(',', '')),
                        'profit': float(profits[i].replace(',', ''))
                    })
                
                return result_data
                
        except Exception as e:
            # 静默失败，返回空数据
            pass
        
        return []
    
    def analyze_growth(self, financial_data):
        """分析财报增长情况"""
        if not financial_data or len(financial_data) < 2:
            return {
                'continuous_growth': False,
                'accelerating_growth': False,
                'high_growth': False,
                'score': 0,
                'signals': []
            }
        
        signals = []
        score = 0
        
        # 检查连续增长（需要至少4个季度，跳过Q1 vs Q4的比较）
        continuous_growth = True
        growth_rates = []
        
        for i in range(len(financial_data) - 1):
            current = financial_data[i]
            previous = financial_data[i + 1]
            
            # 跳过跨年度的Q1 vs Q4比较（会出现负增长）
            if current['period'].endswith('-03-31') and previous['period'].endswith('-12-31'):
                continue
            
            revenue_growth = (current['revenue'] - previous['revenue']) / previous['revenue'] * 100
            profit_growth = (current['profit'] - previous['profit']) / previous['profit'] * 100
            
            growth_rates.append({
                'revenue': revenue_growth,
                'profit': profit_growth
            })
            
            # 如果营收或利润下降，则不是连续增长
            if revenue_growth < 0 or profit_growth < 0:
                continuous_growth = False
        
        # 规则3.1: 连续增长 +15分
        if continuous_growth and len(growth_rates) >= 3:
            score += 15
            signals.append('连续增长')
        
        # 规则3.2: 增长率加速 +20分
        accelerating = False
        if len(growth_rates) >= 3:
            # 检查增长率是否递增
            revenue_accelerating = all(growth_rates[i]['revenue'] < growth_rates[i+1]['revenue'] 
                                      for i in range(len(growth_rates)-1))
            profit_accelerating = all(growth_rates[i]['profit'] < growth_rates[i+1]['profit'] 
                                     for i in range(len(growth_rates)-1))
            
            if revenue_accelerating and profit_accelerating:
                score += 20
                signals.append('增长加速')
                accelerating = True
        
        # 规则3.3: 近一年高增长 +20分
        # 比较最近4个季度 vs 前4个季度
        high_growth = False
        if len(financial_data) >= 8:
            # 最近4个季度总和
            recent_revenue = sum(d['revenue'] for d in financial_data[:4])
            recent_profit = sum(d['profit'] for d in financial_data[:4])
            
            # 前4个季度总和
            previous_revenue = sum(d['revenue'] for d in financial_data[4:8])
            previous_profit = sum(d['profit'] for d in financial_data[4:8])
            
            if previous_revenue > 0 and previous_profit > 0:
                annual_revenue_growth = (recent_revenue - previous_revenue) / previous_revenue * 100
                annual_profit_growth = (recent_profit - previous_profit) / previous_profit * 100
                
                if annual_revenue_growth > 50 or annual_profit_growth > 100:
                    score += 20
                    if annual_revenue_growth > 50:
                        signals.append(f'年营收增长{annual_revenue_growth:.0f}%')
                    if annual_profit_growth > 100:
                        signals.append(f'年利润增长{annual_profit_growth:.0f}%')
                    high_growth = True
        
        return {
            'continuous_growth': continuous_growth,
            'accelerating_growth': accelerating,
            'high_growth': high_growth,
            'score': score,
            'signals': signals
        }

if __name__ == '__main__':
    api = SinaFinancialAPI()
    
    # 测试
    data = api.get_financial_data('600000')
    if data:
        print(f"获取到 {len(data)} 个季度的数据\n")
        for d in data:
            print(f"{d['period']}: 营收 {d['revenue']:,.0f}万, 利润 {d['profit']:,.0f}万")
        
        analysis = api.analyze_growth(data)
        print(f"\n增长分析:")
        print(f"  得分: {analysis['score']}")
        print(f"  信号: {analysis['signals']}")
