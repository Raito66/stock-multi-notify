# 台積電價格監控 - 使用 LINE Messaging API 推播通知
# 策略：多均線分析 + GitHub Gist 永久儲存

import requests
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ======================== 環境變數 ========================

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN 未設定")
if not USER_ID:
    raise RuntimeError("LINE_USER_ID 未設定")

# ======================== 參數設定 ========================

TSMC_SYMBOL = "2330"
API_URL = (
    f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    f"?ex_ch=tse_{TSMC_SYMBOL}.tw&json=1&delay=0"
)

# 歷史資料設定
HISTORY_DAYS = 60  # 保留 60 天資料
GIST_FILENAME = "tsmc_price_history.json"
GIST_DESCRIPTION = "台積電股價歷史資料（自動更新）"

# GitHub API
GITHUB_API = "https://api.github.com"

# 本地備援路徑
LOCAL_BACKUP = "/tmp/tsmc_history.json"

# ==========================================================

def send_line_push(message: str):
    """發送 LINE 推播訊息"""
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
            print(f"⚠️ LINE 推播失敗：{r.status_code} - {r.text}")
    except Exception as e:
        print(f"⚠️ LINE 推播錯誤：{e}")

def get_tsmc_data(max_retries=3) -> Optional[Dict]:
    """取得台積電股價資訊（現價 + 昨收）"""
    for _ in range(max_retries):
        try:
            r = requests.get(API_URL, timeout=10)
            data = r.json()
            if data.get("msgArray"):
                stock_data = data["msgArray"][0]
                
                # z: 最新成交價, y: 昨收價
                price_str = stock_data.get("z")
                yesterday_str = stock_data.get("y")
                
                if price_str and price_str != "-" and yesterday_str and yesterday_str != "-":
                    return {
                        "price": float(price_str),
                        "yesterday_close": float(yesterday_str)
                    }
        except Exception as e:
            print(f"⚠️ API 請求失敗：{e}")
    return None

# ==================== GitHub Gist 操作 ====================

def get_gist_id() -> Optional[str]:
    """取得現有的 Gist ID"""
    if not GITHUB_TOKEN:
        return None
    
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        r = requests.get(f"{GITHUB_API}/gists", headers=headers, timeout=10)
        
        if r.status_code == 200:
            gists = r.json()
            for gist in gists:
                if GIST_FILENAME in gist.get("files", {}):
                    print(f"✅ 找到現有 Gist：{gist['id']}")
                    return gist["id"]
        elif r.status_code == 401:
            print("⚠️ GitHub Token 無效或已過期")
            send_line_push("⚠️【系統通知】\nGitHub Token 已過期\n請更新 Render 環境變數中的 GITHUB_TOKEN")
        else:
            print(f"⚠️ 取得 Gist 列表失敗：{r.status_code}")
    except Exception as e:
        print(f"⚠️ Gist 操作錯誤：{e}")
    
    return None

def create_gist(content: str) -> Optional[str]:
    """建立新的 Gist"""
    if not GITHUB_TOKEN:
        return None
    
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "description": GIST_DESCRIPTION,
            "public": False,
            "files": {
                GIST_FILENAME: {
                    "content": content
                }
            }
        }
        
        r = requests.post(f"{GITHUB_API}/gists", headers=headers, json=payload, timeout=10)
        
        if r.status_code == 201:
            gist_id = r.json()["id"]
            print(f"✅ 建立新 Gist���{gist_id}")
            return gist_id
        else:
            print(f"⚠️ 建立 Gist 失敗：{r.status_code} - {r.text}")
    except Exception as e:
        print(f"⚠️ 建立 Gist 錯誤：{e}")
    
    return None

def update_gist(gist_id: str, content: str) -> bool:
    """更新 Gist 內容"""
    if not GITHUB_TOKEN:
        return False
    
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "files": {
                GIST_FILENAME: {
                    "content": content
                }
            }
        }
        
        r = requests.patch(f"{GITHUB_API}/gists/{gist_id}", headers=headers, json=payload, timeout=10)
        
        if r.status_code == 200:
            return True
        else:
            print(f"⚠️ 更新 Gist 失敗：{r.status_code}")
    except Exception as e:
        print(f"⚠️ 更新 Gist 錯誤：{e}")
    
    return False

