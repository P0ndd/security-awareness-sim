# ระบบจำลอง Phishing เพื่อฝึกอบรมพนักงาน (Security Awareness Simulation)

เครื่องมือนี้ใช้สำหรับ **การฝึกอบรมความปลอดภัยไซเบอร์ภายในองค์กรเท่านั้น**
จุดประสงค์คือสอนให้พนักงานมีวิจารณญาณก่อนคลิกลิงก์ที่น่าสงสัย โดยส่ง **SMS จำลอง**
ที่มีลิงก์ ซึ่งเมื่อคลิกแล้วจะพาไปยัง **หน้าให้ความรู้ (เฉลย)** ไม่ใช่หน้าขโมยข้อมูลจริง

ระบบเก็บแค่ "ใครคลิก + เวลา" เพื่อใช้จัดอบรมต่อ — ไม่มีการเก็บรหัสผ่านหรือข้อมูลส่วนตัวใด ๆ

---

## ⚖️ ข้อบังคับก่อนใช้งาน (สำคัญมาก — อ่านก่อน)

การส่งข้อความหลอกลวงไปยังบุคคลโดยไม่ได้รับอนุญาต แม้จะเป็นพนักงานเอง อาจผิดกฎหมาย
(พ.ร.บ.คอมพิวเตอร์ / PDPA) ดังนั้นก่อนรันจริง **ต้องครบทุกข้อ**:

1. ✅ ได้รับอนุมัติเป็นลายลักษณ์อักษรจากผู้บริหาร / HR / เจ้าของข้อมูล — กรอกใน `AUTHORIZATION.txt`
2. ✅ มีขอบเขตชัดเจน: รายชื่อพนักงานเป้าหมาย, ช่วงเวลา, ผู้รับผิดชอบ
3. ✅ เก็บข้อมูลเท่าที่จำเป็น (ใครคลิก + เวลา) เพื่อการอบรมเท่านั้น ไม่นำไปลงโทษ/ประจาน
4. ✅ ไม่ปลอมเป็นสถาบันภายนอก (ธนาคาร, หน่วยงานรัฐ) — ใช้บริบทภายในองค์กรเท่านั้น
5. ✅ ไม่ส่งข้อความข่มขู่รุนแรง (ไล่ออก/ฟ้องร้อง) และส่งในเวลาที่เหมาะสม
6. ✅ มีแผนแจ้งผล + อบรมซ้ำสำหรับผู้ที่คลิก

> `send_campaign.py` ทำงานแบบ **dry-run (ทดสอบ ไม่ส่งจริง)** เป็นค่าเริ่มต้น
> และจะยอมส่งจริงก็ต่อเมื่อมีไฟล์ `AUTHORIZATION.txt` ที่กรอกครบ **และ** ใส่ flag `--live`

---

## 📁 โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|------|--------|
| `server.py` | เว็บเซิร์ฟเวอร์: รับการคลิกที่ `/t/<employee_id>` → บันทึกลง `clicks.csv` → แสดงหน้าเฉลย |
| `send_campaign.py` | อ่านรายชื่อ/ลิงก์ + ส่ง SMS จำลอง (dry-run เป็นค่าเริ่มต้น) |
| `report.py` | สรุปสถิติผู้คลิกจาก `clicks.csv` |
| `make_links.py` | (ทางเลือก) วนสร้าง short link ต่อคนอัตโนมัติ → `campaign_links.csv` (ใช้ is.gd; ดูข้อจำกัดด้านล่าง) |
| `render.yaml` | Blueprint สำหรับ deploy `server.py` ขึ้น Render |
| `start.ps1` | สคริปต์รันไฟล์เดียวจบ: เปิด server + Cloudflare tunnel + แสดง public link |
| `cloudflared.exe` | โปรแกรม Cloudflare Tunnel (ไฟล์เดียว ไม่ต้องติดตั้ง) |
| `templates/awareness.html` | หน้า landing (หน้าเฉลย 404 + สเปซแมน) |
| `static/style.css`, `static/script.js` | สไตล์ + อนิเมชัน (GSAP 3) ของหน้า landing |
| `config.example.json` → `config.json` | ตั้งค่า: THSMS token, ชื่อผู้ส่ง, ข้อความ, `base_url` |
| `employees.example.csv` → `employees.csv` | รายชื่อเป้าหมาย: `employee_id,name,phone` |
| `campaign_links.csv` | (ทางเลือก) ลิงก์สำเร็จรูปต่อคน สำหรับโหมด `--from-links` เช่น short link |
| `AUTHORIZATION.example.txt` → `AUTHORIZATION.txt` | เอกสารอนุมัติ (ต้องกรอกก่อนส่งจริง) |
| `clicks.csv` | ไฟล์บันทึกการคลิก (สร้าง/ต่อท้ายอัตโนมัติ) |

