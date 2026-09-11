"""
เว็บเซิร์ฟเวอร์หน้า "เฉลย" สำหรับ Phishing Simulation

- /t/<employee_id> : บันทึกว่าใครคลิก (เวลา + อุปกรณ์/เบราว์เซอร์/OS/IP) ลง clicks.csv
                     แล้วแสดงหน้าเฉลยที่ "โชว์ข้อมูลที่เก็บได้" กลับไปให้ผู้คลิกเห็น (ใช้สาธิตตอนอบรม)
- /export?token=   : ดาวน์โหลด clicks.csv (ป้องกันด้วย ADMIN_TOKEN)
- ไม่มีช่องกรอกรหัสผ่าน/ข้อมูลส่วนตัว — เก็บเพื่อการอบรมเท่านั้น

รันในเครื่อง:  python server.py            (พอร์ต 8080)
รันบน Render:  gunicorn server:app --bind 0.0.0.0:$PORT
"""
import csv
import os
import re
from datetime import datetime, timezone, timedelta

from flask import Flask, request, render_template, Response, abort

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
CLICKS_FILE = os.path.join(DATA_DIR, "clicks.csv")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
TH_TZ = timezone(timedelta(hours=7))
COLUMNS = ["timestamp", "employee_id", "device", "os", "browser", "ip", "user_agent"]

app = Flask(__name__)


def parse_ua(ua):
    """แยกชนิดอุปกรณ์ / ระบบปฏิบัติการ / เบราว์เซอร์ จาก User-Agent (ไม่พึ่ง library ภายนอก)"""
    u = ua or ""
    # OS
    if re.search(r"iPhone|iPad|iPod", u):
        os_name = "iOS"
    elif "Android" in u:
        os_name = "Android"
    elif "Windows NT" in u:
        os_name = "Windows"
    elif "Mac OS X" in u:
        os_name = "macOS"
    elif "Linux" in u:
        os_name = "Linux"
    else:
        os_name = "ไม่ทราบ"
    # device
    if "iPad" in u or ("Android" in u and "Mobile" not in u):
        device = "แท็บเล็ต"
    elif re.search(r"Mobile|iPhone|iPod|Android", u):
        device = "มือถือ"
    else:
        device = "คอมพิวเตอร์"
    # browser (เรียงลำดับสำคัญ)
    if "Line/" in u:
        browser = "LINE in-app"
    elif re.search(r"FBAN|FBAV|FB_IAB", u):
        browser = "Facebook in-app"
    elif "Edg" in u:
        browser = "Microsoft Edge"
    elif "OPR" in u or "Opera" in u:
        browser = "Opera"
    elif "Firefox" in u:
        browser = "Firefox"
    elif "Chrome" in u:
        browser = "Google Chrome"
    elif "Safari" in u:
        browser = "Safari"
    else:
        browser = "ไม่ทราบ"
    return device, os_name, browser


def client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or ""


def log_click(employee_id, device, os_name, browser, ip, ua):
    os.makedirs(DATA_DIR, exist_ok=True)
    exists = os.path.exists(CLICKS_FILE)
    with open(CLICKS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(COLUMNS)
        writer.writerow([
            datetime.now(TH_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            employee_id, device, os_name, browser, ip, ua[:200],
        ])


@app.route("/t/<employee_id>")
def track(employee_id):
    ua = request.headers.get("User-Agent", "")
    device, os_name, browser = parse_ua(ua)
    ip = client_ip()
    seen_at = datetime.now(TH_TZ).strftime("%d/%m/%Y %H:%M:%S")
    lang = request.headers.get("Accept-Language", "").split(",")[0] or "ไม่ทราบ"
    log_click(employee_id, device, os_name, browser, ip, ua)
    return render_template(
        "awareness.html",
        employee_id=employee_id,
        device=device, os=os_name, browser=browser,
        ip=ip, seen_at=seen_at, lang=lang,
    )


@app.route("/export")
def export():
    if not ADMIN_TOKEN or request.args.get("token") != ADMIN_TOKEN:
        abort(404)
    if not os.path.exists(CLICKS_FILE):
        data = ",".join(COLUMNS) + "\n"
    else:
        with open(CLICKS_FILE, encoding="utf-8") as f:
            data = f.read()
    return Response(
        data, mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=clicks.csv"},
    )


@app.route("/")
def home():
    return "Security Awareness Training Server", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
