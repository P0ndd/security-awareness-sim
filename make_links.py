"""
สร้างลิงก์ย่อ (mask) ต่อคนอัตโนมัติ แล้วเขียนลง campaign_links.csv

- ปลายทางของแต่ละลิงก์ = <base_url>/t/<employee_id>  (server.py จะ track การคลิกได้ตามปกติ)
- ใช้ is.gd เป็นค่าเริ่มต้น เพราะมี API ฟรี ไม่ต้องมี key และเรียกวน loop ได้
  (shorturl.asia บล็อกการเรียกอัตโนมัติ = HTTP 403 จึงใช้ทำ loop ไม่ได้)

วิธีใช้:
  1) เปิด tunnel ก่อน (start.ps1) เพื่อให้มี public URL
  2) python make_links.py                     # อ่าน base URL จาก tunnel.log อัตโนมัติ
     หรือระบุเอง: python make_links.py --base https://xxxx.trycloudflare.com
  3) ตรวจ campaign_links.csv แล้วส่ง:
     python send_campaign.py --from-links campaign_links.csv          # dry-run
     python send_campaign.py --from-links campaign_links.csv --live   # ส่งจริง
"""
import argparse
import csv
import os
import re
import sys
import time
import urllib.parse

import requests

# ให้ print ภาษาไทย/อีโมจิได้บน console โค้ดเพจ cp874 (Windows ไทย)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMPLOYEES_FILE = os.path.join(BASE_DIR, "employees.csv")
LINKS_FILE = os.path.join(BASE_DIR, "campaign_links.csv")
TUNNEL_LOG = os.path.join(BASE_DIR, "tunnel.log")

PROVIDERS = {
    # ส่ง long URL ไป แล้วได้ short URL กลับมาเป็น plain text
    "isgd": "https://is.gd/create.php?format=simple&url={url}",
    "vgd": "https://v.gd/create.php?format=simple&url={url}",
    "tinyurl": "https://tinyurl.com/api-create.php?url={url}",
}


def detect_base():
    """ดึง public URL ล่าสุดจาก tunnel.log (ถ้ามี)"""
    if not os.path.exists(TUNNEL_LOG):
        return None
    with open(TUNNEL_LOG, encoding="utf-8", errors="ignore") as f:
        matches = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", f.read())
    return matches[-1] if matches else None


def load_employees():
    if not os.path.exists(EMPLOYEES_FILE):
        sys.exit("ไม่พบ employees.csv — คัดลอกจาก employees.example.csv แล้วกรอกรายชื่อก่อน")
    with open(EMPLOYEES_FILE, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def shorten(long_url, provider):
    api = PROVIDERS[provider].format(url=urllib.parse.quote(long_url, safe=""))
    resp = requests.get(api, timeout=20)
    text = resp.text.strip()
    if resp.status_code != 200 or not text.lower().startswith("http"):
        raise RuntimeError(f"{resp.status_code}: {text[:120]}")
    return text


def main():
    parser = argparse.ArgumentParser(description="สร้าง short link ต่อคน → campaign_links.csv")
    parser.add_argument("--base", help="base URL ของ server (ไม่ใส่ = อ่านจาก tunnel.log)")
    parser.add_argument("--provider", choices=PROVIDERS.keys(), default="isgd",
                        help="ผู้ให้บริการย่อลิงก์ (ค่าเริ่มต้น: isgd)")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="หน่วงเวลาระหว่างการสร้างแต่ละลิงก์ (วินาที) กันโดน rate limit")
    args = parser.parse_args()

    base = args.base or detect_base()
    if not base:
        sys.exit("❌ ไม่พบ base URL — เปิด tunnel ด้วย start.ps1 ก่อน หรือระบุ --base https://...")
    base = base.rstrip("/")

    employees = load_employees()
    print(f"=== สร้าง short link ({args.provider}) ให้ {len(employees)} คน | base = {base} ===\n")

    rows, ok, fail = [], 0, 0
    for i, e in enumerate(employees, 1):
        emp_id = e.get("employee_id", "").strip()
        phone = e.get("phone", "").strip()
        if not emp_id:
            continue
        dest = f"{base}/t/{urllib.parse.quote(emp_id)}"
        try:
            short = shorten(dest, args.provider)
            rows.append({"employee_id": emp_id, "phone": phone, "link": short})
            ok += 1
            print(f"[{i}/{len(employees)}] {emp_id}: {short}  ←  {dest}")
        except Exception as ex:  # noqa: BLE001
            fail += 1
            print(f"[{i}/{len(employees)}] {emp_id}: ❌ ล้มเหลว ({ex})")
        if i < len(employees):
            time.sleep(args.delay)

    if not rows:
        sys.exit("\n❌ ไม่ได้ลิงก์เลย — ตรวจการเชื่อมต่ออินเทอร์เน็ต/ผู้ให้บริการ")

    with open(LINKS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["employee_id", "phone", "link"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ เขียน {ok} ลิงก์ลง campaign_links.csv แล้ว" + (f" (ล้มเหลว {fail})" if fail else ""))
    print("   ขั้นต่อไป:")
    print("   python send_campaign.py --from-links campaign_links.csv          # dry-run")
    print("   python send_campaign.py --from-links campaign_links.csv --live   # ส่งจริง")


if __name__ == "__main__":
    main()
