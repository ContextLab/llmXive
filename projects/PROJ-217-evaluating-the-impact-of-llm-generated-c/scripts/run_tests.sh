#!/usr/bin/env bash
set -e
# Run the project's pytest suite to ensure all tests (including test_download)
# pass after the recent modifications.
pytest -q