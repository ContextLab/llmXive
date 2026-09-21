@echo off
setlocal enabledelayedexpansion

echo === PROJ-342 CI Pipeline: Final Verification (Windows) ===

REM 1. Setup Environment
echo [1/6] Setting up environment...
if exist .env (
    for /f "tokens=1,* delims==" %%a in ('findstr /v "^#" .env') do set "%%a=%%b"
)
set PYTHONPATH=%PYTHONPATH%;%CD%\code

REM 2. Data Ingestion
echo [2/6] Running data ingestion...
python code\ingest.py
if not exist data\processed\cleaned_mg.csv (
    echo ERROR: data\processed\cleaned_mg.csv not found.
    exit /b 1
)

REM 3. Feature Engineering
echo [3/6] Computing descriptors...
python code\descriptors.py
if not exist data\processed\descriptors.csv (
    echo ERROR: data\processed\descriptors.csv not found.
    exit /b 1
)

REM 4. Model Training
echo [4/6] Training model with LOFO CV...
python code\train.py
if not exist artifacts\models\best_model.pkl (
    echo ERROR: artifacts\models\best_model.pkl not found.
    exit /b 1
)

REM 5. Analysis
echo [5/6] Running analysis...
python code\analyze.py
if not exist data\processed\vif_diagnostic_log.json (
    echo ERROR: data\processed\vif_diagnostic_log.json not found.
    exit /b 1
)
if not exist artifacts\metrics\sensitivity_analysis.json (
    echo ERROR: artifacts\metrics\sensitivity_analysis.json not found.
    exit /b 1
)

REM 6. Reporting
echo [6/6] Generating final report...
python code\report.py
if not exist artifacts\reports\final_report.md (
    echo ERROR: artifacts\reports\final_report.md not found.
    exit /b 1
)

REM Final Verification
echo === Final Verification Checks ===
findstr /C:"These findings are associational only" artifacts\reports\final_report.md >nul
if %errorlevel% neq 0 (
    echo FAIL: Mandatory phrase not found.
    exit /b 1
)

echo === CI Pipeline Completed Successfully ===
exit /b 0