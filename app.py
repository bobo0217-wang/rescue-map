from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, session, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from database.init_db import init_db
from routes.auth import auth_bp
from routes.cases import cases_bp
from routes.scraper import scraper_bp, scrape_ptt, scrape_moa

app = Flask(__name__)
app.config.from_object(Config)

# Session cookie 設定
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"]   = False  # 部署到 HTTPS 時改 True

CORS(app, supports_credentials=True,
     origins=["http://localhost:5000", "http://127.0.0.1:5000"])

# 初始化資料庫
init_db(app.config["DB_PATH"])

# 註冊 Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(cases_bp)
app.register_blueprint(scraper_bp)

# ── 頁面路由 ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("cases.html")

@app.route("/cases")
def cases_page():
    return render_template("cases.html")

@app.route("/shelters")
def shelters_page():
    return render_template("shelters.html")

@app.route("/map")
def map_page():
    return render_template("map.html")

@app.route("/report")
def report_page():
    return render_template("report.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

# ── 定時爬蟲（每 3 小時）────────────────────────────────
def scheduled_scrape():
    with app.app_context():
        db_path = app.config["DB_PATH"]
        scrape_ptt(db_path)
        scrape_moa(db_path)

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_scrape, "interval", hours=3, id="scraper")
scheduler.start()

# 啟動時先跑一次
with app.app_context():
    scheduled_scrape()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
