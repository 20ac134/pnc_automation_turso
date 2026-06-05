@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

title PnC Automation Tool - Windows Stop

echo ========================================
echo Stopping PnC Automation Tool
echo ========================================
echo.

REM Close the named cmd windows first (graceful — lets uvicorn/vite clean up)
echo Closing backend command window...
taskkill /FI "WINDOWTITLE eq PnC Backend*" /T >nul 2>&1

echo Closing frontend command window...
taskkill /FI "WINDOWTITLE eq PnC Frontend*" /T >nul 2>&1

REM Give them a moment to exit gracefully before force-killing.
timeout /t 2 /nobreak >nul

echo.
echo Checking for backend process on port %BACKEND_PORT%...
set "FOUND_BACKEND=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%BACKEND_PORT% "') do (
    echo Killing process %%a on port %BACKEND_PORT%...
    taskkill /PID %%a /T /F >nul 2>&1
    set "FOUND_BACKEND=1"
)
IF "!FOUND_BACKEND!"=="0" (
    echo No backend process found on port %BACKEND_PORT%.
)

echo.
echo Checking for frontend process on port %FRONTEND_PORT%...
set "FOUND_FRONTEND=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%FRONTEND_PORT% "') do (
    echo Killing process %%a on port %FRONTEND_PORT%...
    taskkill /PID %%a /T /F >nul 2>&1
    set "FOUND_FRONTEND=1"
)
IF "!FOUND_FRONTEND!"=="0" (
    echo No frontend process found on port %FRONTEND_PORT%.
)

echo.
echo ========================================
echo PnC Automation Tool stopped.
echo ========================================
echo.
pause