import os

class Config:
    SECRET_KEY         = os.environ.get("SECRET_KEY") or "rescue-map-dev-secret-key-2024"
    DB_PATH            = os.environ.get("DB_PATH", "rescue.db")
    LINE_CLIENT_ID     = os.environ.get("LINE_CLIENT_ID", "")
    LINE_CLIENT_SECRET = os.environ.get("LINE_CLIENT_SECRET", "")
    LINE_REDIRECT_URI  = os.environ.get("LINE_REDIRECT_URI", "http://localhost:5000/auth/line/callback")

    # Session 設定
    SESSION_COOKIE_NAME     = "rescue_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE   = False  # Railway 上設 True
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 天
