# TSMC-Notify (多股價格監控自動推播)

本專案可自動監控多檔台股股票，推播即時/收盤價、均線、建議等資訊到 Discord，並同步寫入 Google Sheets。

## 功能特色
- 盤中推播即時成交價、均線、操作建議
- 盤後推播收盤價、均線、行情摘要、操作建議
- 支援多檔股票（如台積電、力積電、群創等）
- 所有推播內容皆自動產生，無人工干預
- 資料來源：FinMind

## 快速開始

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 設定 .env
請建立 `.env` 檔案，內容如下：
```
GOOGLE_SHEETS_CREDENTIALS=你的 Google Sheets Service Account JSON 字串
GOOGLE_SHEET_ID=你的 Google Sheets ID
FINMIND_TOKEN=你的 FinMind API Token
DISCORD_WEBHOOK_URL=你的 Discord Webhook 連結
```

### 3. 設定 Discord Webhook
1. 進入 Discord 頻道 > 編輯頻道 > 整合 > Webhooks > 新增 Webhook。
2. 複製 Webhook URL，貼到 `.env` 的 `DISCORD_WEBHOOK_URL`。

### 4. 設定 Google Sheets 權限
- 請將 Service Account 的 email 加入 Google Sheets 共用（編輯權限）。
- 否則會出現「權限錯誤」。

### 5. 執行主程式
```bash
python stock-multi-notify.py
```

### 6. 補齊歷史資料
如需補齊 Google Sheets 歷史收盤價與均線資料，請執行：
```bash
python stock-history-fill.py
```
- 程式會自動檢查每檔股票是否有 400 筆資料，缺漏會自動補齊。
- 所有 Google Sheets 操作（寫入、刪除、更新）遇到 API 配額限制（429 quota exceeded）時，會自動 sleep 60 秒並無限重試直到成功，**確保資料不會有缺漏且流程不中斷**。
- **若資料已達 400 筆，則自動跳過該股票，不再補資料，排程可安全重複執行。**

## 推播內容範例
```
【2330 台積電 價格監控】
時間：2026-02-09 14:00:00
━━━━━━━━━━━━━━
現價：600.00 元
昨收：590.00 元
漲跌：+10.00（+1.69%）
5日均線：595.00
20日均線：580.00
60日均線：570.00
今日收盤：600.00 元
行情摘要：建議明天可以買進，今天收盤價比平均價高
※ 資料來源：FinMind
```

## 注意事項
- 本專案僅供資訊參考，無任何投資建議，請自行判斷風險。
- 推播時間與頻率依程式設定，若有異常請聯絡管理員。
- 若需新增/移除股票，請修改 `STOCK_LIST`。
- Service Account 權限不足會導致 Sheets 寫入失敗，請務必設定共用。
- 補齊歷史資料時，若遇到 Google Sheets API 配額限制，程式會自動等待並重試，**不會遺漏任何資料**。

---

**自動推播程式：TSMC-Notify**
