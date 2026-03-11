#!/usr/bin/env python3
"""
东方财富股东人数 API - 获取股东户数变化（带缓存）
"""
import requests
import json
import os
from datetime import datetime, timedelta

class EastmoneyShareholderAPI:
    def __init__(self, cache_dir='/root/.openclaw/workspace/cache'):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'shareholder_cache.json')
        self.cache_days = 7  # 缓存7天
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 加载缓存
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def _is_cache_valid(self, code):
        """检查缓存是否有效（7天内）"""
        if code not in self.cache:
            return False
        
        cache_time = datetime.fromisoformat(self.cache[code]['cache_time'])
        now = datetime.now()
        
        return (now - cache_time).days < self.cache_days
    
    def get_shareholder_data(self, code, force_refresh=False):
        """获取股东人数数据（带缓存）"""
        # 检查缓存
        if not force_refresh and self._is_cache_valid(code):
            return self.cache[code]['data']
        
        # 从接口获取
        prefix = 'SH' if code.startswith('6') else 'SZ'
        url = f'http://emweb.securities.eastmoney.com/PC_HSF10/ShareholderResearch/PageAjax?code={prefix}{code}'
        
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                gdrs = data.get('gdrs', [])
                
                if gdrs:
                    # 更新缓存
                    self.cache[code] = {
                        'data': gdrs,
                        'cache_time': datetime.now().isoformat()
                    }
                    self._save_cache()
                    
                    return gdrs
        except Exception as e:
            pass
        
        return []
    
    def analyze_shareholder_change(self, code):
        """分析股东人数变化"""
        data = self.get_shareholder_data(code)
        
        if not data or len(data) < 2:
            return {
                'score': 0,
                'signals': [],
                'trend': 'unknown'
            }
        
        score = 0
        signals = []
        
        # 获取最近3期数据
        recent_3 = data[:3]
        
        # 提取环比变化率
        changes = [item['TOTAL_NUM_RATIO'] for item in recent_3]
        
        # 规则5.1: 连续减少（筹码集中）
        if len(changes) >= 3 and all(c < 0 for c in changes):
            score += 15
            signals.append('股东连续3期减少')
            trend = 'concentrating'
        elif len(changes) >= 2 and all(c < 0 for c in changes[:2]):
            score += 10
            signals.append('股东连续2期减少')
            trend = 'concentrating'
        elif changes[0] < 0:
            trend = 'concentrating'
        else:
            trend = 'dispersing'
        
        # 规则5.2: 单期大幅减少
        if changes[0] < -10:
            score += 5
            signals.append(f'股东大幅减少{abs(changes[0]):.1f}%')
        
        # 规则5.3: 连续增加（筹码分散，警惕）
        if len(changes) >= 2 and all(c > 0 for c in changes[:2]):
            score -= 5
            signals.append('股东连续增加(警惕)')
        
        # 规则5.4: 单期大幅增加
        if changes[0] > 20:
            score -= 10
            signals.append(f'股东大幅增加{changes[0]:.1f}%(警惕)')
        
        # 添加最新股东户数信息
        latest = recent_3[0]
        holder_num = latest['HOLDER_TOTAL_NUM']
        change_ratio = latest['TOTAL_NUM_RATIO']
        
        return {
            'score': score,
            'signals': signals,
            'trend': trend,
            'holder_num': holder_num,
            'change_ratio': change_ratio,
            'latest_date': latest['END_DATE'][:10]
        }

if __name__ == '__main__':
    api = EastmoneyShareholderAPI()
    
    # 测试
    test_stocks = [
        ('600000', '浦发银行'),
        ('600036', '招商银行'),
        ('000001', '平安银行'),
    ]
    
    print("=== 测试股东人数分析（带缓存）===\n")
    
    for code, name in test_stocks:
        print(f"{name} ({code})")
        
        # 第一次调用（从接口获取）
        result = api.analyze_shareholder_change(code)
        
        print(f"  最新报告期: {result['latest_date']}")
        print(f"  股东户数: {result['holder_num']:,}")
        print(f"  环比变化: {result['change_ratio']:+.2f}%")
        print(f"  趋势: {result['trend']}")
        print(f"  得分: {result['score']:+d}")
        print(f"  信号: {result['signals']}")
        print()
    
    # 测试缓存
    print("\n=== 测试缓存（第二次调用应该很快）===\n")
    import time
    start = time.time()
    result = api.analyze_shareholder_change('600000')
    elapsed = time.time() - start
    print(f"浦发银行 (600000) - 耗时: {elapsed:.3f}秒")
    print(f"  使用缓存: {elapsed < 0.1}")
