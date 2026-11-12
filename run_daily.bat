@echo off
cd /d F:\Github4
call C:\venvs\energy\Scripts\activate.bat
python daily.py >> logs\daily.log 2>&1
python dashboard.py >> logs\daily.log 2>&1