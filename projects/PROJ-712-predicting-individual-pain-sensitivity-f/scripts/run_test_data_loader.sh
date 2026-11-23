#!/usr/bin/env bash
set -e
# Run integration tests for the data loader
python -m pytest -v tests/integration/test_data_loader.py