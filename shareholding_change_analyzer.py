#!/usr/bin/env python3
"""
减持/增持分析 - 基于东方财富公告数据
"""
import requests
import json
from datetime import datetime, timedelta

class ShareholdingChangeAnalyzer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        # 减持关键词
        self.reduction_keywords = ['减持', '减少持股', '股份减少', '出售股份']
        
        # 增持关键词
        self.increase_keywords = ['增持', '增加持股', '股份增加', '购买股份', '回购']
    
    def get_announcements(self, code):
        """获取公告数据"""
        url = f'http://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1&page_size=50&page_index=1&ann_type=SHA&client_source=web&stock_list={code}&f_node=0'
        
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and 'list' in data['data']:
                    return data['data']['list']
        except:
            pass
        
        return []
    
    def get_price_position(self, history_data, current_price):
        """判断当前价格位置（高位/低位）"""
        if not history_data or len(history_data) < 250:
            return 'unknown', 0, 0
        
        # 获取近1年数据（约250个交易日）
        recent_year = history_data[-250:]
        
        # 计算1年内的最高价和最低价
        high_1y = max(float(item['high']) for item in recent_year)
        low_1y = min(float(item['low']) for item in recent_year)
        
        # 判断位置
        # 高位：距最高点-15%以内
        if current_price >= high_1y * 0.85:
            position = 'high'
        # 低位：距最低点+20%以内
        elif current_price <= low_1y * 1.20:
            position = 'low'
        else:
            position = 'middle'
        
        return position, high_1y, low_1y
    
    def analyze_reduction(self, code, current_price, history_data):
        """分析减持情况"""
        announcements = self.get_announcements(code)
        
        if not announcements:
            return {
                'score': 0,
                'signals': []
            }
        
        now = datetime.now()
        
        # 查找减持公告
        reductions = []
        for item in announcements:
            title = item.get('title', '')
            date_str = item.get('notice_date', '')
            
            # 判断是否为减持公告
            if any(keyword in title for keyword in self.reduction_keywords):
                try:
                    ann_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    days_ago = (now - ann_date).days
                    
                    # 只看最近2个月
                    if days_ago <= 60:
                        reductions.append({
                            'title': title,
                            'days_ago': days_ago
                        })
                except:
                    pass
        
        if not reductions:
            return {
                'score': 0,
                'signals': []
            }
        
        # 判断价格位置
        position, high_1y, low_1y = self.get_price_position(history_data, current_price)
        
        # 找出最近的减持
        latest_reduction = min(reductions, key=lambda x: x['days_ago'])
        days_ago = latest_reduction['days_ago']
        
        score = 0
        signals = []
        
        # 规则8: 减持判断
        if position == 'high':
            # 高位减持
            if days_ago <= 30:
                score = -40
                signals.append(f'高位减持(警惕)')
        elif position == 'low':
            # 低位减持
            if days_ago <= 7:
                score = -20
                signals.append(f'低位减持(谨慎)')
            elif days_ago <= 14:
                score = -10
                signals.append(f'低位减持(观察)')
            elif days_ago <= 60:
                score = 15
                signals.append(f'低位减持(机会)')
        
        return {
            'score': score,
            'signals': signals,
            'reduction_count': len(reductions),
            'position': position
        }
    
    def analyze_increase(self, code):
        """分析增持/回购情况"""
        announcements = self.get_announcements(code)
        
        if not announcements:
            return {
                'score': 0,
                'signals': []
            }
        
        now = datetime.now()
        
        # 查找增持公告
        increases = []
        for item in announcements:
            title = item.get('title', '')
            date_str = item.get('notice_date', '')
            
            # 判断是否为增持公告
            if any(keyword in title for keyword in self.increase_keywords):
                try:
                    ann_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    days_ago = (now - ann_date).days
                    
                    # 只看最近3个月
                    if days_ago <= 90:
                        increases.append({
                            'title': title,
                            'days_ago': days_ago
                        })
                except:
                    pass
        
        if not increases:
            return {
                'score': 0,
                'signals': []
            }
        
        # 找出最近的增持
        latest_increase = min(increases, key=lambda x: x['days_ago'])
        days_ago = latest_increase['days_ago']
        
        score = 0
        signals = []
        
        # 规则9: 增持/回购评分
        if days_ago <= 7:
            score = 20
            signals.append(f'近1周增持/回购')
        elif days_ago <= 30:
            score = 15
            signals.append(f'近1月增持/回购')
        elif days_ago <= 90:
            score = 10
            signals.append(f'近3月增持/回购')
        
        return {
            'score': score,
            'signals': signals,
            'increase_count': len(increases)
        }

if __name__ == '__main__':
    from sina_history_api import SinaHistoryAPI
    
    analyzer = ShareholdingChangeAnalyzer()
    history_api = SinaHistoryAPI()
    
    # 测试
    test_stocks = [
        ('600000', 9.60, '浦发银行'),
        ('600519', 1401.18, '贵州茅台'),
    ]
    
    print("=== 测试减持/增持分析 ===\n")
    
    for code, price, name in test_stocks:
        print(f"{name} ({code})")
        
        # 获取历史数据
        history = history_api.get_history_data(code)
        
        # 分析减持
        reduction_result = analyzer.analyze_reduction(code, price, history)
        print(f"  减持分析:")
        print(f"    价格位置: {reduction_result.get('position', 'unknown')}")
        print(f"    得分: {reduction_result['score']:+d}")
        print(f"    信号: {reduction_result['signals']}")
        
        # 分析增持
        increase_result = analyzer.analyze_increase(code)
        print(f"  增持分析:")
        print(f"    得分: {increase_result['score']:+d}")
        print(f"    信号: {increase_result['signals']}")
        
        print()
