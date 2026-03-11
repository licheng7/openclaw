#!/usr/bin/env python3
"""
成交额分析 - 底部放量突破检测
"""
from sina_history_api import SinaHistoryAPI

class VolumeAnalyzer:
    def __init__(self):
        self.history_api = SinaHistoryAPI()
    
    def analyze_bottom_breakout(self, code, current_price):
        """分析底部放量突破"""
        history = self.history_api.get_history_data(code)
        
        if not history or len(history) < 130:  # 至少需要6个月数据
            return {
                'score': 0,
                'signals': []
            }
        
        # 获取近6个月数据（约130个交易日）
        recent_6m = history[-130:]
        
        # 获取近18个月数据（约360个交易日）
        recent_18m = history[-360:] if len(history) >= 360 else history
        
        # 1. 判断是否在底部
        # 方法1：相比18个月高点回调>35%
        high_18m = max(float(item['high']) for item in recent_18m)
        drawdown_18m = (high_18m - current_price) / high_18m * 100
        
        # 方法2：相比6个月最低点+15%以内
        low_6m = min(float(item['low']) for item in recent_6m)
        above_low_6m = (current_price - low_6m) / low_6m * 100
        
        is_bottom = drawdown_18m > 35 or above_low_6m < 15
        
        if not is_bottom:
            return {
                'score': 0,
                'signals': []
            }
        
        # 2. 分析成交额（价格*成交量）
        # 计算每天的成交额（万元）
        volumes = []
        for item in recent_6m:
            close = float(item['close'])
            volume = float(item['volume'])  # 成交量（股）
            amount = close * volume / 10000  # 成交额（万元）
            volumes.append(amount)
        
        # 找出6个月内成交额最低点
        min_volume = min(volumes)
        
        # 3. 检测连续萎缩（>5天）
        # 最近10天的成交额
        recent_10_volumes = volumes[-10:]
        
        # 统计有多少天在低位（最低点+30%以内）
        low_volume_threshold = min_volume * 1.30
        low_volume_days = sum(1 for v in recent_10_volumes if v <= low_volume_threshold)
        
        # 需要连续5天以上在低位
        if low_volume_days < 5:
            return {
                'score': 0,
                'signals': []
            }
        
        score = 15
        signals = ['底部缩量筑底']
        
        # 4. 检测放量突破
        # 找出最近10天的最低成交额
        recent_min_volume = min(recent_10_volumes)
        
        # 检查最近2天是否放量（相比最低点+100%以上）
        recent_2_volumes = volumes[-2:]
        
        has_breakout = False
        for v in recent_2_volumes:
            if v > recent_min_volume * 2.0:  # 放量100%以上
                has_breakout = True
                break
        
        if has_breakout:
            score += 30
            signals.append('底部放量突破')
        
        return {
            'score': score,
            'signals': signals,
            'is_bottom': is_bottom,
            'low_volume_days': low_volume_days,
            'has_breakout': has_breakout
        }

if __name__ == '__main__':
    analyzer = VolumeAnalyzer()
    
    # 测试
    test_stocks = [
        ('600000', 9.60, '浦发银行'),
        ('600036', 38.60, '招商银行'),
    ]
    
    print("=== 测试底部放量突破分析 ===\n")
    
    for code, price, name in test_stocks:
        print(f"{name} ({code})")
        
        result = analyzer.analyze_bottom_breakout(code, price)
        
        print(f"  是否在底部: {result.get('is_bottom', False)}")
        print(f"  低位缩量天数: {result.get('low_volume_days', 0)}")
        print(f"  是否放量突破: {result.get('has_breakout', False)}")
        print(f"  得分: {result['score']:+d}")
        print(f"  信号: {result['signals']}")
        print()
