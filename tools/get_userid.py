import requests

# 把你的 long-lived Channel access token 貼在這裡
CHANNEL_ACCESS_TOKEN = "dlYyOYuIula9h4aazdYHXNQK7MhyZr08AZ91HtpsL/E+iflnoJjbpZZwSutsinYmfNuQZwps477WfFfcZI9KG5cuwhjW3B1ORW+Xb0fiAoE9Vn2CLZ0Q/pvtz/PXR1kgYo9TKBazA9Me8Lv8IbIydAdB04t89/1O/w1cDnyilFU="

headers = {
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 取得官方帳號最近收到的訊息（limit=1 只要最新一筆）
url = "https://api.line.me/v2/bot/message/quota/consumption"  # 先用 quota 測試 token 是否正常
# 但更實用的方式是用 get message 相關 API，不過 LINE 沒有直接提供「取得收到的訊息」給自己

print("請先確認：")
print("1. 你已經用手機加官方帳號為好友")
print("2. 你已經對官方帳號傳送過至少一則訊息")
print("如果都做了，請繼續往下")

# 目前最簡單的替代方案：請你手動看 LINE 的官方帳號管理後台

print("\n替代方案（最快）：")
print("1. 前往 https://manager.line.biz/")
print("2. 登入你的 LINE 帳號")
print("3. 選擇你的官方帳號 (@883lfbyr)")
print("4. 點左側「聊天」或「訊息」")
print("5. 找到你剛剛傳的那則訊息")
print("6. 點進去聊天室，右上角點「i」或「詳細資訊」")
print("7. 有些版本會顯示「使用者 ID」或「User ID」，就是 U 開頭的那串")

print("\n如果 LINE Manager 沒有顯示 userId，請告訴我，我給你另一個方法（用 ngrok + 暫時開 webhook）")