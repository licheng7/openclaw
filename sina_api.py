#!/usr/bin/env python3
"""
直接使用新浪接口获取股票数据（绕过 AKShare）
"""
import requests
import re
import json

class SinaStockAPI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://finance.sina.com.cn',
        }
    
    def get_stock_realtime(self, code):
        """获取单只股票实时数据"""
        # 转换股票代码格式
        if code.startswith('6'):
            symbol = f'sh{code}'
        else:
            symbol = f'sz{code}'
        
        url = f'http://hq.sinajs.cn/list={symbol}'
        
        try:
            r = requests.get(url, headers=self.headers, timeout=5)
            if r.status_code == 200:
                # 解析返回数据
                match = re.search(r'"(.+)"', r.text)
                if match:
                    data = match.group(1).split(',')
                    if len(data) >= 32:
                        return {
                            'code': code,
                            'name': data[0],
                            'price': float(data[3]),
                            'change_pct': ((float(data[3]) - float(data[2])) / float(data[2]) * 100) if float(data[2]) > 0 else 0,
                            'volume': int(data[8]),
                            'amount': float(data[9]),
                        }
        except Exception as e:
            print(f"获取 {code} 失败: {e}")
        
        return None
    
    def get_all_stocks(self):
        """获取所有A股列表（简化版）"""
        # 主板股票代码范围
        stocks = []
        
        # 上海主板 600000-603999
        print("获取上海主板股票...")
        for i in range(600000, 600100):  # 先测试100只
            code = f'{i:06d}'
            stock = self.get_stock_realtime(code)
            if stock and stock['name']:
                stocks.append(stock)
                if len(stocks) % 10 == 0:
                    print(f"  已获取 {len(stocks)} 只...")
        
        return stocks

def main():
    print("=== 使用新浪接口直接获取股票数据 ===\n")
    
    api = SinaStockAPI()
    
    # 测试单只股票
    print("1. 测试单只股票（浦发银行 600000）...")
    stock = api.get_stock_realtime('600000')
    if stock:
        print(f"  ✓ {stock['name']} ({stock['code']})")
        print(f"    价格: ¥{stock['price']:.2f}")
        print(f"    涨跌幅: {stock['change_pct']:+.2f}%")
    
    # 获取多只股票
    print("\n2. 批量获取股票数据...")
    stocks = api.get_all_stocks()
    
    print(f"\n✓ 共获取 {len(stocks)} 只股票")
    
    # 保存结果
    with open('stocks_sina.json', 'w', encoding='utf-8') as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    print("结果已保存到 stocks_sina.json")

if __name__ == '__main__':
    main()