def read_gist(gist_id: str) -> Optional[str]:
    """讀取 Gist 內容"""
    if not GITHUB_TOKEN:
        return None
    
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        r = requests.get(f"{GITHUB_API}/gists/{gist_id}", headers=headers, timeout=10)
        
        if r.status_code == 200:
            gist = r.json()
            if GIST_FILENAME in gist["files"]:
                return gist["files"][GIST_FILENAME]["content"]
        else:
            print(f"⚠️ 讀取 Gist 失敗：{r.status_code}")
    except Exception as e:
        print(f"⚠️ 讀取 Gist 錯誤：{e}")
    
    return None

# ==================== 資料儲存管理 ====================

def load_history() -> List[Dict]:
    """載入歷史價格資料（優先從 Gist，降級到本地）"""
    history = []
    
    # 1. 嘗試從 GitHub Gist 載入
    if GITHUB_TOKEN:
        print("🔍 從 GitHub Gist 載入資料...")
        gist_id = get_gist_id()
        if gist_id:
            content = read_gist(gist_id)
            if content:
                try:
                    history = json.loads(content)
                    print(f"✅ 從 Gist 載入 {len(history)} 筆資料")
                    return history
                except json.JSONDecodeError:
                    print("⚠️ Gist 資料格式錯誤")
    
    # 2. 降級：從本地備援載入
    try:
        if os.path.exists(LOCAL_BACKUP):
            print("🔍 從本地備援載入資料...")
            with open(LOCAL_BACKUP, 'r', encoding='utf-8') as f:
                history = json.load(f)
                print(f"✅ 從本地載入 {len(history)} 筆資料")
    except Exception as e:
        print(f"⚠️ 載入本地資料失敗：{e}")
    
    return history

