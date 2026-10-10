#!/usr/bin/env bash
# Environment verification for the residual-stress fatigue project.
# Checks that every pinned dependency in requirements.txt is importable
# at the expected major.minor version and records the result to
# results/env_check.log.  Exits non-zero on any failure.
set -euo pipefail

mkdir -p results
LOG=results/env_check.log
: > "$LOG"

fail=0

check() {
  local module="$1" expected="$2"
  if python -c "import $module, sys; sys.exit(0)" 2>>"$LOG"; then
    actual=$(python -c "import $module; print($module.__version__)")
    echo "OK    $module==${actual} (expected ${expected}.*)" | tee -a "$LOG"
  else
    echo "FAIL  $module could not be imported (expected ${expected}.*)" | tee -a "$LOG"
    fail=1
  fi
}

{
  echo "env-check started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "python: $(python --version 2>&1)"
} | tee -a "$LOG"

check pandas 2.2
check numpy 1.26
check sklearn 1.5
check torch 2.3
check statsmodels 0.14
check datasets 2.20
check yaml 6.0
check pytest 8.2
check requests 2.32
check jsonschema 4.22
check matplotlib 3.9

if [ "$fail" -ne 0 ]; then
  echo "env-check FAILED" | tee -a "$LOG"
  exit 1
fi
echo "env-check PASSED: all pinned dependencies importable" | tee -a "$LOG"
exit 0