> ไฟล์ `config.json`, `employees.csv`, `clicks.csv`, `AUTHORIZATION.txt` ถูก gitignore ไว้
> เพราะมี token / เบอร์โทร / ข้อมูลการคลิก — **อย่า commit ขึ้น git**

---

## 📦 การติดตั้ง (ครั้งเดียว)

```powershell
cd "security-awareness-sim"
pip install -r requirements.txt
copy config.example.json config.json
copy employees.example.csv employees.csv
copy AUTHORIZATION.example.txt AUTHORIZATION.txt
```

จากนั้นแก้ไข:
- **`config.json`** — ใส่ `thsms.api_token`, `thsms.sender` (ชื่อผู้ส่งที่ลงทะเบียนกับ THSMS แล้ว) และปรับข้อความ `message_template`
- **`employees.csv`** — ใส่รายชื่อ/เบอร์เป้าหมาย (คอลัมน์: `employee_id,name,phone`)
- **`AUTHORIZATION.txt`** — กรอกผู้อนุมัติ/ตำแหน่ง/วันที่/ขอบเขต ให้ครบ (ถ้าจะส่งจริง)

---

## 🚀 วิธีใช้งาน (โหมดเร็วสุด — แนะนำ)

รัน `start.ps1` ไฟล์เดียว จะเปิด server + tunnel + แสดง public link ให้อัตโนมัติ:

```powershell
cd "security-awareness-sim"
./start.ps1
```

ถ้ารันไม่ได้เพราะ execution policy ให้สั่งครั้งเดียวก่อน:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

สคริปต์จะ:
1. ตรวจ/ติดตั้ง flask, requests
2. เปิด Flask server ที่ `localhost:8080`
3. เปิด Cloudflare tunnel → ได้ public URL (เช่น `https://random-words.trycloudflare.com`)
4. อัปเดต `base_url` ใน `config.json` ให้อัตโนมัติ + แสดงลิงก์ทดสอบ

จากนั้น (หน้าต่างใหม่):
```powershell
python send_campaign.py                          # ทดสอบ (ไม่ส่งจริง)
python send_campaign.py --live                   # ส่งจริง (ต้องมี AUTHORIZATION.txt ครบ)
python report.py                                 # ดูว่าใครคลิกบ้าง
```

> กด `Ctrl+C` ในหน้าต่าง `start.ps1` เพื่อหยุด server + tunnel พร้อมกัน

---

## 🔧 วิธีใช้งาน (โหมดแยกขั้นตอน — ถ้าอยากคุมเอง)

### 1) เปิดเซิร์ฟเวอร์หน้าเฉลย
```powershell
python server.py                                 # รันที่ localhost:8080
```
ทดสอบบนเครื่องนี้: เปิด `http://localhost:8080/t/EMP001` ควรเห็นหน้าเฉลย และมีแถวใหม่ใน `clicks.csv`

### 2) เปิด tunnel เพื่อให้เข้าจากภายนอกได้
```powershell
./cloudflared.exe tunnel --url http://localhost:8080
```
ได้ public URL → นำไปใส่ `base_url` ใน `config.json`

### 3) ส่ง + ดูผล
```powershell
python send_campaign.py                          # dry-run
python send_campaign.py --live                   # ส่งจริง
python report.py                                 # สรุปผล
```

---

