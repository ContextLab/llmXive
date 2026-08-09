#!/bin/bash
# T045: Validate quickstart.md against the implemented pipeline
# Success condition: Exit code 0 and no errors in logs/validation.log

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUICKSTART_PATH="$PROJECT_ROOT/specs/001-predict-weibull-modulus/quickstart.md"
LOG_FILE="$PROJECT_ROOT/logs/validation.log"
ERRORS=0

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Initialize log
echo "=== Quickstart Validation Run: $(date) ===" > "$LOG_FILE"

# Check 1: Verify quickstart.md exists
echo "Checking: $QUICKSTART_PATH" >> "$LOG_FILE"
if [ ! -f "$QUICKSTART_PATH" ]; then
    echo "ERROR: quickstart.md not found at $QUICKSTART_PATH" >> "$LOG_FILE"
    ERRORS=$((ERRORS + 1))
else
    echo "OK: quickstart.md found" >> "$LOG_FILE"
fi

# Check 2: Verify required directories exist (as per quickstart setup)
REQUIRED_DIRS=(
    "data/raw"
    "data/processed"
    "data/artifacts"
    "data/results"
    "data/models"
    "data/reports"
    "code"
    "tests"
    "specs/001-predict-weibull-modulus"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    echo "Checking directory: $dir" >> "$LOG_FILE"
    if [ ! -d "$PROJECT_ROOT/$dir" ]; then
        echo "ERROR: Directory missing: $dir" >> "$LOG_FILE"
        ERRORS=$((ERRORS + 1))
    else
        echo "OK: Directory exists: $dir" >> "$LOG_FILE"
    fi
done

# Check 3: Verify required code files exist (as per quickstart execution steps)
REQUIRED_FILES=(
    "code/ingestion.py"
    "code/descriptors.py"
    "code/modeling.py"
    "code/diagnostics.py"
    "code/report.py"
    "code/config.py"
    "code/contracts/generate_schemas.py"
    "code/hash_artifacts.py"
    "code/setup_directories.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    echo "Checking file: $file" >> "$LOG_FILE"
    if [ ! -f "$PROJECT_ROOT/$file" ]; then
        echo "ERROR: File missing: $file" >> "$LOG_FILE"
        ERRORS=$((ERRORS + 1))
    else
        echo "OK: File exists: $file" >> "$LOG_FILE"
    fi
done

# Check 4: Verify requirements.txt exists
echo "Checking: requirements.txt" >> "$LOG_FILE"
if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "ERROR: requirements.txt not found" >> "$LOG_FILE"
    ERRORS=$((ERRORS + 1))
else
    echo "OK: requirements.txt found" >> "$LOG_FILE"
fi

# Check 5: Verify Python syntax for all code files
echo "Checking Python syntax for code files..." >> "$LOG_FILE"
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        python3 -m py_compile "$PROJECT_ROOT/$file" 2>> "$LOG_FILE"
        if [ $? -eq 0 ]; then
            echo "OK: Syntax valid: $file" >> "$LOG_FILE"
        else
            echo "ERROR: Syntax invalid: $file" >> "$LOG_FILE"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# Check 6: Verify quickstart.md contains required sections
echo "Checking quickstart.md content..." >> "$LOG_FILE"
REQUIRED_SECTIONS=(
    "Setup"
    "Data Fetch"
    "Pipeline Execution"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
    if grep -q "$section" "$QUICKSTART_PATH"; then
        echo "OK: Section found: $section" >> "$LOG_FILE"
    else
        echo "WARNING: Section not found in quickstart.md: $section" >> "$LOG_FILE"
        # Not a fatal error, just a warning
    fi
done

# Final Summary
echo "=== Validation Complete: $(date) ===" >> "$LOG_FILE"
if [ $ERRORS -eq 0 ]; then
    echo "RESULT: SUCCESS - All critical checks passed" >> "$LOG_FILE"
    exit 0
else
    echo "RESULT: FAILURE - $ERRORS error(s) found" >> "$LOG_FILE"
    exit 1
fi