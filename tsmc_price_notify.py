# 台積電價格監控 - 使用 Google Sheets 永久儲存
# 資料來源：FinMind（付費版 Backer / Pro 已解鎖即時分鐘資料）
# 支援盤中即時推播 + 盤後存收盤價 + 同時顯示最新成交與收盤價

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import pandas as pd

from FinMind.data import DataLoader
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time

# ======================== 環境變數 ========================

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
FINMIND_TOKEN = os.getenv("FINMIND_TOKEN")

if not all([CHANNEL_ACCESS_TOKEN, USER_ID, GOOGLE_SHEETS_CREDENTIALS, GOOGLE_SHEET_ID, FINMIND_TOKEN]):
    raise RuntimeError("缺少必要的環境變數")

# ======================== 參數設定 ========================

TSMC_STOCK_ID = "2330"
HISTORY_DAYS = 365
SHEET_NAME = "Sheet1"

# ==========================================================

def get_sheets_service():
    try:
        creds_json = GOOGLE_SHEETS_CREDENTIALS
        try:
            credentials_info = json.loads(creds_json)
        except json.JSONDecodeError:
            creds_json = creds_json.encode().decode('unicode_escape')
            credentials_info = json.loads(creds_json)

        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=credentials)
        print("✅ Google Sheets 連線成功")
        return service
    except Exception as e:
        print(f"⚠️ Google Sheets 連線失敗：{e}")
        return None


def send_line_push(message: str):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}],
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"LINE 推播失敗：{r.status_code} - {r.text}")
    except Exception as e:
        print(f"LINE 推播錯誤：{e}")


def get_latest_minute_price(dl) -> Optional[Dict]:
    """
    取得台積電今日最新的分鐘級成交價（盤中即時，盤後為最後成交）
    使用 FinMind 付費版支援的 TaiwanStockMinute 資料集
    """
    try:
        today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        print(f"正在查詢分鐘資料 → 日期：{today}，股票：{TSMC_STOCK_ID}")

        df = dl.get_data(
            dataset="TaiwanStockMinute",
            data_id=TSMC_STOCK_ID,
            start_date=today,
            end_date=today
        )

        print(f"取得資料筆數：{len(df) if not df.empty else 0}")

        if df.empty:
            print("分鐘資料為空（可能尚未開盤、盤後未更新、或資料延遲）")
            return None

        # 檢查必要欄位
        required_cols = ['date', 'close']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            print(f"資料欄位異常，缺少：{missing}")
            print("實際欄位：", list(df.columns))
            return None

        df = df.sort_values('date')
        latest = df.iloc[-1]

        price = float(latest['close'])
        time_str = latest['date']

        print(f"成功取得最新分鐘資料 - 時間：{time_str}，成交價：{price:.2f}")

        return {
            "price": price,
            "time": time_str,
        }

    except Exception as e:
        print(f"取得分鐘價失敗：{str(e)}")
        print("錯誤類型：", type(e).__name__)
        return None


def get_today_close(dl, date_str: str) -> Optional[float]:
    """盤後取得今日收盤價（用於存檔）"""
    try:
        df = dl.taiwan_stock_daily(
            stock_id=TSMC_STOCK_ID,
            start_date=date_str,
            end_date=date_str
        )
        if not df.empty:
            close_price = float(df.iloc[0]['close'])
            print(f"取得今日收盤價：{close_price:.2f}")
            return close_price
        print("今日日K資料為空")
        return None
    except Exception as e:
        print(f"取得今日收盤價失敗：{e}")
        return None


def get_yesterday_close(dl) -> Optional[float]:
    """取得前一交易日收盤價"""
    try:
        now = datetime.now(timezone(timedelta(hours=8)))
        start = (now - timedelta(days=10)).strftime("%Y-%m-%d")
        end = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        df = dl.taiwan_stock_daily(
            stock_id=TSMC_STOCK_ID,
            start_date=start,
            end_date=end
        )
        if not df.empty:
            df = df.sort_values('date')
            close_price = float(df.iloc[-1]['close'])
            print(f"前日收盤價：{close_price:.2f} ({df.iloc[-1]['date']})")
            return close_price
        print("無法取得前日收盤價")
        return None
    except Exception as e:
        print(f"取得昨收失敗：{e}")
        return None