def save_history(history: List[Dict]) -> bool:
    """儲存歷史價格資料（同步到 Gist + 本地備援）"""
    # 只保留最近的資料
    history = history[-HISTORY_DAYS:]
    content = json.dumps(history, ensure_ascii=False, indent=2)
    
    success = False
    
    # 1. 嘗試儲存到 GitHub Gist
    if GITHUB_TOKEN:
        gist_id = get_gist_id()
        
        if gist_id:
            # 更新現有 Gist
            if update_gist(gist_id, content):
                print("✅ 已更新 GitHub Gist")
                success = True
        else:
            # 建立新 Gist
            new_gist_id = create_gist(content)
            if new_gist_id:
                print(f"✅ 已建立新 Gist：{new_gist_id}")
                success = True
    
    # 2. 同時儲存到本地（備援）
    try:
        with open(LOCAL_BACKUP, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 已儲存本地備援")
    except Exception as e:
        print(f"⚠️ 儲存本地備援失敗：{e}")
    
    return success

# ==================== 技術分析 ====================

def calculate_ma(history: List[Dict], days: int) -> Optional[float]:
    """計算 N 日均線"""
    if len(history) < days:
        return None
    recent_prices = [h['price'] for h in history[-days:]]
    return sum(recent_prices) / len(recent_prices)

def analyze_trend(history: List[Dict], days: int = 3) -> tuple:
    """分析近 N 日趨勢"""
    if len(history) < days:
        return "資料不足", "📊"
    
    prices = [h['price'] for h in history[-days:]]
    
    # 判斷趨勢
    if days == 3:
        if prices[0] > prices[1] > prices[2]:
            return "連續下跌", "📉"
        elif prices[0] < prices[1] < prices[2]:
            return "連續上漲", "📈"
        elif prices[0] > prices[1] and prices[1] < prices[2]:
            return "止跌反彈", "💡"
        elif prices[0] < prices[1] and prices[1] > prices[2]:
            return "上漲回落", "⚠️"
        else:
            return "震盪整理", "📊"
    
    return "整理中", "📊"

def get_ma_position(price: float, ma: Optional[float]) -> str:
    """判斷價格相對均線位置"""
    if ma is None:
        return "無資料"
    
    if price > ma:
        diff = ((price - ma) / ma) * 100
        return f"上方 +{diff:.1f}%"
    else:
        diff = ((ma - price) / ma) * 100
        return f"下方 -{diff:.1f}%"

def get_smart_suggestion(price: float, history: List[Dict], ma5: Optional[float], 
                         ma20: Optional[float], ma60: Optional[float]) -> List[str]:
    """智能買賣建議"""
    suggestions = []
    
    # 基本資料檢查
    if len(history) < 3:
        suggestions.append("📊 資料累積中，暫無建議")
        return suggestions
    
    # 趨勢分析
    trend_desc, trend_icon = analyze_trend(history, days=3)
    
    # 均線排列
    ma_alignment = []
    if ma5 and ma20:
        if ma5 > ma20:
            ma_alignment.append("短期 > 中期")
        else:
            ma_alignment.append("短期 < 中期")
    
    if ma20 and ma60:
        if ma20 > ma60:
            ma_alignment.append("中期 > 長期")
        else:
            ma_alignment.append("中期 < 長期")
    
    # ============ 買入訊號 ============
    
    # 強烈買入：多頭排列 + 止跌反彈
    if (ma5 and ma20 and ma60 and 
        price > ma5 > ma20 > ma60 and 
        trend_desc == "止跌反彈"):
        suggestions.append("🔥 多頭排列且止跌反彈")
        suggestions.append("💡 強烈建議：可積極買入")
        return suggestions
    
    # 買入：突破關鍵均線
    if ma20 and price > ma20 and len(history) >= 2:
        prev_price = history[-2]['price']
        if prev_price <= ma20:
            suggestions.append("💡 突破20日均線（月線）")
            suggestions.append("✅ 建議：可考慮分批買入")
            return suggestions
    
    # 買入：止跌反彈且站穩5日線
    if trend_desc == "止跌反彈" and ma5 and price > ma5:
        suggestions.append(f"{trend_icon} {trend_desc}且站穩5日線")
        suggestions.append("💡 建議：可考慮分批買入")
        return suggestions
    
    # ============ 觀望訊號 ============
    
    # 觀望：連續下跌
    if trend_desc == "連續下跌":
        suggestions.append(f"{trend_icon} {trend_desc}")
        if ma20 and price < ma20:
            suggestions.append("⚠️ 建議：趨勢偏弱，繼續觀望")
            suggestions.append("👀 等待：止跌並突破月線再考慮")
        else:
            suggestions.append("👀 建議：等待止跌訊號")
        return suggestions
    
    # 觀望：空頭排列
    if ma5 and ma20 and ma60 and price < ma5 < ma20 < ma60:
        suggestions.append("📉 空頭排列（價格 < 短期 < 中期 < 長期）")
        suggestions.append("⚠️ 建議：趨勢偏弱，不宜進場")
        return suggestions
    
    # ============ 賣出/減碼訊號 ============
    
    # 賣出：跌破關鍵均線
    if ma20 and price < ma20 and len(history) >= 2:
        prev_price = history[-2]['price']
        if prev_price >= ma20:
            suggestions.append("⚠️ 跌破20日均線（月線）")
            suggestions.append("🚫 建議：考慮減碼或停損")
            return suggestions
    
    # 賣出：上漲回落
    if trend_desc == "上漲回落" and ma5 and price < ma5:
        suggestions.append(f"{trend_icon} {trend_desc}且跌破5日線")
        suggestions.append("⚠️ 建議：可考慮減碼")
        return suggestions
    
    # ============ 持有訊號 ============
    
    # 持有：多頭排列
    if ma5 and ma20 and price > ma5 > ma20:
        suggestions.append("📈 短中期多頭格局")
        suggestions.append("✅ 建議：可持續持有")
        return suggestions
    
    # 持有：連續上漲
    if trend_desc == "連續上漲":
        suggestions.append(f"{trend_icon} {trend_desc}")
        if ma5 and price > ma5 * 1.05:  # 漲幅超過5日線5%
            suggestions.append("⚠️ 提醒：漲幅較大，注意回檔風險")
        else:
            suggestions.append("✅ 建議：可持續持有")
        return suggestions
    
    # 預設：震盪整理
    suggestions.append(f"{trend_icon} {trend_desc}")
    suggestions.append("📊 建議：區間震盪，等待方向明朗")
    
    return suggestions

# ==================== 主程式 ====================

def main():
    # 取得台灣時間
    now = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    today = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
    
    print(f"🕐 台灣時間：{now}")
    print(f"🔑 GitHub Token: {'已設定 ✅' if GITHUB_TOKEN else '未設定 ⚠️'}")
    
    # 取得股價資料
    stock_data = get_tsmc_data()
    if stock_data is None:
        send_line_push(f"【台積電監控】\n{now}\n⚠️ 無法取得股價資料")
        print("⚠️ 無法取得股價")
        return
    
    price = stock_data["price"]
    yesterday_close = stock_data["yesterday_close"]
    change_percent = ((price - yesterday_close) / yesterday_close) * 100
    change_amount = price - yesterday_close
    
    # 載入歷史資料
    history = load_history()
    
    # 檢查是否為新的一天，避免重複記錄
    if not history or history[-1].get('date') != today:
        history.append({
            'date': today,
            'price': price,
            'timestamp': now
        })
        save_success = save_history(history)
        print(f"✅ 已記錄今日價格：{price:.2f}（{'Gist' if save_success else '本地'}）")
    
    # 計算均線
    ma5 = calculate_ma(history, 5)
    ma20 = calculate_ma(history, 20)
    ma60 = calculate_ma(history, 60)
    
    # 智能建議
    suggestions = get_smart_suggestion(price, history, ma5, ma20, ma60)
    
    # ==================== 組合訊息 ====================
    
    msg_parts = []
    
    # 標題
    msg_parts.append("【台積電價格監控】")
    msg_parts.append(f"時間：{now}")
    msg_parts.append("━━━━━━━━━━━━━━")
    
    # 基本資訊
    msg_parts.append(f"現價：{price:.2f} 元")
    msg_parts.append(f"昨收：{yesterday_close:.2f} 元")
    msg_parts.append(f"漲跌：{change_amount:+.2f} 元（{change_percent:+.2f}%）")
    
    # 均線資訊
    if ma5 or ma20 or ma60:
        msg_parts.append("━━━━━━━━━━━━━━")
        msg_parts.append("📊 技術分析")
        
        if ma5:
            pos = get_ma_position(price, ma5)
            icon = "✅" if price > ma5 else "⚠️"
            msg_parts.append(f"5日均線：{ma5:.2f} 元 {icon}")
        
        if ma20:
            pos = get_ma_position(price, ma20)
            icon = "✅" if price > ma20 else "⚠️"
            msg_parts.append(f"20日均線：{ma20:.2f} 元 {icon}")
        
        if ma60:
            pos = get_ma_position(price, ma60)
            icon = "✅" if price > ma60 else "⚠️"
            msg_parts.append(f"60日均線：{ma60:.2f} 元 {icon}")
    
    # 智能建議
    msg_parts.append("━━━━━━━━━━━━━━")
    msg_parts.extend(suggestions)
    
    # 資料狀態
    msg_parts.append("━━━━━━━━━━━━━━")
    storage_status = "GitHub Gist ☁️" if GITHUB_TOKEN and get_gist_id() else "本地備援 💾"
    msg_parts.append(f"📝 歷史：{len(history)}/{HISTORY_DAYS} 天 ({storage_status})")
    
    # 發送訊息
    msg = "\n".join(msg_parts)
    send_line_push(msg)
    
    print("✅ 推播完成")
    print(f"   現價：{price:.2f}，昨收：{yesterday_close:.2f}，漲跌：{change_percent:+.2f}%")
    if ma5:
        print(f"   MA5：{ma5:.2f}")
    if ma20:
        print(f"   MA20：{ma20:.2f}")
    if ma60:
        print(f"   MA60：{ma60:.2f}")

if __name__ == "__main__":
    main()