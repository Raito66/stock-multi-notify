# 測試發送推播給所有好友（你應該只有自己）
import requests

CHANNEL_ACCESS_TOKEN = "dlYyOYuIula9h4aazdYHXNQK7MhyZr08AZ91HtpsL/E+iflnoJjbpZZwSutsinYmfNuQZwps477WfFfcZI9KG5cuwhjW3B1ORW+Xb0fiAoE9Vn2CLZ0Q/pvtz/PXR1kgYo9TKBazA9Me8Lv8IbIydAdB04t89/1O/w1cDnyilFU="   # 貼你的 long-lived token

url = "https://api.line.me/v2/bot/message/broadcast"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
}

payload = {
    "messages": [
        {
            "type": "text",
            "text": "測試訊息：這是系統發給你的 userId 確認用\n如果看到這句，表示你的帳號已正確連結。"
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    print("測試廣播訊息發送成功！")
    print("請馬上檢查你的 LINE App 是否收到這則訊息")
else:
    print("發送失敗")
    print("狀態碼：", response.status_code)
    print("錯誤訊息：", response.text)