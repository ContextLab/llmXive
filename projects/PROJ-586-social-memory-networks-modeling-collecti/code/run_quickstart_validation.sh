#!/bin/bash
# Quickstart validation runner
set -e
cd "$(dirname "$0")/.."
python code/run_quickstart_validation.py
