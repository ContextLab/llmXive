#!/bin/bash
set -euo pipefail

# ==============================================================================
# Test Script: code/tests/test_run_pipeline.sh
# ==============================================================================
# Verifies that run_pipeline.sh exists, is executable, and contains the
# expected orchestration logic (stubs for T008).
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PIPELINE_SCRIPT="$PROJECT_ROOT/code/run_pipeline.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

passed=0
failed=0

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((passed++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((failed++))
}

# Test 1: File Exists
test_file_exists() {
    if [[ -f "$PIPELINE_SCRIPT" ]]; then
        log_pass "run_pipeline.sh exists at $PIPELINE_SCRIPT"
    else
        log_fail "run_pipeline.sh not found at $PIPELINE_SCRIPT"
    fi
}

# Test 2: File is Executable
test_is_executable() {
    if [[ -x "$PIPELINE_SCRIPT" ]]; then
        log_pass "run_pipeline.sh is executable"
    else
        log_fail "run_pipeline.sh is not executable"
    fi
}

# Test 3: Contains Ingest Step
test_contains_ingest() {
    if grep -q "run_ingest" "$PIPELINE_SCRIPT"; then
        log_pass "run_pipeline.sh contains Ingest step"
    else
        log_fail "run_pipeline.sh missing Ingest step"
    fi
}

# Test 4: Contains Metrics Step
test_contains_metrics() {
    if grep -q "run_metrics" "$PIPELINE_SCRIPT"; then
        log_pass "run_pipeline.sh contains Metrics step"
    else
        log_fail "run_pipeline.sh missing Metrics step"
    fi
}

# Test 5: Contains Labeling Step
test_contains_labeling() {
    if grep -q "run_labeling" "$PIPELINE_SCRIPT"; then
        log_pass "run_pipeline.sh contains Labeling step"
    else
        log_fail "run_pipeline.sh missing Labeling step"
    fi
}

# Test 6: Contains Analysis Step (Stubbed)
test_contains_analysis() {
    if grep -q "run_analysis" "$PIPELINE_SCRIPT"; then
        log_pass "run_pipeline.sh contains Analysis step"
    else
        log_fail "run_pipeline.sh missing Analysis step"
    fi
}

# Test 7: Contains Validation Step
test_contains_validation() {
    if grep -q "run_validation" "$PIPELINE_SCRIPT"; then
        log_pass "run_pipeline.sh contains Validation step"
    else
        log_fail "run_pipeline.sh missing Validation step"
    fi
}

# Test 8: Contains Error Handling (set -euo pipefail)
test_error_handling() {
    if grep -q "set -euo pipefail" "$PIPELINE_SCRIPT"; then
        log_pass "run_pipeline.sh has strict error handling enabled"
    else
        log_fail "run_pipeline.sh missing strict error handling"
    fi
}

# Test 9: Verify Order (Ingest -> Metrics -> Labeling -> Validation -> Analysis)
test_execution_order() {
    # Extract line numbers of function calls
    ingest_line=$(grep -n "run_ingest" "$PIPELINE_SCRIPT" | head -1 | cut -d: -f1)
    metrics_line=$(grep -n "run_metrics" "$PIPELINE_SCRIPT" | head -1 | cut -d: -f1)
    labeling_line=$(grep -n "run_labeling" "$PIPELINE_SCRIPT" | head -1 | cut -d: -f1)
    validation_line=$(grep -n "run_validation" "$PIPELINE_SCRIPT" | head -1 | cut -d: -f1)
    analysis_line=$(grep -n "run_analysis" "$PIPELINE_SCRIPT" | head -1 | cut -d: -f1)

    if [[ -n "$ingest_line" && -n "$metrics_line" && -n "$labeling_line" && -n "$validation_line" && -n "$analysis_line" ]]; then
        if [[ $ingest_line -lt $metrics_line && $metrics_line -lt $labeling_line && $labeling_line -lt $validation_line && $validation_line -lt $analysis_line ]]; then
            log_pass "Execution order is correct: Ingest -> Metrics -> Labeling -> Validation -> Analysis"
        else
            log_fail "Execution order is incorrect"
        fi
    else
        log_fail "Could not determine line numbers for all steps"
    fi
}

# Run all tests
echo "Running Pipeline Script Tests..."
echo "--------------------------------"

test_file_exists
test_is_executable
test_contains_ingest
test_contains_metrics
test_contains_labeling
test_contains_analysis
test_contains_validation
test_error_handling
test_execution_order

echo "--------------------------------"
echo "Tests Passed: $passed"
echo "Tests Failed: $failed"

if [[ $failed -gt 0 ]]; then
    exit 1
fi
exit 0