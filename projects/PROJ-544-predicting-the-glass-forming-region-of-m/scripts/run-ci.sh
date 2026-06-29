#!/bin/bash
# CI Sanity Check Script for Glass-Forming Region Prediction Pipeline
# Usage: scripts/run-ci.sh --dry-run
#
# This script attempts to execute every script under code/ and scripts/
# without manual input, satisfying Constitution I's requirement that all
# scripts be runnable end-to-end.
#
# In dry-run mode (--dry-run), it performs syntax validation only.
# Without --dry-run, it executes scripts with minimal arguments.

set -o pipefail

# Configuration
DRY_RUN=false
LOG_FILE="logs/env_check.log"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Ensure log directory exists
mkdir -p logs

# Initialize log file
{
  echo "========================================"
  echo "CI Sanity Check Log"
  echo "Timestamp: $(date -Iseconds)"
  echo "Dry Run Mode: $DRY_RUN"
  echo "Project Root: $PROJECT_ROOT"
  echo "========================================"
  echo ""
} > "$LOG_FILE"

# Track results
TOTAL=0
PASSED=0
FAILED=0

# Function to run a Python script
run_python_script() {
  local script="$1"
  TOTAL=$((TOTAL + 1))
  local script_name=$(basename "$script")
  local script_dir=$(dirname "$script")

  echo "Testing Python script: $script" >> "$LOG_FILE"

  if [ "$DRY_RUN" = true ]; then
    # Dry run - syntax check only
    if python -m py_compile "$script" 2>>"$LOG_FILE"; then
      echo "  ✓ Syntax OK" >> "$LOG_FILE"
      PASSED=$((PASSED + 1))
      return 0
    else
      echo "  ✗ Syntax Error" >> "$LOG_FILE"
      FAILED=$((FAILED + 1))
      return 1
    fi
  else
    # Full execution with timeout
    if timeout 30 python "$script" >>"$LOG_FILE" 2>&1; then
      echo "  ✓ Execution OK" >> "$LOG_FILE"
      PASSED=$((PASSED + 1))
      return 0
    else
      echo "  ✗ Execution Failed or Timeout" >> "$LOG_FILE"
      FAILED=$((FAILED + 1))
      return 1
    fi
  fi
}

# Function to run a Bash script
run_bash_script() {
  local script="$1"
  TOTAL=$((TOTAL + 1))

  echo "Testing Bash script: $script" >> "$LOG_FILE"

  if [ "$DRY_RUN" = true ]; then
    # Dry run - syntax check only
    if bash -n "$script" 2>>"$LOG_FILE"; then
      echo "  ✓ Syntax OK" >> "$LOG_FILE"
      PASSED=$((PASSED + 1))
      return 0
    else
      echo "  ✗ Syntax Error" >> "$LOG_FILE"
      FAILED=$((FAILED + 1))
      return 1
    fi
  else
    # Full execution
    if bash "$script" >>"$LOG_FILE" 2>&1; then
      echo "  ✓ Execution OK" >> "$LOG_FILE"
      PASSED=$((PASSED + 1))
      return 0
    else
      echo "  ✗ Execution Failed" >> "$LOG_FILE"
      FAILED=$((FAILED + 1))
      return 1
    fi
  fi
}

# Change to project root
cd "$PROJECT_ROOT"

# Find and test Python scripts in code/ directory
echo "" >> "$LOG_FILE"
echo "=== Testing code/ Python scripts ===" >> "$LOG_FILE"
if [ -d "code" ]; then
  while IFS= read -r -d '' script; do
    run_python_script "$script"
  done < <(find code -name "*.py" -type f -print0 2>/dev/null)
fi

# Find and test Python scripts in scripts/ directory
echo "" >> "$LOG_FILE"
echo "=== Testing scripts/ Python scripts ===" >> "$LOG_FILE"
if [ -d "scripts" ]; then
  while IFS= read -r -d '' script; do
    run_python_script "$script"
  done < <(find scripts -maxdepth 1 -name "*.py" -type f -print0 2>/dev/null)
fi

# Find and test Bash scripts in scripts/ directory
echo "" >> "$LOG_FILE"
echo "=== Testing scripts/ Bash scripts ===" >> "$LOG_FILE"
if [ -d "scripts" ]; then
  while IFS= read -r -d '' script; do
    run_bash_script "$script"
  done < <(find scripts -maxdepth 1 -name "*.sh" -type f -print0 2>/dev/null)
fi

# Write summary
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "SUMMARY" >> "$LOG_FILE"
echo "Total scripts tested: $TOTAL" >> "$LOG_FILE"
echo "Passed: $PASSED" >> "$LOG_FILE"
echo "Failed: $FAILED" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Exit with appropriate code
if [ $FAILED -gt 0 ]; then
  echo "CI Check FAILED: $FAILED script(s) failed"
  exit 1
else
  echo "CI Check PASSED: All $TOTAL scripts OK"
  exit 0
fi