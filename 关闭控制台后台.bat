@echo off
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$cwd=(Get-Location).Path; $pidFile=Join-Path $cwd 'control_panel.pid'; $targetPid=$null; if (Test-Path $pidFile) { $raw=Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1; if ($raw -match '^\d+$') { $targetPid=[int]$raw } }; if ($targetPid) { try { Stop-Process -Id $targetPid -Force -ErrorAction Stop; Remove-Item $pidFile -Force -ErrorAction SilentlyContinue; Write-Host ('[OK] Control panel stopped. PID=' + $targetPid); exit 0 } catch {} }; $conn=Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if ($conn) { try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop; Remove-Item $pidFile -Force -ErrorAction SilentlyContinue; Write-Host ('[OK] Control panel stopped. PID=' + $conn.OwningProcess); exit 0 } catch { Write-Host ('[ERROR] Failed to stop PID=' + $conn.OwningProcess); exit 1 } }; Write-Host '[INFO] No running control panel was found.'; exit 0"

if errorlevel 1 pause
