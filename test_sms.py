"""
ทดสอบส่ง SMS ทีละ 1 ข้อความ เพื่อแยกสาเหตุปัญหา delivery
(THSMS ตอบ success:true เสมอแม้ส่งไม่ถึง — ต้องดูผลที่ "มือถือจริง")

ตัวอย่าง:
  # ทดสอบข้อความไม่มีลิงก์ (ดูว่า sender ผ่านไหม)
  python test_sms.py --to 08xxxxxxxx --message "ทดสอบระบบ BMU"

  # ทดสอบข้อความมีลิงก์ (ดูว่าโดนกรอง URL ไหม)
  python test_sms.py --to 08xxxxxxxx --message "ดูรายละเอียด https://bmu-awareness.onrender.com"

  # ลองเปลี่ยน sender
  python test_sms.py --to 08xxxxxxxx --message "ทดสอบ" --sender "SMS"

อ่าน api_endpoint/api_token/sender จาก config.json (override sender ได้ด้วย --sender)
"""
import argparse
import json
import os
import sys

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    p = argparse.ArgumentParser(description="ทดสอบส่ง SMS 1 ข้อความ")
    p.add_argument("--to", required=True, help="เบอร์ปลายทาง เช่น 0812345678")
    p.add_argument("--message", required=True, help="ข้อความที่จะส่ง")
    p.add_argument("--sender", help="override ชื่อผู้ส่ง (ไม่ใส่ = ใช้จาก config.json)")
    args = p.parse_args()

    with open(os.path.join(BASE_DIR, "config.json"), encoding="utf-8") as f:
        thsms = json.load(f)["thsms"]
    sender = args.sender or thsms["sender"]

    resp = requests.post(
        thsms["api_endpoint"],
        headers={
            "Authorization": f"Bearer {thsms['api_token']}",
            "Content-Type": "application/json",
        },
        json={"sender": sender, "msisdn": [args.to], "message": args.message},
        timeout=20,
    )
    print(f"sender = {sender!r}")
    print(f"to     = {args.to}")
    print(f"HTTP {resp.status_code}: {resp.text}")
    print("\n>>> ไปเช็กที่มือถือปลายทางว่าข้อความเข้าไหม (API บอกแค่ 'รับเข้าคิว')")


if __name__ == "__main__":
    main()
