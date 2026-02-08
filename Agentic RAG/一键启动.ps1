# Agentic RAG 一键启动脚本
# PowerShell版本 - 同时启动后端和前端服务

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Agentic RAG System - One-Click Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"

# 检查Python是否安装
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "    $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "    ERROR: Python not found!" -ForegroundColor Red
    Write-Host "    Please install Python 3.8+ first" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 检查后端目录
Write-Host "[2/4] Checking backend directory..." -ForegroundColor Yellow
if (-not (Test-Path $backendDir)) {
    Write-Host "    ERROR: Backend directory not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "    Backend directory: $backendDir" -ForegroundColor Green

# 检查知识库是否初始化
Write-Host "[3/4] Checking knowledge base..." -ForegroundColor Yellow
$chromaDbPath = Join-Path $backendDir "chroma_db"
if (Test-Path $chromaDbPath) {
    Write-Host "    Knowledge base initialized" -ForegroundColor Green
} else {
    Write-Host "    WARNING: Knowledge base not initialized" -ForegroundColor Yellow
    Write-Host "    Run: cd backend && python init_kb.py" -ForegroundColor Yellow
}

# 启动后端服务
Write-Host "[4/4] Starting services..." -ForegroundColor Yellow
Write-Host ""

# 启动后端（新窗口）
Write-Host "Starting backend server (port 5000)..." -ForegroundColor Cyan
$backendScript = @"
cd `"$backendDir`"
python app.py
pause
"@

$backendScript | Out-File -FilePath "$env:TEMP\start_backend.ps1" -Encoding UTF8
Start-Process powershell -ArgumentList "-NoExit", "-File", "$env:TEMP\start_backend.ps1" -WindowStyle Normal

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端（新窗口）
Write-Host "Starting frontend server (port 8080)..." -ForegroundColor Cyan
$frontendScript = @"
cd `"$scriptDir`"
python -m http.server 8080
pause
"@

$frontendScript | Out-File -FilePath "$env:TEMP\start_frontend.ps1" -Encoding UTF8
Start-Process powershell -ArgumentList "-NoExit", "-File", "$env:TEMP\start_frontend.ps1" -WindowStyle Normal

# 等待前端启动
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Services Started Successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# 打开浏览器
Start-Process "http://localhost:8080"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Tips:" -ForegroundColor Cyan
Write-Host "  - Keep both PowerShell windows open" -ForegroundColor White
Write-Host "  - Close windows to stop services" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:5000/api/health" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit this window (services will keep running)..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
