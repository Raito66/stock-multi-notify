# 台積電價格監控

每 5 分鐘檢查台積電股價，當價格進入動態區間（±2%）時，透過 LINE 推播通知。

## 功能
- 動態計算提醒區間（根據當前股價 ±2%）
- 使用 LINE Messaging API 推播（長期穩定）
- 從外部檔案讀取 token（安全）
- 包含交易時間判斷與重試機制

## 使用方式
1. 在 channelaccesstoken.txt 放入 LINE Channel Access Token
2. 執行：python tsmc_price_notify.py

## 部署建議
- Render.com（免費方案）
- Railway.app
- Heroku（付費 Eco 方案）

## 注意事項
- token 絕對不要 commit 上 Git
- 程式使用環境變數或 txt 檔案管理 token