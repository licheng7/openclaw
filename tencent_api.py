#!/usr/bin/env python3
"""
腾讯股票 API - 获取实时行情和市值
"""
import requests
import re

class TencentStockAPI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://finance.qq.com',
        }
    
    def get_stock_info(self, code):
        """获取单只股票信息（包含市值）"""
        # 判断市场
        prefix = 'sh' if code.startswith('6') else 'sz'
        url = f'http://qt.gtimg.cn/q={prefix}{code}'
        
        try:
            r = requests.get(url, headers=self.headers, timeout=5)
            if r.status_code == 200:
                # 解析数据：v_sh600000="字段1~字段2~..."
                data = r.text.split('"')[1].split('~')
                
                if len(data) > 45:
                    return {
                        'code': code,
                        'name': data[1],
                        'price': float(data[3]),
                        'change_pct': float(data[32]),  # 涨跌幅
                        'volume': int(float(data[6])),  # 成交量（手）
                        'market_cap': float(data[45]),  # 总市值（亿）
                    }
        except Exception as e:
            print(f"获取 {code} 失败: {e}")
        
        return None

if __name__ == '__main__':
    api = TencentStockAPI()
    
    # 测试
    stock = api.get_stock_info('600000')
    if stock:
        print(f"{stock['name']} ({stock['code']})")
        print(f"  价格: ¥{stock['price']:.2f}")
        print(f"  涨跌幅: {stock['change_pct']:+.2f}%")
        print(f"  市值: {stock['market_cap']:.2f}亿")
