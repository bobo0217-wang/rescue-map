import requests
import warnings
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, current_app
from database.init_db import get_db

warnings.filterwarnings("ignore")

scraper_bp = Blueprint("scraper", __name__, url_prefix="/api/scraper")

PTT_BOARD  = "https://www.ptt.cc/bbs/animal/index.html"
PTT_BASE   = "https://www.ptt.cc"
ANIMAL_API = "https://data.moa.gov.tw/Service/OpenData/TransService.aspx?UnitId=QcbUEzN6E6DL&IsTransData=1"

RESCUE_KEYWORDS = ["急", "救援", "救助", "受傷", "流浪", "需要幫助", "待救", "協尋", "緊急", "求助"]

AREA_CODE_MAP = {
    "01": "臺北市", "02": "新北市", "03": "桃園市", "04": "臺中市",
    "05": "臺南市", "06": "高雄市", "07": "基隆市", "08": "新竹市",
    "09": "新竹縣", "10": "苗栗縣", "11": "彰化縣", "12": "南投縣",
    "13": "雲林縣", "14": "嘉義市", "15": "嘉義縣", "16": "屏東縣",
    "17": "宜蘭縣", "18": "花蓮縣", "19": "臺東縣", "20": "澎湖縣",
    "21": "金門縣", "22": "連江縣",
}

# ── PTT 動物版爬蟲 ────────────────────────────────────────
def scrape_ptt(db_path, pages=3):
    """
    PTT 需要先 POST 成人確認頁才能取得 over18 cookie，
    否則會被導向確認頁，選不到文章。
    """
    sess = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 第一步：先 POST 成人確認，取得合法 cookie
    try:
        sess.post(
            "https://www.ptt.cc/ask/over18",
            data={"yes": "yes"},
            headers=headers,
            timeout=8,
        )
    except Exception as e:
        print(f"[PTT] 成人確認失敗: {e}")
        return 0

    inserted = 0
    url = PTT_BOARD

    for _ in range(pages):
        try:
            resp = sess.get(url, headers=headers, timeout=8)
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"[PTT] 抓取失敗: {e}")
            break

        # 確認頁面有沒有正確拿到文章（防止被擋在確認頁）
        articles = soup.select(".r-ent")
        if not articles:
            print(f"[PTT] 頁面沒有文章，可能被擋：{resp.url}")
            break

        for art in articles:
            title_el = art.select_one(".title a")
            if not title_el:
                continue
            title = title_el.text.strip()
            href  = PTT_BASE + title_el["href"]

            if not any(kw in title for kw in RESCUE_KEYWORDS):
                continue

            animal_type = "不明"
            if "貓" in title:
                animal_type = "貓"
            elif "狗" in title or "犬" in title:
                animal_type = "狗"

            conn = get_db(db_path)
            exists = conn.execute(
                "SELECT id FROM cases WHERE source_url=?", (href,)
            ).fetchone()
            if not exists:
                conn.execute("""
                    INSERT INTO cases (title, source, source_url, animal_type, status)
                    VALUES (?, 'ptt', ?, ?, 'open')
                """, (title, href, animal_type))
                conn.commit()
                inserted += 1
            conn.close()

        # 翻到上一頁（舊文章方向）
        prev_btn = soup.select(".btn-group-paging a")
        prev_url = None
        for btn in prev_btn:
            if "上頁" in btn.text or "‹" in btn.text:
                prev_url = PTT_BASE + btn["href"]
                break
        if prev_url:
            url = prev_url
        else:
            break

    print(f"[PTT] 新增 {inserted} 筆")
    return inserted

# ── 農業部 API ────────────────────────────────────────────
def scrape_moa(db_path):
    try:
        resp    = requests.get(ANIMAL_API, timeout=15, verify=False)
        animals = resp.json()
    except Exception as e:
        print(f"[MOA] 抓取失敗: {e}")
        return 0

    shelters = {}
    for a in animals:
        name = (a.get("shelter_name") or "").strip()
        if not name:
            continue
        if name not in shelters:
            area_code = str(a.get("animal_area_pkid") or "").zfill(2)
            county = AREA_CODE_MAP.get(area_code, "")
            addr   = (a.get("shelter_address") or "").strip()
            shelters[name] = {
                "name": name, "county": county,
                "address": addr, "tel": (a.get("shelter_tel") or "").strip(),
                "dogs": 0, "cats": 0,
            }
        kind = a.get("animal_kind") or ""
        if "狗" in kind or "犬" in kind:
            shelters[name]["dogs"] += 1
        elif "貓" in kind:
            shelters[name]["cats"] += 1

    inserted = 0
    for s in shelters.values():
        title      = f"【收容所】{s['name']} — 狗{s['dogs']}隻 貓{s['cats']}隻"
        source_url = f"moa://{s['name']}"
        conn   = get_db(db_path)
        exists = conn.execute(
            "SELECT id FROM cases WHERE source_url=?", (source_url,)
        ).fetchone()
        if exists:
            conn.execute("""
                UPDATE cases SET title=?, description=?, updated_at=datetime('now','localtime')
                WHERE source_url=?
            """, (title, f"地址：{s['address']}\n電話：{s['tel']}", source_url))
        else:
            conn.execute("""
                INSERT INTO cases (title, description, location, animal_type, source, source_url, status)
                VALUES (?, ?, ?, '不明', 'moa', ?, 'open')
            """, (title, f"地址：{s['address']}\n電話：{s['tel']}",
                  s["county"] + s["address"], source_url))
            inserted += 1
        conn.commit()
        conn.close()

    print(f"[MOA] 新增/更新 {len(shelters)} 筆，其中新增 {inserted} 筆")
    return inserted

# ── 手動觸發 ─────────────────────────────────────────────
@scraper_bp.route("/run", methods=["POST"])
def run_scraper():
    db_path = current_app.config["DB_PATH"]
    ptt = scrape_ptt(db_path)
    moa = scrape_moa(db_path)
    return jsonify({"ptt": ptt, "moa": moa})
