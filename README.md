# 多股即時價格監控通知（Google Sheets 雲端版）

自動監控多支台股（可自訂股票清單）即時價格，並將歷史資料永久儲存於 Google Sheets，透過 LINE 即時推播通知。支援 Render.com 定時排程與本地執行。

## 功能特色

- 即時取得多支台股現價、昨收價（FinMind API，台灣證券交易所資料）
- Google Sheets 雲端儲存歷史資料（自動保留一年）
- 多均線技術分析（5/20/60日）
- LINE 通知（每支股票獨立推播，顯示代號與中文名稱）
- 支援 Render.com 定時任務與本地執行

---

## 資料流程說明

1. 從 FinMind API 取得多支股票即時股價與歷史資料
2. 計算均線等技術指標
3. 將資料寫入 Google Sheets 雲端表格（自動保留一年）
4. 產生 LINE 推播訊息並發送給用戶

---

## 執行環境與需求

- Python 3.8+
- Google Sheets API Service Account 憑證（JSON 格式）
- LINE Messaging API Channel Access Token & User ID
- FinMind API Token（可至 https://finmind.github.io/ 申請，免費註冊即可取得）

### 必要環境變數

| 變數名 | 說明 |
|--------|------|
| LINE_CHANNEL_ACCESS_TOKEN | LINE Bot Token |
| LINE_USER_ID | LINE User ID |
| GOOGLE_SHEETS_CREDENTIALS | Google Sheets Service Account JSON（整份內容） |
| GOOGLE_SHEET_ID | 目標 Google Sheet 的 ID |
| FINMIND_TOKEN | FinMind API Token（股價資料來源） |

---

## Google Sheets 結構

- 每天僅新增一筆資料（自動判斷日期，不重複寫入）
- 欄位：股票代號、中文名稱、日期、收盤價、5日均線、20日均線、60日均線、更新時間
- 自動清理超過一年（365天）前的舊資料

---

## LINE 通知內容範例

【2330 台積電 價格監控】  
時間：2026-02-08 10:30:00  
━━━━━━━━━━━━━━  
現價：678.00 元  
昨收：670.00 元  
漲跌：+8.00（+1.19%）  
5日均線：675.00  
20日均線：660.00  
60日均線：650.00  
今日收盤：678.00 元  
※ 資料來源：FinMind（付費版）

---

## Render.com 部署建議

- 建立 Cron Job，排程建議：
  - 盤中：09:00-13:30，每 3 分鐘
  - 盤後：14:00-14:30，每 3 分鐘
- 設定所有必要環境變數（於 Render.com 設定頁面填入）

---

## 專案結構

stock-multi-notify/  
├── stock-multi-notify.py   # 主程式（多股監控）  
├── requirements.txt       # 相依套件  
├── README.md              # 說明文件  
├── channelaccesstoken.txt # (可選) LINE Token 檔  
├── tsmc-monitor-xxxx.json # (可選) Google 憑證檔  

---

## 常見問題

- Google Sheets 權限錯誤：請確認 Service Account 已加入該 Sheet 共用
- LINE 未收到通知：請檢查 Token 與 User ID 是否正確
- FinMind API 錯誤：請確認 Token 有效且 API 服務正常，若遇到流量限制可稍後再試
- 只新增一筆資料：設計上每天只新增一筆，避免重複，適合做長期均線與年度統計
- 多次執行不會重複寫入同一天資料

---

## 授權
MIT License

---

如有問題，請開 Issue 或聯絡作者。  
**如果覺得有幫助，歡迎給 Star！**
