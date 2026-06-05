@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

set "BACKEND_DIR=%ROOT%\vosyn-automation"
set "FRONTEND_DIR=%ROOT%\university-job-portal\university-job-portal"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

title PnC Automation Tool - Windows Launcher

echo ========================================
echo Starting PnC Automation Tool
echo ========================================
echo.
echo Root folder:
echo %CD%
echo.

REM -------------------------------
REM Check folders and prerequisites
REM -------------------------------
IF NOT EXIST "%BACKEND_DIR%" (
    echo ERROR: Backend folder not found:
    echo %BACKEND_DIR%
    pause
    exit /b 1
)

IF NOT EXIST "%FRONTEND_DIR%" (
    echo ERROR: Frontend folder not found:
    echo %FRONTEND_DIR%
    pause
    exit /b 1
)

IF NOT EXIST "%BACKEND_DIR%\env\Scripts\python.exe" (
    echo ERROR: Backend virtual environment not found or broken.
    echo Please run setup_windows.bat first.
    pause
    exit /b 1
)

IF NOT EXIST "%FRONTEND_DIR%\node_modules" (
    echo ERROR: Frontend node_modules not found.
    echo Please run setup_windows.bat first.
    pause
    exit /b 1
)

REM -------------------------------
REM Preflight: make sure ports are free
REM -------------------------------
netstat -ano | findstr "LISTENING" | findstr ":%BACKEND_PORT% " >nul 2>&1
IF NOT ERRORLEVEL 1 (
    echo ERROR: Port %BACKEND_PORT% is already in use.
    echo Run stop_pnc_tool_windows.bat first, then try again.
    pause
    exit /b 1
)

netstat -ano | findstr "LISTENING" | findstr ":%FRONTEND_PORT% " >nul 2>&1
IF NOT ERRORLEVEL 1 (
    echo ERROR: Port %FRONTEND_PORT% is already in use.
    echo Run stop_pnc_tool_windows.bat first, then try again.
    pause
    exit /b 1
)

REM -------------------------------
REM Start backend
REM -------------------------------
echo Starting backend...

REM Call the venv's python directly. No `call activate` needed.
start "PnC Backend" cmd /k "cd /d "%BACKEND_DIR%" && "env\Scripts\python.exe" -m uvicorn src.API.api:app --host 127.0.0.1 --port %BACKEND_PORT%"

echo Waiting for backend to be ready...
set "BACKEND_READY=0"
for /l %%i in (1,1,30) do (
    if "!BACKEND_READY!"=="0" (
        curl -s http://127.0.0.1:%BACKEND_PORT% >nul 2>&1
        if not errorlevel 1 (
            set "BACKEND_READY=1"
            echo Backend is up.
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)

IF "!BACKEND_READY!"=="0" (
    echo ERROR: Backend did not become ready within 30 seconds.
    echo Check the "PnC Backend" window for error messages.
    pause
    exit /b 1
)

REM -------------------------------
REM Start frontend
REM -------------------------------
echo Starting frontend...

start "PnC Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo Waiting for frontend to be ready...
set "FRONTEND_READY=0"
for /l %%i in (1,1,30) do (
    if "!FRONTEND_READY!"=="0" (
        curl -s http://127.0.0.1:%FRONTEND_PORT% >nul 2>&1
        if not errorlevel 1 (
            set "FRONTEND_READY=1"
            echo Frontend is up.
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)

IF "!FRONTEND_READY!"=="0" (
    echo ERROR: Frontend did not become ready within 30 seconds.
    echo Check the "PnC Frontend" window for error messages.
    pause
    exit /b 1
)

REM -------------------------------
REM Open browser
REM -------------------------------
echo Opening app...
start http://localhost:%FRONTEND_PORT%

echo.
echo ========================================
echo PnC Automation Tool started.
echo   Backend:  http://127.0.0.1:%BACKEND_PORT%
echo   Frontend: http://127.0.0.1:%FRONTEND_PORT%
echo.
echo Keep the backend and frontend windows open.
echo To stop, run:
echo   launchers\windows\stop_pnc_tool_windows.bat
echo ========================================
echo.
pause