## 🔗 ลิงก์ tracking ทำงานอย่างไร

ลิงก์ต่อคนมีรูปแบบ:
```
https://<โดเมนของคุณ>/t/<employee_id>
```
เมื่อพนักงานคลิก → `server.py` บันทึก `timestamp, employee_id, user_agent` ลง `clicks.csv`
แล้วแสดงหน้าเฉลย โดย `send_campaign.py` จะสร้างลิงก์นี้จาก `base_url` + `/t/` + `employee_id` ให้อัตโนมัติ

---

## 🎭 การซ่อนลิงก์ด้วย Short URL (เช่น shorturl.asia)

ถ้าอยากให้ลิงก์ดูเนียนขึ้น (ไม่โชว์โดเมน trycloudflare แปลก ๆ) ใช้ short link ได้ แต่ **ต้องเข้าใจ 2 ข้อจำกัด**:

1. **Short link แม็ป "โค้ดเดียว → ปลายทางเดียว"** ต่อ path เพิ่มไม่ได้
   - ❌ ผิด: ตั้ง `base_url = https://shorturl.asia/XXXX` แล้วให้สคริปต์ต่อ `/t/EMP001` → กลายเป็น
     `https://shorturl.asia/XXXX/t/EMP001` ซึ่ง **ใช้ไม่ได้**
   - ✅ ถูก: ให้ short link ชี้ตรงไปที่ **ลิงก์เต็มรวม `/t/<id>` แล้ว** เช่น
     `XXXX` → `https://<tunnel>.trycloudflare.com/t/EMP001`
     แล้วส่งผ่านโหมด `--from-links` (ดูด้านล่าง) เพื่อไม่ให้สคริปต์ต่อ path ซ้ำ

2. **Short link ไม่ทะลุการบล็อก DNS** — สุดท้ายมัน redirect ไปโดเมนปลายทางอยู่ดี
   ถ้าเครือข่ายเป้าหมายบล็อกโดเมนนั้น (ดูหัวข้อ Troubleshooting) short link ก็ช่วยไม่ได้

**วิธีส่งด้วย short link (โหมด `--from-links`):**

สร้างไฟล์ `campaign_links.csv` โดยใส่ short link เป็นลิงก์สำเร็จรูป:
```csv
employee_id,phone,link
IT00008,0855208351,https://shorturl.asia/XXXX
```
แล้วส่ง:
```powershell
python send_campaign.py --from-links campaign_links.csv           # dry-run
python send_campaign.py --from-links campaign_links.csv --live    # ส่งจริง
```
โหมดนี้ใช้ค่าในคอลัมน์ `link` ตรง ๆ ไม่แตะ `base_url` และไม่ต่อ `/t/` เพิ่ม
เมื่อคลิก short link → redirect ไป `/t/IT00008` → `server.py` บันทึกการคลิกได้ตามปกติ

> ⚠️ ต้องแก้ปลายทางของ short link ทุกครั้งที่ tunnel URL เปลี่ยน (ดูหัวข้อถัดไป)

---

## 🎨 ปรับแต่งหน้า landing

หน้าเฉลยอยู่ที่ `templates/awareness.html` (สไตล์/อนิเมชันใน `static/`) แก้ข้อความ/ภาพได้ตามต้องการ
ควรให้หน้านี้ **เผยชัดเจนว่าเป็นการทดสอบ** พร้อมสอนจุดสังเกตของ phishing

> หลังแก้ template แล้ว **ต้องรีสตาร์ท `server.py`** เพราะ Flask แคช template ไว้ในหน่วยความจำ
> (ไฟล์ static เช่น css/js ไม่ต้องรีสตาร์ท โหลดใหม่ทุกครั้งอยู่แล้ว)

---

## 🩺 Troubleshooting

