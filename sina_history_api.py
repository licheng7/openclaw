#!/usr/bin/env python3
"""
新浪历史价格 API - 获取历史K线数据
"""
import requests
import json

class SinaHistoryAPI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://finance.sina.com.cn',
        }
    
    def get_history_data(self, code):
        """获取历史K线数据（最近18个月，约360个交易日）"""
        # 新浪历史K线接口
        # scale=240 表示日K线
        # datalen=360 表示获取360个交易日数据（约18个月）
        symbol = f'sh{code}' if code.startswith('6') else f'sz{code}'
        url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=5&datalen=360'
        
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = json.loads(r.text)
                if data and len(data) > 0:
                    return data
        except Exception as e:
            pass
        
        return []
    
    def analyze_drawdown(self, code, current_price):
        """分析当前价格相对18个月高点的回调幅度"""
        history = self.get_history_data(code)
        
        if not history or len(history) < 30:
            return {
                'score': 0,
                'signals': [],
                'drawdown': 0,
                'high_18m': 0
            }
        
        # 找出18个月内的最高价
        high_18m = max(float(item['high']) for item in history)
        
        # 计算回调幅度
        drawdown = (high_18m - current_price) / high_18m * 100
        
        score = 0
        signals = []
        
        # 规则4: 回调幅度评分
        if drawdown >= 60:
            score = 35
            signals.append(f'距高点回调{drawdown:.1f}%')
        elif drawdown >= 45:
            score = 25
            signals.append(f'距高点回调{drawdown:.1f}%')
        elif drawdown >= 30:
            score = 15
            signals.append(f'距高点回调{drawdown:.1f}%')
        elif drawdown < 10:
            score = -15
            signals.append(f'高位(距高点仅{drawdown:.1f}%)')
        
        return {
            'score': score,
            'signals': signals,
            'drawdown': drawdown,
            'high_18m': high_18m
        }
    
    def analyze_monthly_gain(self, code, current_price):
        """分析近1个月涨幅（约20个交易日）"""
        history = self.get_history_data(code)
        
        if not history or len(history) < 20:
            return {
                'score': 0,
                'signals': [],
                'monthly_gain': 0
            }
        
        # 获取20个交易日前的收盘价（近1个月）
        price_1m_ago = float(history[-20]['close'])
        
        # 计算涨幅
        monthly_gain = (current_price - price_1m_ago) / price_1m_ago * 100
        
        score = 0
        signals = []
        
        # 规则6: 近1月涨幅限制（涨太多扣分，避免追高）
        if monthly_gain > 70:
            score = -35
            signals.append(f'近1月暴涨{monthly_gain:.1f}%(追高风险)')
        elif monthly_gain > 50:
            score = -25
            signals.append(f'近1月大涨{monthly_gain:.1f}%(追高风险)')
        elif monthly_gain > 30:
            score = -15
            signals.append(f'近1月涨{monthly_gain:.1f}%(追高风险)')
        elif monthly_gain > 20:
            score = -8
            signals.append(f'近1月涨{monthly_gain:.1f}%(偏高)')
        
        return {
            'score': score,
            'signals': signals,
            'monthly_gain': monthly_gain
        }

if __name__ == '__main__':
    api = SinaHistoryAPI()
    
    # 测试几只股票
    test_stocks = [
        ('600000', 9.60, '浦发银行'),
        ('600036', 38.60, '招商银行'),
        ('600519', 1401.18, '贵州茅台'),
    ]
    
    print("=== 测试历史价格回调分析 ===\n")
    
    for code, price, name in test_stocks:
        result = api.analyze_drawdown(code, price)
        print(f"{name} ({code})")
        print(f"  当前价: ¥{price:.2f}")
        print(f"  18月高点: ¥{result['high_18m']:.2f}")
        print(f"  回调幅度: {result['drawdown']:.2f}%")
        print(f"  得分: {result['score']:+d}")
        print(f"  信号: {result['signals']}\n")
    
    print("=== 测试近1月涨幅分析 ===\n")
    
    for code, price, name in test_stocks:
        result = api.analyze_monthly_gain(code, price)
        print(f"{name} ({code})")
        print(f"  当前价: ¥{price:.2f}")
        print(f"  近1月涨幅: {result['monthly_gain']:+.2f}%")
        print(f"  得分: {result['score']:+d}")
        print(f"  信号: {result['signals']}\n")
