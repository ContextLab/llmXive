#!/bin/bash
# Validation script for quickstart.md instructions
# This script verifies that the project setup and basic execution work as documented.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

REPORT_FILE="data/quickstart_validation_report.txt"
ERRORS=0

echo "Starting Quickstart Validation..." > "$REPORT_FILE"
echo "Timestamp: $(date)" >> "$REPORT_FILE"
echo "----------------------------------------" >> "$REPORT_FILE"

# 1. Check directory structure
echo "Checking directory structure..." >> "$REPORT_FILE"
DIRS=("code" "data" "tests" "specs" "contracts")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  [PASS] Directory $dir exists" >> "$REPORT_FILE"
    else
        echo "  [FAIL] Directory $dir missing" >> "$REPORT_FILE"
        ERRORS=$((ERRORS + 1))
    fi
done

# 2. Check requirements.txt
echo "Checking requirements.txt..." >> "$REPORT_FILE"
if [ -f "requirements.txt" ]; then
    echo "  [PASS] requirements.txt exists" >> "$REPORT_FILE"
    # Check for essential packages
    if grep -q "pandas" requirements.txt && grep -q "pytest" requirements.txt; then
        echo "  [PASS] Essential packages found in requirements.txt" >> "$REPORT_FILE"
    else
        echo "  [FAIL] Missing essential packages in requirements.txt" >> "$REPORT_FILE"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  [FAIL] requirements.txt missing" >> "$REPORT_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 3. Check schema files
echo "Checking schema files..." >> "$REPORT_FILE"
SCHEMAS=("dataset.schema.yaml" "coverage.schema.yaml" "generated_test.schema.yaml" "analysis_result.schema.yaml")
for schema in "${SCHEMAS[@]}"; do
    if [ -f "contracts/$schema" ]; then
        echo "  [PASS] Schema $schema exists" >> "$REPORT_FILE"
    else
        echo "  [FAIL] Schema $schema missing" >> "$REPORT_FILE"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Check Python modules compile
echo "Checking Python module syntax..." >> "$REPORT_FILE"
MODULES=("code/config.py" "code/data_loader.py" "code/llm_generator.py" "code/test_executor.py" "code/analyzer.py" "code/main.py" "code/report_generator.py")
for module in "${MODULES[@]}"; do
    if python3 -m py_compile "$module" 2>/dev/null; then
        echo "  [PASS] $module compiles" >> "$REPORT_FILE"
    else
        echo "  [FAIL] $module syntax error" >> "$REPORT_FILE"
        ERRORS=$((ERRORS + 1))
    fi
done

# 5. Run main.py --help to verify entry point
echo "Checking main.py entry point..." >> "$REPORT_FILE"
if python3 code/main.py --help > /dev/null 2>&1; then
    echo "  [PASS] main.py --help executed successfully" >> "$REPORT_FILE"
else
    echo "  [FAIL] main.py --help failed" >> "$REPORT_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 6. Run quickstart validation helper
echo "Running quickstart validation helper..." >> "$REPORT_FILE"
if python3 code/run_quickstart_validation.py > /dev/null 2>&1; then
    echo "  [PASS] run_quickstart_validation.py executed successfully" >> "$REPORT_FILE"
else
    echo "  [FAIL] run_quickstart_validation.py failed" >> "$REPORT_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 7. Final summary
echo "----------------------------------------" >> "$REPORT_FILE"
if [ $ERRORS -eq 0 ]; then
    echo "PASS: All quickstart validations succeeded." >> "$REPORT_FILE"
    echo "Validation Status: PASS"
    exit 0
else
    echo "FAIL: $ERRORS validation(s) failed. See report for details." >> "$REPORT_FILE"
    echo "Validation Status: FAIL"
    exit 1
fi
