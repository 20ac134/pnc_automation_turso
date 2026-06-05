@echo off
setlocal

REM Always run from this script's own folder, so it doesn't matter
REM where the user double-clicks it from.
cd /d "%~dp0"

echo ========================================
echo PnC Automation Tool - Debug Info
echo ========================================
echo.
echo Current folder:
cd
echo.

echo --- Project structure ---
dir /b
echo.

echo --- Backend folder ---
IF EXIST "vosyn-automation" (
    echo OK - vosyn-automation found
) ELSE (
    echo MISSING - vosyn-automation
)

echo --- Backend venv python ---
IF EXIST "vosyn-automation\env\Scripts\python.exe" (
    echo OK - venv python.exe found
) ELSE (
    echo MISSING - vosyn-automation\env\Scripts\python.exe
)

echo --- Backend requirements.txt ---
IF EXIST "vosyn-automation\requirements.txt" (
    echo OK - requirements.txt found
) ELSE (
    echo MISSING - vosyn-automation\requirements.txt
)

echo --- Frontend folder ---
IF EXIST "university-job-portal\university-job-portal" (
    echo OK - frontend folder found
) ELSE (
    echo MISSING - university-job-portal\university-job-portal
)

echo --- Frontend node_modules ---
IF EXIST "university-job-portal\university-job-portal\node_modules" (
    echo OK - node_modules found
) ELSE (
    echo MISSING - university-job-portal\university-job-portal\node_modules
)

echo --- Launcher scripts ---
IF EXIST "launchers\windows\setup_windows.bat" (
    echo OK - setup_windows.bat
) ELSE (
    echo MISSING - launchers\windows\setup_windows.bat
)
IF EXIST "launchers\windows\start_pnc_tool_windows.bat" (
    echo OK - start_pnc_tool_windows.bat
) ELSE (
    echo MISSING - launchers\windows\start_pnc_tool_windows.bat
)

echo.
echo --- Python on PATH ---
where python 2>nul
IF ERRORLEVEL 1 echo NOT FOUND on PATH

echo.
echo --- Node on PATH ---
where node 2>nul
IF ERRORLEVEL 1 echo NOT FOUND on PATH

echo.
echo --- npm on PATH ---
where npm 2>nul
IF ERRORLEVEL 1 echo NOT FOUND on PATH

echo.
echo --- Ports in use ---
echo Port 8000:
netstat -ano | findstr "LISTENING" | findstr ":8000 "
IF ERRORLEVEL 1 echo   ^(free^)
echo Port 5173:
netstat -ano | findstr "LISTENING" | findstr ":5173 "
IF ERRORLEVEL 1 echo   ^(free^)

echo.
echo ========================================
echo Done. Screenshot or copy this output.
echo ========================================
echo.
pause