#!/usr/bin/env python3
"""
股票监控器 - 在交易时间内定时推送股票推荐到飞书（使用真实数据）
"""
import time
import json
import requests
import sys
from datetime import datetime

# 导入真实数据筛选器
sys.path.insert(0, '/usr/lib/node_modules/openclaw/skills/stock-assistant/scripts')
from stock_screener_real import StockScreenerReal

class StockMonitor:
    def __init__(self, feishu_webhook):
        self.feishu_webhook = feishu_webhook
        self.screener = StockScreenerReal()
        
        # 交易时间配置（港股通时间）
        self.trading_hours = {
            'morning': ('09:30', '12:00'),
            'afternoon': ('13:00', '16:00')
        }
    
    def is_trading_time(self):
        """判断当前是否在交易时间内"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        weekday = now.weekday()
        
        # 周末不交易
        if weekday >= 5:
            return False
        
        # 判断是否在交易时间段
        morning_start, morning_end = self.trading_hours['morning']
        afternoon_start, afternoon_end = self.trading_hours['afternoon']
        
        if morning_start <= current_time <= morning_end:
            return True
        if afternoon_start <= current_time <= afternoon_end:
            return True
        
        return False
    
    def send_to_feishu(self, recommendations):
        """发送推荐到飞书"""
        if not recommendations:
            content = "⚠️ 当前没有符合条件的股票推荐"
        else:
            content = self.build_message(recommendations)
        
        payload = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        
        try:
            response = requests.post(self.feishu_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"✓ 推送成功 ({len(recommendations)} 只股票)")
                else:
                    print(f"✗ 推送失败: {result}")
            else:
                print(f"✗ 推送失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ 推送异常: {e}")
    
    def build_message(self, recommendations):
        """构建飞书消息内容"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = [
            f"📊 A股推荐 ({now})",
            f"共 {len(recommendations)} 只股票 | 真实数据\n",
            "=" * 40
        ]
        
        for i, stock in enumerate(recommendations[:30], 1):
            lines.append(f"\n{i}. {stock['name']} ({stock['code']})")
            lines.append(f"   💰 价格: ¥{stock['price']:.2f}")
            
            # 涨跌幅用不同emoji
            change = stock['change_pct']
            if change > 0:
                emoji = "📈"
            elif change < 0:
                emoji = "📉"
            else:
                emoji = "➡️"
            lines.append(f"   {emoji} 涨跌: {change:+.2f}%")
            
            lines.append(f"   ⭐ 得分: {stock['score']}")
            if stock['signals']:
                lines.append(f"   🔔 {', '.join(stock['signals'])}")
        
        lines.append("\n" + "=" * 40)
        lines.append("⚠️ 仅供参考，不构成投资建议")
        lines.append("📡 数据来源：新浪财经实时行情")
        
        return '\n'.join(lines)
    
    def run(self):
        """启动监控"""
        print("=" * 60)
        print("股票监控器已启动（真实数据版本）")
        print("=" * 60)
        print(f"飞书 Webhook: {self.feishu_webhook[:50]}...")
        print(f"交易时间: {self.trading_hours['morning'][0]}-{self.trading_hours['morning'][1]}, "
              f"{self.trading_hours['afternoon'][0]}-{self.trading_hours['afternoon'][1]}")
        print(f"数据源: 新浪财经实时接口")
        print("=" * 60)
        
        last_push_time = None
        
        while True:
            now = datetime.now()
            current_time = now.strftime('%H:%M:%S')
            
            if self.is_trading_time():
                # 每分钟推送一次
                if last_push_time is None or (now - last_push_time).seconds >= 60:
                    print(f"\n[{current_time}] 开始筛选股票（真实数据）...")
                    
                    try:
                        recommendations = self.screener.screen_stocks(limit=30)
                        
                        if recommendations:
                            print(f"  筛选完成，推荐 {len(recommendations)} 只股票")
                            self.send_to_feishu(recommendations)
                        else:
                            print(f"  ⚠️ 未找到符合条件的股票")
                            self.send_to_feishu([])
                        
                        last_push_time = now
                    except Exception as e:
                        error_msg = f"✗ 筛选失败: {e}"
                        print(error_msg)
                        
                        # 推送错误信息到飞书
                        error_payload = {
                            "msg_type": "text",
                            "content": {
                                "text": f"⚠️ 股票筛选失败\n时间: {current_time}\n错误: {str(e)[:200]}\n\n请检查数据接口是否正常"
                            }
                        }
                        try:
                            requests.post(self.feishu_webhook, json=error_payload, timeout=10)
                        except:
                            pass
                
                time.sleep(10)  # 每10秒检查一次
            else:
                print(f"[{current_time}] 非交易时间，等待中...")
                time.sleep(60)  # 非交易时间每分钟检查一次

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='股票监控器 - 定时推送到飞书（真实数据）')
    parser.add_argument('--feishu-webhook', required=True, help='飞书机器人 Webhook URL')
    parser.add_argument('--test', action='store_true', help='测试模式（立即推送一次）')
    
    args = parser.parse_args()
    
    monitor = StockMonitor(args.feishu_webhook)
    
    if args.test:
        print("测试模式：立即执行一次筛选和推送（真实数据）...")
        try:
            recommendations = monitor.screener.screen_stocks(limit=30)
            if recommendations:
                print(f"✓ 筛选成功，推荐 {len(recommendations)} 只股票")
                monitor.send_to_feishu(recommendations)
            else:
                print("⚠️ 未找到符合条件的股票")
                monitor.send_to_feishu([])
            print("测试完成")
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            print("\n请检查：")
            print("1. 网络连接是否正常")
            print("2. 新浪财经接口是否可访问")
            print("3. 飞书 Webhook 是否正确")
    else:
        monitor.run()

if __name__ == '__main__':
    main()
