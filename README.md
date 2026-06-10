# 浪浪救援平台

Flask + SQLite + PTT爬蟲 + 農業部API，部署於 Railway。

## 專案結構

```
rescue-map/
├── app.py                  # Flask 主程式（路由 + 排程爬蟲）
├── config.py               # 設定（LINE Login key、DB 路徑）
├── requirements.txt
├── Procfile
├── database/
│   └── init_db.py          # 資料表建立
├── routes/
│   ├── auth.py             # 登入/註冊/LINE Login
│   ├── cases.py            # 個案 CRUD API
│   └── scraper.py          # PTT + 農業部爬蟲
├── static/
│   ├── css/style.css
│   └── js/
│       ├── auth.js         # 登入/註冊邏輯
│       ├── cases.js        # 個案清單 + Modal
│       ├── map.js          # Leaflet 地圖
│       └── report.js       # 回報表單
└── templates/
    ├── base.html           # 共用 Layout（Navbar）
    ├── login.html
    ├── register.html
    ├── cases.html          # 個案清單頁
    ├── map.html            # 地圖頁
    └── report.html         # 回報個案頁
```

## 本地啟動

```bash
pip install -r requirements.txt
python app.py
# 開啟 http://localhost:5000
```

## 部署到 Railway

1. 推上 GitHub → Railway New Project → 選 repo
2. 設定環境變數：

| 變數名稱 | 說明 |
|---------|------|
| `SECRET_KEY` | 隨機字串，用於 Session 加密 |
| `LINE_CLIENT_ID` | LINE Login Channel ID |
| `LINE_CLIENT_SECRET` | LINE Login Channel Secret |
| `LINE_REDIRECT_URI` | `https://你的網址/auth/line/callback` |

## LINE Login 設定

1. 前往 https://developers.line.biz/console/
2. 建立 Provider → 建立 LINE Login Channel
3. 在「LINE Login」分頁設定 Callback URL：
   `https://你的網址/auth/line/callback`
4. 把 Channel ID / Channel Secret 填入環境變數

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/cases` | GET | 取得個案清單（支援 status/animal_type/source 篩選）|
| `/api/cases` | POST | 新增個案（需登入）|
| `/api/cases/<id>` | GET | 個案詳情 + 筆記 |
| `/api/cases/<id>/handle` | POST | 標記已處理（需登入）|
| `/api/cases/<id>/reopen` | POST | 重新開啟個案（需登入）|
| `/api/cases/<id>/notes` | POST | 新增筆記（需登入）|
| `/api/scraper/run` | POST | 手動觸發爬蟲 |
| `/auth/register` | POST | 一般註冊 |
| `/auth/login` | POST | 一般登入 |
| `/auth/logout` | POST | 登出 |
| `/auth/me` | GET | 取得目前登入者資訊 |
| `/auth/line` | GET | 開始 LINE Login 流程 |
| `/auth/line/callback` | GET | LINE Login Callback |
