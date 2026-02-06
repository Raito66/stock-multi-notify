# 台積電價格監控 - 使用 LINE Messaging API 推播通知（長期穩定版）
# 範圍會根據當前股價動態調整，適合台積電高價股特性

import requests
import time
from datetime import datetime, timedelta

# ======================== 設定區塊 ========================

# 從檔案讀取 token
try:
    with open("channelaccesstoken.txt", "r", encoding="utf-8") as f:
        CHANNEL_ACCESS_TOKEN = f.read().strip()
    print("成功從 channelaccesstoken.txt 讀取 token")
except FileNotFoundError:
    print("錯誤：找不到 channelaccesstoken.txt 檔案，請確認檔案存在")
    exit(1)
except Exception as e:
    print(f"讀取 token 失敗：{e}")
    exit(1)

USER_ID = "U21b54887e18940a7a37ee8c7b6dcb286"

# 動態區間設定（最適合台積電的推薦值）
PERCENT_RANGE = 2.0     # ±2%（可調整為 1.5 ~ 2.5，建議從 2.0 開始）
MIN_RANGE = 60          # 最小區間寬度（避免股價低時區間過小）

# 檢查間隔（秒）
CHECK_INTERVAL = 300

TSMC_SYMBOL = "2330"
API_URL = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{TSMC_SYMBOL}.tw&json=1&delay=0"

# ==========================================================

def is_trading_time():
    """判斷現在是否為台股交易時間（09:00 ~ 13:30）"""
    now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:  # 週六、週日
        return False
    
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=13, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close

def send_line_push(message):
    """發送 LINE 推播訊息"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            print("LINE 推播訊息已發送")
        else:
            print(f"推播失敗：{r.status_code} - {r.text}")
    except Exception as e:
        print(f"發送推播時發生錯誤：{e}")

def get_tsmc_price(max_retries=3):
    """從證交所 API 取得台積電最新價格，自動重試"""
    for attempt in range(max_retries):
        try:
            r = requests.get(API_URL, timeout=10)
            data = r.json()
            if 'msgArray' in data and len(data['msgArray']) > 0:
                price_str = data['msgArray'][0].get('z', '-')
                if price_str != '-' and price_str != '':
                    return float(price_str)
            print(f"嘗試 {attempt+1}/{max_retries}：無最新成交價")
        except Exception as e:
            print(f"嘗試 {attempt+1}/{max_retries} 失敗：{e}")
        time.sleep(2)
    print("連續多次無法取得最新股價")
    return None

def main():
    print("台積電價格監控程式啟動（動態區間版 - 適合台積電）")
    print(f"區間調整規則：當前股價 ± {PERCENT_RANGE}%（最小寬度 {MIN_RANGE} 元）")
    print(f"檢查間隔：{CHECK_INTERVAL} 秒")
    print("按 Ctrl+C 結束程式\n")

    # 啟動測試訊息
    startup_msg = (
        "台積電監控程式已啟動\n"
        f"動態區間設定：±{PERCENT_RANGE}%（最小{MIN_RANGE}元）\n"
        "開始監控... 午休時會顯示最後價格或等待開盤"
    )
    send_line_push(startup_msg)

    already_notified = False
    last_price = None  # 記住最後取得的價格

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price = get_tsmc_price()

        if price is None:
            if is_trading_time():
                if last_price is not None:
                    print(f"[{now}] 交易時間內暫無最新成交（午休或暫停），最後價格：{last_price:.2f} 元")
                else:
                    print(f"[{now}] 交易時間內無法取得股價，稍後重試...")
            else:
                if last_price is not None:
                    print(f"[{now}] 非交易時間，最後價格：{last_price:.2f} 元，等待開盤...")
                else:
                    print(f"[{now}] 非交易時間，等待開盤...")
        else:
            last_price = price  # 更新最後價格
            print(f"[{now}] 台積電現價：{price:.2f} 元")

            # 動態計算區間
            offset = price * (PERCENT_RANGE / 100)
            dynamic_low = price - offset
            dynamic_high = price + offset

            # 確保區間不會太小
            if dynamic_high - dynamic_low < MIN_RANGE:
                dynamic_low = price - MIN_RANGE / 2
                dynamic_high = price + MIN_RANGE / 2

            print(f"當前動態提醒區間：{dynamic_low:.2f} ~ {dynamic_high:.2f} 元")

            in_range = dynamic_low <= price <= dynamic_high

            if in_range and not already_notified:
                position = ""
                if price <= dynamic_low + (dynamic_high - dynamic_low) * 0.2:
                    position = "（接近下緣，較適合買入）"
                elif price >= dynamic_high - (dynamic_high - dynamic_low) * 0.2:
                    position = "（接近上緣，建議觀望）"

                msg = (
                    f"【台積電買入提醒】\n"
                    f"現價：{price:.2f} 元\n"
                    f"進入動態區間：{dynamic_low:.2f} ~ {dynamic_high:.2f} 元\n"
                    f"{position}\n"
                    f"時間：{now}"
                )
                send_line_push(msg)
                print("已發送買入提醒！")
                already_notified = True
            elif not in_range:
                already_notified = False

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()