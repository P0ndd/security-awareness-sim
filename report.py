"""สรุปผลว่าใครคลิกลิงก์จำลองบ้าง จาก clicks.csv"""
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLICKS_FILE = os.path.join(BASE_DIR, "clicks.csv")


def main():
    if not os.path.exists(CLICKS_FILE):
        print("ยังไม่มีข้อมูลการคลิก (clicks.csv ยังไม่ถูกสร้าง)")
        return
    with open(CLICKS_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    unique = {}
    for r in rows:
        unique.setdefault(r["employee_id"], r["timestamp"])

    print(f"=== สรุปผล Phishing Simulation ===")
    print(f"จำนวนการคลิกทั้งหมด: {len(rows)} ครั้ง")
    print(f"จำนวนพนักงานที่หลงคลิก (ไม่ซ้ำ): {len(unique)} คน\n")
    print(f"{'รหัสพนักงาน':<15}{'คลิกครั้งแรกเมื่อ'}")
    print("-" * 40)
    for emp_id, ts in sorted(unique.items()):
        print(f"{emp_id:<15}{ts}")


if __name__ == "__main__":
    main()
