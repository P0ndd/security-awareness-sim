# start.ps1 — เปิด server + Cloudflare tunnel แล้วแสดง public link (รันไฟล์เดียวจบ)
#
# วิธีรัน (ใน PowerShell):
#   cd "security-awareness-sim"
#   ./start.ps1
#
# ถ้ารันไม่ได้เพราะ execution policy ให้สั่งครั้งเดียว:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#
# กด Ctrl+C เพื่อหยุด server + tunnel

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$port = 8080

# 1) ตรวจ/ติดตั้ง Python packages ที่จำเป็น
Write-Host "[1/4] ตรวจสอบ Python packages..." -ForegroundColor Cyan
python -m pip install -q flask requests 2>$null

# 2) ดาวน์โหลด cloudflared ถ้ายังไม่มี (ไฟล์เดียว ไม่ต้องติดตั้ง)
$cf = Join-Path $PSScriptRoot "cloudflared.exe"
if (-not (Test-Path $cf)) {
    Write-Host "[2/4] ดาวน์โหลด cloudflared..." -ForegroundColor Cyan
    $dl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $dl -OutFile $cf
} else {
    Write-Host "[2/4] พบ cloudflared แล้ว" -ForegroundColor Cyan
}

# 3) เปิด Flask server เป็น background process
Write-Host "[3/4] เปิดเซิร์ฟเวอร์ที่ localhost:$port..." -ForegroundColor Cyan
$server = Start-Process -FilePath "python" -ArgumentList "server.py" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

# 4) เปิด tunnel แล้วดึง public URL จาก log
Write-Host "[4/4] เปิด Cloudflare tunnel..." -ForegroundColor Cyan
$logFile = Join-Path $PSScriptRoot "tunnel.log"
if (Test-Path $logFile) { Remove-Item $logFile -Force }
$tunnel = Start-Process -FilePath $cf `
    -ArgumentList "tunnel", "--url", "http://localhost:$port" `
    -PassThru -RedirectStandardError $logFile -WindowStyle Hidden

$publicUrl = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $logFile) {
        $m = Select-String -Path $logFile -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" |
             Select-Object -First 1
        if ($m) { $publicUrl = $m.Matches[0].Value; break }
    }
}

if ($publicUrl) {
    # อัปเดต base_url ใน config.json ให้อัตโนมัติ (ถ้ามีไฟล์)
    $cfgPath = Join-Path $PSScriptRoot "config.json"
    if (Test-Path $cfgPath) {
        try {
            $cfg = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $cfg.campaign.base_url = $publicUrl
            $cfg | ConvertTo-Json -Depth 10 | Set-Content $cfgPath -Encoding UTF8
            $updated = "  (อัปเดต base_url ใน config.json ให้แล้ว)"
        } catch {
            $updated = "  (แก้ base_url ใน config.json เองเป็น: $publicUrl)"
        }
    }

    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host "  พร้อมใช้งาน! Public link:" -ForegroundColor Green
    Write-Host "    $publicUrl" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  ทดลองเปิดในมือถือ (ตัวอย่างพนักงาน EMP001):" -ForegroundColor Green
    Write-Host "    $publicUrl/t/EMP001" -ForegroundColor Yellow
    if ($updated) { Write-Host $updated -ForegroundColor Green }
    Write-Host ""
    Write-Host "  ขั้นต่อไป: python send_campaign.py            # ทดสอบ (ไม่ส่งจริง)" -ForegroundColor Green
    Write-Host "            python send_campaign.py --live     # ส่งจริง (ต้องมี AUTHORIZATION.txt)" -ForegroundColor Green
    Write-Host "            python report.py                   # ดูว่าใครคลิกบ้าง" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "กด Ctrl+C เพื่อหยุด server + tunnel" -ForegroundColor Cyan
} else {
    Write-Host "ไม่พบ public URL ภายใน 30 วินาที — ดูรายละเอียดใน tunnel.log" -ForegroundColor Red
}

# คงทำงานไว้จนกด Ctrl+C แล้วเก็บกวาด process ให้เรียบร้อย
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "`nกำลังหยุด server + tunnel..." -ForegroundColor Cyan
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force }
    if ($tunnel -and -not $tunnel.HasExited) { Stop-Process -Id $tunnel.Id -Force }
    Write-Host "หยุดเรียบร้อย" -ForegroundColor Cyan
}
