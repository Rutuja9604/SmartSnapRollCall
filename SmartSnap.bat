@echo off
title SmartSnap Attendance System

REM Go to the folder where this .bat file is located
cd /d "%~dp0"

echo =========================================
echo   SmartSnap Attendance System Starting...
echo =========================================

REM Check virtual environment
if not exist "studentenv\Scripts\activate.bat" (
    echo ERROR: Virtual environment 'studentenv' not found!
    pause
    exit /b
)

REM Activate virtual environment
call studentenv\Scripts\activate

REM Run application
python main.py

REM Keep window open if error occurs
pause
