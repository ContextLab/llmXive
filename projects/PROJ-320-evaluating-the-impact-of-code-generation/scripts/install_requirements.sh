#!/usr/bin/env bash
# T001: Install project dependencies from the root requirements.txt and
# record the full pip output (including the success message) in
# logs/requirements_install.log.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

mkdir -p logs

{
  echo "# requirements install log"
  echo "# date: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "# command: pip install -r requirements.txt"
  echo "# python: $(python --version 2>&1)"
  echo "# pip: $(pip --version 2>&1)"
  echo
} > logs/requirements_install.log

# Install (or verify already satisfied) every dependency; tee output to
# the log while preserving pip's exit status.
set -o pipefail
python -m pip install -r requirements.txt 2>&1 | tee -a logs/requirements_install.log
pip_status=$?

if [ "$pip_status" -ne 0 ]; then
  echo "ERROR: pip install failed with status $pip_status" | tee -a logs/requirements_install.log
  exit "$pip_status"
fi

# Verify the key imports work in the current environment.
python -c "import requests, pandas, scipy, matplotlib, seaborn, yaml, statsmodels, pytest, pydantic" 2>&1 | tee -a logs/requirements_install.log
import_status=$?

if [ "$import_status" -ne 0 ]; then
  echo "ERROR: dependency import verification failed" | tee -a logs/requirements_install.log
  exit "$import_status"
fi

echo "SUCCESS: all requirements installed and importable." | tee -a logs/requirements_install.log
echo "Install log written to logs/requirements_install.log"