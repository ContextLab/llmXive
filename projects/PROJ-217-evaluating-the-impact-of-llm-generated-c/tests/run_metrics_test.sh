#!/usr/bin/env bash
set -e
# Run the pytest suite that validates the metrics implementation.
pytest -q src/tests/test_metrics.py