**`DNS_PROBE_FINISHED_NXDOMAIN` เวลาเปิดลิงก์**
- สาเหตุที่พบบ่อย: **เครือข่ายของอุปกรณ์ที่เปิดบล็อก `*.trycloudflare.com`** (WiFi องค์กรหลายที่บล็อกไว้)
- ทดสอบ: เปิดลิงก์ด้วย **เน็ตมือถือ (4G/5G)** — ถ้าเข้าได้ = WiFi ที่ใช้บล็อก trycloudflare
- ทางแก้: เปลี่ยน DNS อุปกรณ์เป็น `1.1.1.1`/`8.8.8.8`, หรือใช้ **named tunnel + โดเมนบริษัท** (ดูด้านล่าง)
- ตรวจว่าเครื่องเซิร์ฟเวอร์ resolve ได้ไหม: `Resolve-DnsName <ชื่อโดเมน>.trycloudflare.com`

**ลิงก์เดิมใช้ไม่ได้หลังรันใหม่**
- Cloudflare quick tunnel **สุ่ม subdomain ใหม่ทุกครั้ง** — URL เก่าจะตายทันที
- ต้องอัปเดต `base_url` (หรือปลายทาง short link) ด้วย URL ใหม่ทุกครั้ง — `start.ps1` อัปเดต `base_url` ให้อัตโนมัติแล้ว

**แก้ template/หน้าเว็บแล้วไม่เปลี่ยน**
- รีสตาร์ท `server.py` (Flask แคช template)

**ตรวจว่า tunnel ทำงานจริงไหม (จากเครื่องเซิร์ฟเวอร์)**
```powershell
Invoke-WebRequest -Uri "http://localhost:8080/t/EMP001" -UseBasicParsing   # ทดสอบ local
Invoke-WebRequest -Uri "https://<tunnel>.trycloudflare.com/t/EMP001" -UseBasicParsing  # ทดสอบผ่าน tunnel
```
ได้ HTTP 200 ทั้งคู่ = ระบบปกติ ปัญหาอยู่ที่อุปกรณ์/เครือข่ายฝั่งผู้เปิด

---

## 🌐 ทางเลือกสำหรับงานจริง (ลิงก์ถาวร + ไม่โดนบล็อก)

quick tunnel เหมาะกับ **ทดสอบ/เดโมสั้น ๆ** แต่มีข้อจำกัด (URL เปลี่ยนทุกครั้ง + อาจโดน WiFi บล็อก)
สำหรับแคมเปญจริงในองค์กร แนะนำอย่างใดอย่างหนึ่ง:

1. **Cloudflare named tunnel + subdomain ของบริษัท** (เช่น `training.bmu.co.th`)
   - URL คงที่ ไม่เปลี่ยน, ดูน่าเชื่อถือ, และไม่โดน filter ของบริษัทเอง
   - ต้องมีบัญชี Cloudflare ที่จัดการ DNS ของโดเมนบริษัท
2. **Deploy `server.py` ขึ้น cloud** (VPS / Render / Railway) หลัง HTTPS
3. **รันในวง LAN** แล้วใช้ IP ภายใน (เข้าได้เฉพาะคนในวงเดียวกัน — ไม่ต้องออกเน็ต)

---

## ☁️ Deploy บน Render (โดเมนคงที่ ไม่ต้องใช้ tunnel/shortener)

ยกเฉพาะ **หน้า tracking (`server.py`)** ขึ้น Render จะได้โดเมน HTTPS คงที่ (`https://<ชื่อ>.onrender.com`)
ที่ต่อ `/t/<รหัสพนักงาน>` ได้เองอยู่แล้ว — ไม่ต้องใช้ shortener และไม่โดนปัญหา URL เปลี่ยนทุกครั้ง

> การส่ง SMS (`send_campaign.py`) ยัง **รันในเครื่องคุณ** เหมือนเดิม token/เบอร์โทรจึงไม่ขึ้น cloud
> บน Render มีแค่หน้า landing + ตัวเก็บคลิกเท่านั้น

### ขั้นตอน
1. push โฟลเดอร์ `security-awareness-sim` ขึ้น GitHub (ให้เป็น repo root)
   ```powershell
   cd "security-awareness-sim"
   git init; git add .; git commit -m "awareness tracking server"
   # แล้ว push ขึ้น GitHub repo ของคุณ
   ```
   > `.gitignore` กันไฟล์ลับ (`config.json`, `employees.csv`, `clicks.csv`, `AUTHORIZATION.txt`) ไม่ให้ขึ้น git อยู่แล้ว
