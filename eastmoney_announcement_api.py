#!/usr/bin/env python3
"""
东方财富公告 API - 获取重大风险公告（带缓存）
"""
import requests
import json
import os
from datetime import datetime, timedelta

class EastmoneyAnnouncementAPI:
    def __init__(self, cache_dir='/root/.openclaw/workspace/cache'):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'announcement_cache.json')
        self.cache_days = 7  # 缓存7天
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 加载缓存
        self.cache = self._load_cache()
        
        # 重大风险关键词（排除误判）
        self.risk_keywords = [
            '风险提示', '风险警示', '处罚', '立案', '调查',
            '违规', '诉讼', '仲裁', '重大亏损', '债务违约',
            '退市风险', 'ST', '*ST', '暂停上市', '终止上市',
            '异常波动', '停牌', '重大事项停牌', '业绩预亏',
            '业绩大幅下滑', '商誉减值', '资产减值', '担保风险'
        ]
        
        # 排除关键词（避免误判）
        self.exclude_keywords = [
            '风险官', '风险管理', '风险控制', '风险委员会',
            '首席风险官', '风险总监'
        ]
    
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
    
    def get_announcements(self, code, force_refresh=False):
        """获取公告数据（带缓存）"""
        # 检查缓存
        if not force_refresh and self._is_cache_valid(code):
            return self.cache[code]['data']
        
        # 从接口获取
        url = f'http://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1&page_size=50&page_index=1&ann_type=SHA&client_source=web&stock_list={code}&f_node=0'
        
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and 'list' in data['data']:
                    announcements = data['data']['list']
                    
                    # 更新缓存
                    self.cache[code] = {
                        'data': announcements,
                        'cache_time': datetime.now().isoformat()
                    }
                    self._save_cache()
                    
                    return announcements
        except Exception as e:
            pass
        
        return []
    
    def _is_risk_announcement(self, title):
        """判断是否为风险公告"""
        # 先检查排除关键词
        if any(keyword in title for keyword in self.exclude_keywords):
            return False
        
        # 再检查风险关键词
        return any(keyword in title for keyword in self.risk_keywords)
    
    def analyze_risk_announcements(self, code):
        """分析重大风险公告"""
        announcements = self.get_announcements(code)
        
        if not announcements:
            return {
                'score': 0,
                'signals': [],
                'risk_count': 0
            }
        
        now = datetime.now()
        risk_announcements = []
        
        # 分析最近3个月的公告
        for item in announcements:
            title = item.get('title', '')
            date_str = item.get('notice_date', '')
            
            # 解析日期
            try:
                ann_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except:
                continue
            
            # 只看最近3个月
            days_ago = (now - ann_date).days
            if days_ago > 90:
                continue
            
            # 判断是否为风险公告
            if self._is_risk_announcement(title):
                risk_announcements.append({
                    'title': title,
                    'date': date_str,
                    'days_ago': days_ago
                })
        
        # 计算得分
        score = 0
        signals = []
        
        if not risk_announcements:
            return {
                'score': 0,
                'signals': [],
                'risk_count': 0
            }
        
        # 找出最近的风险公告
        latest_risk = min(risk_announcements, key=lambda x: x['days_ago'])
        days_ago = latest_risk['days_ago']
        
        # 规则7: 重大风险公告评分（分阶段递减，不叠加）
        if days_ago <= 7:
            score = -50
            signals.append(f'近1周风险公告')
        elif days_ago <= 14:
            score = -30
            signals.append(f'近2周风险公告')
        elif days_ago <= 30:
            score = -15
            signals.append(f'近1月风险公告')
        elif days_ago <= 90:
            score = -5
            signals.append(f'近3月风险公告')
        
        return {
            'score': score,
            'signals': signals,
            'risk_count': len(risk_announcements),
            'latest_risk': latest_risk
        }

if __name__ == '__main__':
    api = EastmoneyAnnouncementAPI()
    
    # 测试
    test_stocks = [
        ('600000', '浦发银行'),
        ('600036', '招商银行'),
    ]
    
    print("=== 测试风险公告分析（带缓存）===\n")
    
    for code, name in test_stocks:
        print(f"{name} ({code})")
        
        result = api.analyze_risk_announcements(code)
        
        print(f"  风险公告数量: {result['risk_count']}")
        print(f"  得分: {result['score']:+d}")
        print(f"  信号: {result['signals']}")
        
        if result.get('latest_risk'):
            latest = result['latest_risk']
            print(f"  最近风险公告: {latest['title'][:60]}")
            print(f"  发布时间: {latest['date']} ({latest['days_ago']}天前)")
        
        print()