def get_tsmc_data(dl) -> Optional[Dict]:
    taipei_now = datetime.now(timezone(timedelta(hours=8)))
    today_str = taipei_now.strftime("%Y-%m-%d")

    # 盤中 / 盤後都先用分鐘資料取最新價
    minute_data = get_latest_minute_price(dl)
    if not minute_data:
        print("無法取得分鐘資料，無法繼續")
        return None

    yesterday_close = get_yesterday_close(dl)
    if yesterday_close is None:
        yesterday_close = minute_data["price"]

    result = {
        "latest_price": minute_data["price"],
        "latest_time": minute_data["time"],
        "yesterday_close": yesterday_close,
        "date": today_str,
        "is_after_close": taipei_now.hour > 13 or (taipei_now.hour == 13 and taipei_now.minute >= 30)
    }

    # 盤後額外取正式收盤價（用於存檔）
    if result["is_after_close"]:
        today_close = get_today_close(dl, today_str)
        if today_close is not None:
            result["close_price"] = today_close

    return result


def load_history_from_sheets(service) -> List[Dict]:
    if not service:
        return []
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{SHEET_NAME}!A2:F'
        ).execute()
        values = result.get('values', [])
        history = []
        for row in values:
            if len(row) >= 2:
                history.append({
                    'date': row[0],
                    'price': float(row[1]),
                    'timestamp': row[5] if len(row) > 5 else row[0]
                })
        print(f"載入歷史資料：{len(history)} 筆")
        return history
    except Exception as e:
        print(f"讀取 Sheets 失敗：{e}")
        return []


def save_to_sheets(service, date: str, price: float, ma5: Optional[float],
                   ma20: Optional[float], ma60: Optional[float], timestamp: str) -> bool:
    if not service:
        return False
    try:
        values = [[date, price, f"{ma5:.2f}" if ma5 else "", f"{ma20:.2f}" if ma20 else "", f"{ma60:.2f}" if ma60 else "", timestamp]]
        body = {'values': values}
        service.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{SHEET_NAME}!A2',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        print(f"寫入 Sheets 成功：{date} - {price:.2f}")
        return True
    except Exception as e:
        print(f"寫入 Sheets 失敗：{e}")
        return False


def cleanup_old_data(service, keep_days: int = 365):
    if not service:
        return
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{SHEET_NAME}!A2:F'
        ).execute()
        values = result.get('values', [])
        if len(values) <= keep_days:
            return
        rows_to_delete = len(values) - keep_days
        request = {
            'requests': [{
                'deleteDimension': {
                    'range': {
                        'sheetId': 0,
                        'dimension': 'ROWS',
                        'startIndex': 1,
                        'endIndex': 1 + rows_to_delete
                    }
                }
            }]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=GOOGLE_SHEET_ID,
            body=request
        ).execute()
        print(f"清理舊資料：刪除 {rows_to_delete} 筆")
    except Exception as e:
        print(f"清理舊資料失敗：{e}")


def calculate_ma(history: List[Dict], days: int) -> Optional[float]:
    if len(history) < days:
        return None
    prices = [h['price'] for h in history[-days:]]
    return sum(prices) / len(prices)


def get_smart_suggestion(price: float, history: List[Dict], ma5, ma20, ma60) -> List[str]:
    suggestions = ["技術分析功能保留中..."]  # 請貼上你原本的完整建議邏輯
    return suggestions


# ==================== 主程式 ====================

