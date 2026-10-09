#!/usr/bin/env bash
set -e
# Ensure the virtual environment (if any) is active; otherwise rely on system packages.
pytest -q tests/integration/test_data_loader.py
