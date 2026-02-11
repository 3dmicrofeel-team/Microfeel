@echo off
chcp 65001 >nul
title Agentic RAG - Startup

echo ============================================================
echo Agentic RAG System - Startup
echo ============================================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"

REM 检查Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo     ERROR: Python not found!
    echo     Please install Python 3.8+ first
    pause
    exit /b 1
)
python --version
echo     OK
echo.

REM 检查后端目录
echo [2/4] Checking backend directory...
if not exist "%BACKEND_DIR%" (
    echo     ERROR: Backend directory not found!
    pause
    exit /b 1
)
echo     Backend directory: %BACKEND_DIR%
echo     OK
echo.

REM 检查知识库
echo [3/5] Checking knowledge base...
if exist "%BACKEND_DIR%\chroma_db" (
    echo     Map knowledge base initialized
) else (
    echo     WARNING: Map knowledge base not initialized
    echo     Run: cd backend ^&^& python init_kb.py
)

if exist "%BACKEND_DIR%\chroma_db_gameplay" (
    echo     Encounter knowledge base initialized
) else (
    echo     WARNING: Encounter knowledge base not initialized
    echo     Run: cd backend ^&^& python init_gameplay_kb.py
)
echo.

REM 快速查找可用端口（简化版本，只检查常用端口）
echo [4/5] Finding available ports...
set "BACKEND_PORT=5000"
set "FRONTEND_PORT=8080"

REM 检查后端端口（只检查5000和5001）
netstat -ano 2>nul | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    set "BACKEND_PORT=5001"
    netstat -ano 2>nul | findstr ":5001" | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_PORT=5002"
    )
)

REM 检查前端端口（只检查8080-8082）
netstat -ano 2>nul | findstr ":8080" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    set "FRONTEND_PORT=8081"
    netstat -ano 2>nul | findstr ":8081" | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (
        set "FRONTEND_PORT=8082"
    )
)

echo     Backend port: %BACKEND_PORT%
echo     Frontend port: %FRONTEND_PORT%
echo     OK
echo.

REM 初始化知识库（如果未初始化）
echo [5/5] Initializing knowledge bases (if needed)...
if not exist "%BACKEND_DIR%\chroma_db" (
    echo     Initializing map knowledge base...
    cd /d "%BACKEND_DIR%"
    python init_kb.py >nul 2>&1
    cd /d "%SCRIPT_DIR%"
)

if not exist "%BACKEND_DIR%\chroma_db_gameplay" (
    echo     Initializing encounter knowledge base...
    cd /d "%BACKEND_DIR%"
    python init_gameplay_kb.py >nul 2>&1
    cd /d "%SCRIPT_DIR%"
)
echo     OK
echo.

REM 启动服务
echo [6/6] Starting services...
echo.

REM 启动后端（新窗口）
echo Starting backend server (port %BACKEND_PORT%)...
start "Agentic RAG - Backend" cmd /k "cd /d "%BACKEND_DIR%" && set PORT=%BACKEND_PORT% && python app.py"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端（新窗口）
echo Starting frontend server (port %FRONTEND_PORT%)...
start "Agentic RAG - Frontend" cmd /k "cd /d "%SCRIPT_DIR%" && python -m http.server %FRONTEND_PORT%"

REM 等待前端启动
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo Services Started Successfully!
echo ============================================================
echo.
echo Backend:  http://localhost:%BACKEND_PORT%
echo Frontend: http://localhost:%FRONTEND_PORT%
echo.
echo Opening browser...
timeout /t 2 /nobreak >nul

REM 打开浏览器，并传递端口信息
start http://localhost:%FRONTEND_PORT%?backendPort=%BACKEND_PORT%

echo.
echo ============================================================
echo Services Started!
echo ============================================================
echo Backend:  http://localhost:%BACKEND_PORT%
echo Frontend: http://localhost:%FRONTEND_PORT%
echo.
echo Tips:
echo   - Keep both command windows open
echo   - Close windows to stop services
echo   - Backend API: http://localhost:%BACKEND_PORT%/api/health
echo.
echo NOTE: If frontend cannot connect to backend, check browser console
echo       and update backendPort in localStorage if needed.
echo ============================================================
echo.
echo Press any key to exit this window (services will keep running)...
pause >nul