def main():
    taipei_tz = timezone(timedelta(hours=8))
    now_dt = datetime.now(timezone.utc).astimezone(taipei_tz)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    today = now_dt.strftime("%Y-%m-%d")

    print(f"🕐 台灣時間：{now_str}")
    print(f"FinMind 版本：{DataLoader.__module__.split('.')[0]}")  # 顯示版本確認

    service = get_sheets_service()
    if not service:
        send_line_push(f"【台積電監控】\n{now_str}\n⚠️ Google Sheets 連線失敗")
        return

    dl = DataLoader()
    try:
        dl.login_by_token(api_token=FINMIND_TOKEN)
        print("FinMind 登入成功（付費版已啟用）")
    except Exception as e:
        print(f"FinMind 登入失敗：{e}")
        send_line_push(f"【台積電監控】\nFinMind 登入失敗：{str(e)}")
        return

    stock_data = get_tsmc_data(dl)
    if stock_data is None:
        send_line_push(f"【台積電監控】\n{now_str}\n⚠️ 無法取得股價資料（可能市場未開盤或資料延遲）")
        return

    latest_price = stock_data["latest_price"]
    yesterday_close = stock_data["yesterday_close"]
    change_amount = latest_price - yesterday_close
    change_percent = (change_amount / yesterday_close * 100) if yesterday_close != 0 else 0

    history = load_history_from_sheets(service)
    last_date = history[-1].get('date') if history else None

    is_after_close = stock_data["is_after_close"]
    saved = False
    ma_price = latest_price

    if is_after_close and last_date != today:
        close_price = stock_data.get("close_price")
        if close_price is not None:
            ma_price = close_price
            history.append({'date': today, 'price': close_price, 'timestamp': now_str})
            ma5 = calculate_ma(history, 5)
            ma20 = calculate_ma(history, 20)
            ma60 = calculate_ma(history, 60)
            save_to_sheets(service, today, close_price, ma5, ma20, ma60, now_str)
            cleanup_old_data(service, HISTORY_DAYS)
            saved = True
        else:
            print("盤後但無法取得今日收盤價，暫不存檔")
    else:
        ma5 = calculate_ma(history, 5)
        ma20 = calculate_ma(history, 20)
        ma60 = calculate_ma(history, 60)

    suggestions = get_smart_suggestion(ma_price, history, ma5, ma20, ma60)

    # ==================== 訊息組合 ====================

    msg_parts = []
    title = "【台積電盤中快訊】" if not is_after_close else "【台積電價格監控】"
    msg_parts.append(title)
    msg_parts.append(f"時間：{now_str}")
    msg_parts.append("━━━━━━━━━━━━━━")

    if "latest_time" in stock_data:
        msg_parts.append(f"最新成交：{stock_data['latest_time']}")

    msg_parts.append(f"現價：{latest_price:.2f} 元")

    if is_after_close and "close_price" in stock_data:
        msg_parts.append(f"今日收盤：{stock_data['close_price']:.2f} 元")

    msg_parts.append(f"昨收：{yesterday_close:.2f} 元")
    msg_parts.append(f"漲跌：{change_amount:+.2f} 元（{change_percent:+.2f}%）")

    if ma5 or ma20 or ma60:
        msg_parts.append("━━━━━━━━━━━━━━")
        msg_parts.append("📈 技術分析")
        if ma5:
            icon = "✅" if ma_price > ma5 else "⚠️"
            msg_parts.append(f"5日均線：{ma5:.2f} 元 {icon}")
        if ma20:
            icon = "✅" if ma_price > ma20 else "⚠️"
            msg_parts.append(f"20日均線：{ma20:.2f} 元 {icon}")
        if ma60:
            icon = "✅" if ma_price > ma60 else "⚠️"
            msg_parts.append(f"60日均線：{ma60:.2f} 元 {icon}")

    msg_parts.append("━━━━━━━━━━━━━━")
    msg_parts.extend(suggestions)

    msg_parts.append("━━━━━━━━━━━━━━")
    msg_parts.append(f"歷史資料：{len(history)}/{HISTORY_DAYS} 天")
    msg_parts.append("※ 資料來源：FinMind（付費版）")

    send_line_push("\n".join(msg_parts))

    print("推播完成")
    if saved:
        print(f"已存入今日收盤價：{stock_data['close_price']:.2f}")
    else:
        print("本次未存入新資料（盤中或已存過）")


if __name__ == "__main__":
    main()