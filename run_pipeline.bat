@echo off
cd /d "%~dp0"
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" geospatial
> outputs\logs\pipeline_log.txt echo START %DATE% %TIME%
echo [1/3] Collecting data...
python scripts\01_collect_data.py >> outputs\logs\pipeline_log.txt 2>&1 || goto :fail
echo [2/3] Building networks (first run downloads OSM, about 5-10 min)...
python scripts\02_build_networks.py >> outputs\logs\pipeline_log.txt 2>&1 || goto :fail
echo [3/3] Computing access metrics...
python scripts\03_access_metrics.py >> outputs\logs\pipeline_log.txt 2>&1 || goto :fail
>> outputs\logs\pipeline_log.txt echo FINISHED %DATE% %TIME%
echo Done. See outputs\logs\pipeline_log.txt
pause
exit /b 0
:fail
>> outputs\logs\pipeline_log.txt echo FAILED %DATE% %TIME%
echo Failed. See outputs\logs\pipeline_log.txt
pause
exit /b 1
