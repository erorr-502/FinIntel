@echo off
setlocal
cd /d "%~dp0"
title FININTEL Launcher
echo.
echo ========================================
echo        FININTEL - The AI Market Daily
echo ========================================
echo.

if not exist venv\Scripts\python.exe (
    echo Creating project virtual environment...
    python -m venv venv
    if errorlevel 1 goto :error
)

call venv\Scripts\activate
if errorlevel 1 goto :error

echo Installing / checking requirements...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Starting FININTEL...
python -m streamlit run app.py
if errorlevel 1 goto :error

goto :end

:error
echo.
echo FININTEL could not start. Open this folder in VS Code and run:
echo   venv\Scripts\activate
echo   python -m pip install -r requirements.txt
echo   python -m streamlit run app.py
echo.
pause

:end
endlocal
