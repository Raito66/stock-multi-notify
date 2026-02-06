from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route("/webhook", methods=['POST', 'GET'])
def line_webhook():
    print("\n[DEBUG] 有人訪問了 /webhook")
    print(f"[DEBUG] 方法: {request.method}")
    print(f"[DEBUG] 來源 IP: {request.remote_addr}")
    
    if request.method == 'GET':
        print("[DEBUG] 收到 GET 請求，這是 LINE Verify 測試")
        return "OK - Webhook is ready", 200

    # 處理 POST (LINE 真正送來的 webhook)
    if request.method == 'POST':
        print("[DEBUG] 收到 POST 請求，準備讀取 JSON")
        try:
            data = request.get_json(force=True)
            print("\n=== 收到 LINE Webhook 事件 ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if 'events' in data and data['events']:
                for event in data['events']:
                    if event.get('type') == 'message' and 'source' in event:
                        source = event['source']
                        if 'userId' in source:
                            user_id = source['userId']
                            msg_text = event['message'].get('text', '(非文字訊息)')
                            print("\n★★★★★ 你的 User ID 是：", user_id)
                            print("訊息內容：", msg_text)
                            print("請把上面的 User ID 複製下來！")
            
            return jsonify({"status": "ok"}), 200
        
        except Exception as e:
            print("[ERROR] 解析 JSON 失敗：", str(e))
            return jsonify({"error": "Invalid JSON"}), 400

    return "Method not allowed", 405

@app.route("/", methods=['GET'])
def root():
    return "Webhook server is running. Use /webhook for LINE.", 200

if __name__ == "__main__":
    print("=== Webhook 伺服器啟動中 ===")
    print("訪問 http://127.0.0.1:5000/ 測試是否正常")
    print("等待 LINE 事件中... (記得保持視窗開著)")
    app.run(host='0.0.0.0', port=5000, debug=True)