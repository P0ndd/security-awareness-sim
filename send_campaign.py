"""
ส่ง SMS จำลอง (Phishing Simulation) เพื่อการฝึกอบรมความปลอดภัยภายในองค์กร

- ค่าเริ่มต้นเป็น dry-run (แสดงผลอย่างเดียว ไม่ส่งจริง)
- ส่งจริงต้องใช้ flag --live และต้องมี AUTHORIZATION.txt ที่กรอกครบ
- ใช้ employee_id เป็น tracking id (ไม่ส่งเบอร์โทรไปในลิงก์)
"""
import argparse
import csv
import json
import os
import sys
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(BASE_DIR, "config.json")
    if not os.path.exists(path):
        sys.exit("ไม่พบ config.json — คัดลอกจาก config.example.json แล้วกรอกค่าก่อน")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_employees():
    path = os.path.join(BASE_DIR, "employees.csv")
    if not os.path.exists(path):
        sys.exit("ไม่พบ employees.csv — คัดลอกจาก employees.example.csv แล้วกรอกรายชื่อก่อน")
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def authorization_ok():
    """ตรวจว่ามีเอกสารอนุมัติที่กรอกจริงแล้ว (ไม่ใช่ template เปล่า)"""
    path = os.path.join(BASE_DIR, "AUTHORIZATION.txt")
    if not os.path.exists(path):
        return False, "ไม่พบ AUTHORIZATION.txt"
    with open(path, encoding="utf-8") as f:
        text = f.read()
    required = ["ผู้อนุมัติ:", "ตำแหน่ง:", "วันที่:", "ขอบเขต:"]
    for key in required:
        line = next((l for l in text.splitlines() if l.strip().startswith(key)), "")
        value = line.split(key, 1)[-1].strip() if key in line else ""
        if not value or value.startswith("<"):
            return False, f"AUTHORIZATION.txt ยังไม่ได้กรอกช่อง '{key}'"
    return True, "ok"


def build_link(base_url, employee_id):
    return f"{base_url.rstrip('/')}/t/{urllib.parse.quote(employee_id)}"


def send_sms(cfg, phone, message):
    import requests
    thsms = cfg["thsms"]
    resp = requests.post(
        thsms["api_endpoint"],
        headers={
            "Authorization": f"Bearer {thsms['api_token']}",
            "Content-Type": "application/json",
        },
        json={"from": thsms["sender"], "to": phone, "text": message},
        timeout=20,
    )
    return resp.status_code, resp.text


def load_links(path):
    """อ่านลิงก์ที่ GoPhish สร้างไว้แล้ว (employee_id, phone, link)"""
    full = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        sys.exit(f"ไม่พบไฟล์ลิงก์: {full} — รัน gophish_bridge.py ก่อน")
    with open(full, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(description="ส่ง SMS จำลองเพื่อฝึกอบรม")
    parser.add_argument("--live", action="store_true",
                        help="ส่งจริง (ต้องมี AUTHORIZATION.txt ครบ). ไม่ใส่ = dry-run")
    parser.add_argument("--from-links", metavar="CSV",
                        help="ใช้ลิงก์ที่ GoPhish สร้างไว้ (campaign_links.csv) แทนการสร้างลิงก์เอง")
    args = parser.parse_args()

    cfg = load_config()
    template = cfg["campaign"]["message_template"]

    # รวมรายการเป้าหมายเป็นรูปแบบเดียว: {employee_id, phone, link}
    if args.from_links:
        targets = load_links(args.from_links)
    else:
        base_url = cfg["campaign"]["base_url"]
        targets = [{
            "employee_id": e["employee_id"],
            "phone": e["phone"],
            "link": build_link(base_url, e["employee_id"]),
        } for e in load_employees()]

    if args.live:
        ok, reason = authorization_ok()
        if not ok:
            sys.exit(f"❌ ปฏิเสธการส่งจริง: {reason}\n"
                     f"   กรอก AUTHORIZATION.txt ให้ครบก่อน หรือรันแบบ dry-run (ไม่ใส่ --live)")
        token = cfg["thsms"]["api_token"]
        if not token or token.startswith("PASTE_"):
            sys.exit("❌ ยังไม่ได้ตั้งค่า api_token ใน config.json")

    mode = "LIVE (ส่งจริง)" if args.live else "DRY-RUN (ทดสอบ ไม่ส่งจริง)"
    src = f"จากลิงก์ GoPhish ({args.from_links})" if args.from_links else "สร้างลิงก์เอง"
    print(f"=== โหมด: {mode} | {src} | เป้าหมาย {len(targets)} คน ===\n")

    for t in targets:
        message = template.format(link=t["link"])
        if args.live:
            code, body = send_sms(cfg, t["phone"], message)
            status = "OK" if code == 200 else f"FAIL({code})"
            print(f"[{status}] {t['employee_id']} {t['phone']}: {body[:80]}")
        else:
            print(f"[DRY] {t['employee_id']} {t['phone']}")
            print(f"      ข้อความ: {message}\n")

    if not args.live:
        print("นี่คือการทดสอบ ยังไม่มี SMS ถูกส่ง — เพิ่ม --live เพื่อส่งจริง (ต้องมี AUTHORIZATION.txt)")


if __name__ == "__main__":
    main()
