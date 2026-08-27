"""
เว็บเซิร์ฟเวอร์หน้า "เฉลย" สำหรับ Phishing Simulation

- /t/<employee_id> : บันทึกว่าใครคลิก (พร้อมเวลา) ลง clicks.csv แล้วแสดงหน้าให้ความรู้
- /export?token=   : ดาวน์โหลด clicks.csv (ป้องกันด้วย ADMIN_TOKEN) — ใช้ดึงผลจาก cloud
- ไม่มีช่องกรอกรหัสผ่าน/ข้อมูลส่วนตัว — เก็บแค่ id + เวลา เพื่อการอบรมเท่านั้น

รันในเครื่อง:  python server.py            (พอร์ต 8080)
รันบน Render:  gunicorn server:app --bind 0.0.0.0:$PORT
"""
import csv
import os
from datetime import datetime, timezone, timedelta

from flask import Flask, request, render_template, Response, abort

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR: ตั้งเป็น persistent disk บน Render ได้ (เช่น /data) ไม่งั้นเก็บข้างโค้ด (ชั่วคราว)
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
CLICKS_FILE = os.path.join(DATA_DIR, "clicks.csv")
# token สำหรับดาวน์โหลดผล (ตั้งใน Render > Environment) ไม่ตั้ง = ปิด /export
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
TH_TZ = timezone(timedelta(hours=7))

app = Flask(__name__)


def log_click(employee_id):
    os.makedirs(DATA_DIR, exist_ok=True)
    exists = os.path.exists(CLICKS_FILE)
    with open(CLICKS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["timestamp", "employee_id", "user_agent"])
        writer.writerow([
            datetime.now(TH_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            employee_id,
            request.headers.get("User-Agent", "")[:200],
        ])


@app.route("/t/<employee_id>")
def track(employee_id):
    log_click(employee_id)
    return render_template("awareness.html", employee_id=employee_id)


@app.route("/export")
def export():
    # ป้องกันด้วย token — ไม่ตั้ง ADMIN_TOKEN หรือ token ไม่ตรง = ซ่อน (404)
    if not ADMIN_TOKEN or request.args.get("token") != ADMIN_TOKEN:
        abort(404)
    if not os.path.exists(CLICKS_FILE):
        data = "timestamp,employee_id,user_agent\n"
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
    # โปรดักชันจริง: วางหลัง nginx + HTTPS, อย่าเปิด debug
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
