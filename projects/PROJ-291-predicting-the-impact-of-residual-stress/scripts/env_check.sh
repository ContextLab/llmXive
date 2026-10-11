#!/usr/bin/env bash
# Environment verification script for the residual‑stress fatigue project.
set -euo pipefail

if [ -f "requirements.txt" ]; then
  echo "Installing pinned dependencies (if needed)..."
  pip install -r requirements.txt --quiet
fi

mkdir -p results
LOG=results/env_check.log
: > "$LOG"

fail=0

check() {
  local module="$1"
  if python -c "import $module" 2>>"$LOG"; then
    echo "OK    $module imported successfully" | tee -a "$LOG"
  else
    echo "FAIL  $module could not be imported" | tee -a "$LOG"
    fail=1
  fi
}

{
  echo "env-check started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "python: $(python --version 2>&1)"
} | tee -a "$LOG"

check pandas
check numpy
check sklearn
check torch
check statsmodels
check datasets
check yaml
check pytest
check requests
check jsonschema
check matplotlib

if [ "$fail" -ne 0 ]; then
  echo "env-check FAILED"
  exit 1
fi
echo "env-check PASSED: all required modules importable"
exit 0