2. Render Dashboard > **New > Blueprint** > เลือก repo → Render อ่าน `render.yaml` สร้าง service ให้
   (หรือ New > Web Service แล้วตั้ง Start Command: `gunicorn server:app --bind 0.0.0.0:$PORT`)
3. รอ deploy เสร็จ จะได้ URL เช่น `https://bmu-awareness.onrender.com`
4. เอา URL นั้นใส่ `base_url` ใน `config.json` (ในเครื่อง) แล้วส่งได้เลย:
   ```powershell
   python send_campaign.py                 # dry-run
   python send_campaign.py --live          # ส่งจริง
   ```

### ดูผลว่าใครคลิก (ดึงจาก Render)
Render free ใช้ **ดิสก์ชั่วคราว** — `clicks.csv` จะรีเซ็ตเมื่อ redeploy/สปินดาวน์ จึงต้องดึงผลผ่าน endpoint:
```
https://<ชื่อ>.onrender.com/export?token=<ADMIN_TOKEN>
```
`ADMIN_TOKEN` ดูได้ที่ Render > service > แท็บ **Environment** (render.yaml สั่งสุ่มให้อัตโนมัติ)
เปิดลิงก์นี้จะดาวน์โหลด `clicks.csv` มาดูด้วย `report.py` ได้

### ข้อควรรู้ของ Render free
- **สปินดาวน์หลังไม่มีทราฟฟิก ~15 นาที** — คลิกแรกหลังพักจะโหลดช้า ~50 วิ (แต่ยังเข้าได้)
- **ดิสก์ชั่วคราว** — ดึง `/export` มาเก็บบ่อย ๆ หรืออัปเกรดเพิ่ม persistent disk แล้วตั้ง env `DATA_DIR=/data`
- onrender.com เป็นโดเมน cloud ทั่วไป โอกาสโดน WiFi องค์กรบล็อกน้อยกว่า trycloudflare มาก

### กันสปินดาวน์ด้วย GitHub Actions (all-in-one ในรีโป)
มี workflow `.github/workflows/keep-alive.yml` ที่ ping `/` ทุก ~10 นาทีให้ในตัว ไม่ต้องใช้บริการนอก:
1. หลัง deploy ได้ URL แล้ว ไปที่ GitHub repo > **Settings > Secrets and variables > Actions > Variables**
2. เพิ่มตัวแปร **`RENDER_URL`** = `https://<ชื่อ>.onrender.com`
3. workflow จะเริ่มทำงานอัตโนมัติ (กดทดสอบเองได้ที่แท็บ Actions > keep-alive > Run workflow)

> - cron ของ GitHub อาจดีเลย์ได้บ้าง ไม่เป๊ะทุก 10 นาที — เพียงพอสำหรับ keep-alive
> - **repo public** = Actions ฟรีไม่จำกัด | **repo private** = ฟรี 2000 นาที/เดือน (ping ทุก 10 นาทีตลอดเดือนจะเกินเล็กน้อย — ถ้ารันไม่ถึงเดือนก็มักไม่ถึงเพดาน)
> - ปิด keep-alive เมื่อจบแคมเปญ: ปิด workflow ที่แท็บ Actions หรือลบไฟล์ออก

---

## 🔒 หมายเหตุด้านจริยธรรม

เครื่องมือนี้ออกแบบให้ **สอน ไม่ใช่หลอกเอาข้อมูล**:
- ไม่มีช่องกรอกรหัสผ่าน/ข้อมูลส่วนตัวในหน้า landing
- เก็บเฉพาะ "รหัสพนักงานที่คลิก + เวลา" เพื่อจัดอบรม
- หน้า landing ควรเผยทันทีว่าเป็นการทดสอบ พร้อมสอนจุดสังเกต

หากนำไปใช้นอกเหนือการอบรมที่ได้รับอนุญาต ถือเป็นการใช้งานผิดวัตถุประสงค์
