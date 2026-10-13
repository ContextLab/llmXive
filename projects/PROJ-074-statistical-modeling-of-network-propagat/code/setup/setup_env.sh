#!/usr/bin/env bash
# T002: Initialize the Python project environment.
#
# Installs the pinned dependencies from requirements.txt into the
# active interpreter and verifies that every required package (in
# particular numpyro, whose import previously failed due to a jax
# version mismatch) is importable.  An installation log is written to
# results/installation.log as evidence that the dependencies were
# actually installed.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

mkdir -p results

echo "=== Installing pinned dependencies from requirements.txt ===" \
    | tee results/installation.log
pip install -r requirements.txt 2>&1 | tee -a results/installation.log

echo "=== Verifying environment ===" | tee -a results/installation.log
python code/setup/verify_environment.py 2>&1 | tee -a results/installation.log

echo "=== Environment setup complete ===" | tee -a results/installation.log
