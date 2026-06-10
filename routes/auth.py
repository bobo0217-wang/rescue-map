import sqlite3, hashlib, secrets, requests
from flask import Blueprint, request, jsonify, session, redirect, current_app
from database.init_db import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    db_path = current_app.config["DB_PATH"]
    conn = get_db(db_path)
    row  = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ── 一般註冊 ─────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip()
    password = data.get("password", "")
    if not username or not email or not password:
        return jsonify({"error": "請填寫所有欄位"}), 400
    db_path = current_app.config["DB_PATH"]
    try:
        conn = get_db(db_path)
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?,?,?)",
            (username, email, hash_pw(password))
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        return jsonify({"error": "帳號或 Email 已存在"}), 409

# ── 一般登入 ─────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = (data.get("email") or "").strip()
    password = data.get("password", "")
    db_path  = current_app.config["DB_PATH"]
    conn = get_db(db_path)
    user = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hash_pw(password))
    ).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "帳號或密碼錯誤"}), 401
    session.permanent = True
    session["user_id"] = user["id"]
    return jsonify({"ok": True, "username": user["username"] or user["display_name"]})

# ── 登出 ─────────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

# ── 取得目前登入者 ────────────────────────────────────────
@auth_bp.route("/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in":  True,
        "id":         user["id"],
        "username":   user["username"] or user["display_name"],
        "avatar_url": user["avatar_url"],
        "role":       user["role"],
    })

# ── LINE Login：取得授權 URL ──────────────────────────────
@auth_bp.route("/line")
def line_login():
    cfg   = current_app.config
    state = secrets.token_hex(16)
    session["line_state"] = state
    params = (
        f"response_type=code"
        f"&client_id={cfg['LINE_CLIENT_ID']}"
        f"&redirect_uri={cfg['LINE_REDIRECT_URI']}"
        f"&state={state}"
        f"&scope=profile%20openid%20email"
    )
    return redirect(f"https://access.line.me/oauth2/v2.1/authorize?{params}")

# ── LINE Login：Callback ──────────────────────────────────
@auth_bp.route("/line/callback")
def line_callback():
    code  = request.args.get("code")
    state = request.args.get("state")
    if state != session.pop("line_state", None):
        return "Invalid state", 400

    cfg = current_app.config

    token_resp = requests.post("https://api.line.me/oauth2/v2.1/token", data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  cfg["LINE_REDIRECT_URI"],
        "client_id":     cfg["LINE_CLIENT_ID"],
        "client_secret": cfg["LINE_CLIENT_SECRET"],
    }).json()

    access_token = token_resp.get("access_token")
    if not access_token:
        return "LINE 登入失敗", 400

    profile = requests.get("https://api.line.me/v2/profile", headers={
        "Authorization": f"Bearer {access_token}"
    }).json()

    line_id      = profile.get("userId")
    display_name = profile.get("displayName", "")
    avatar_url   = profile.get("pictureUrl", "")

    db_path = cfg["DB_PATH"]
    conn    = get_db(db_path)
    user    = conn.execute("SELECT * FROM users WHERE line_id=?", (line_id,)).fetchone()
    if not user:
        conn.execute(
            "INSERT INTO users (line_id, display_name, avatar_url) VALUES (?,?,?)",
            (line_id, display_name, avatar_url)
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE line_id=?", (line_id,)).fetchone()
    else:
        conn.execute(
            "UPDATE users SET display_name=?, avatar_url=? WHERE line_id=?",
            (display_name, avatar_url, line_id)
        )
        conn.commit()
    conn.close()

    session.permanent = True
    session["user_id"] = user["id"]
    return redirect("/cases")
