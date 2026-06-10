from flask import Blueprint, request, jsonify, session, current_app
from database.init_db import get_db
from routes.auth import current_user

cases_bp = Blueprint("cases", __name__, url_prefix="/api/cases")

def require_login():
    if not session.get("user_id"):
        return jsonify({"error": "請先登入"}), 401
    return None

# ── 個案清單 ──────────────────────────────────────────────
@cases_bp.route("", methods=["GET"])
def get_cases():
    status      = request.args.get("status", "")
    animal_type = request.args.get("animal_type", "")
    source      = request.args.get("source", "")
    db_path     = current_app.config["DB_PATH"]

    query  = """
        SELECT c.*, u.username, u.display_name, u.avatar_url
        FROM cases c LEFT JOIN users u ON c.reporter_id = u.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND c.status=?";      params.append(status)
    if animal_type:
        query += " AND c.animal_type=?"; params.append(animal_type)
    if source:
        query += " AND c.source=?";      params.append(source)
    query += " ORDER BY c.created_at DESC"

    conn = get_db(db_path)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── 單一個案 ──────────────────────────────────────────────
@cases_bp.route("/<int:case_id>", methods=["GET"])
def get_case(case_id):
    db_path = current_app.config["DB_PATH"]
    conn = get_db(db_path)
    case = conn.execute("""
        SELECT c.*, u.username, u.display_name
        FROM cases c LEFT JOIN users u ON c.reporter_id=u.id
        WHERE c.id=?
    """, (case_id,)).fetchone()
    notes = conn.execute("""
        SELECT n.*, u.username, u.display_name, u.avatar_url
        FROM case_notes n LEFT JOIN users u ON n.user_id=u.id
        WHERE n.case_id=? ORDER BY n.created_at
    """, (case_id,)).fetchall()
    conn.close()
    if not case:
        return jsonify({"error": "找不到個案"}), 404
    return jsonify({"case": dict(case), "notes": [dict(n) for n in notes]})

# ── 新增個案 ──────────────────────────────────────────────
@cases_bp.route("", methods=["POST"])
def create_case():
    err = require_login()
    if err: return err
    data        = request.get_json()
    title       = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    location    = (data.get("location") or "").strip()
    lat         = data.get("lat")
    lng         = data.get("lng")
    animal_type = data.get("animal_type", "不明")
    image_url   = data.get("image_url", "")
    if not title:
        return jsonify({"error": "請填寫標題"}), 400
    db_path = current_app.config["DB_PATH"]
    conn = get_db(db_path)
    cursor = conn.execute("""
        INSERT INTO cases (title, description, location, lat, lng, animal_type,
                           image_url, reporter_id, source)
        VALUES (?,?,?,?,?,?,?,?,'user')
    """, (title, description, location, lat, lng, animal_type,
          image_url, session["user_id"]))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": new_id}), 201

# ── 標記已處理 ────────────────────────────────────────────
@cases_bp.route("/<int:case_id>/handle", methods=["POST"])
def handle_case(case_id):
    err = require_login()
    if err: return err
    db_path = current_app.config["DB_PATH"]
    conn = get_db(db_path)
    conn.execute("""
        UPDATE cases SET status='handled', handler_id=?,
        handled_at=datetime('now','localtime'),
        updated_at=datetime('now','localtime')
        WHERE id=?
    """, (session["user_id"], case_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ── 重新開啟 ──────────────────────────────────────────────
@cases_bp.route("/<int:case_id>/reopen", methods=["POST"])
def reopen_case(case_id):
    err = require_login()
    if err: return err
    db_path = current_app.config["DB_PATH"]
    conn = get_db(db_path)
    conn.execute("""
        UPDATE cases SET status='open', handler_id=NULL, handled_at=NULL,
        updated_at=datetime('now','localtime') WHERE id=?
    """, (case_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ── 新增筆記 ──────────────────────────────────────────────
@cases_bp.route("/<int:case_id>/notes", methods=["POST"])
def add_note(case_id):
    err = require_login()
    if err: return err
    data = request.get_json()
    note = (data.get("note") or "").strip()
    if not note:
        return jsonify({"error": "請輸入筆記內容"}), 400
    db_path = current_app.config["DB_PATH"]
    conn = get_db(db_path)
    conn.execute(
        "INSERT INTO case_notes (case_id, user_id, note) VALUES (?,?,?)",
        (case_id, session["user_id"], note)
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})
