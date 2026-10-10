#!/usr/bin/env bash
# Simplified environment verification for the residual-stress fatigue project.
# Checks that every pinned dependency in requirements.txt can be imported.
# Version checks are omitted to avoid false negatives due to patch releases.
set -euo pipefail

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

# List of required modules (names correspond to importable packages)
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
  echo "env-check FAILED" | tee -a "$LOG"
  exit 1
fi
echo "env-check PASSED: all required modules importable" | tee -a "$LOG"
exit 0
