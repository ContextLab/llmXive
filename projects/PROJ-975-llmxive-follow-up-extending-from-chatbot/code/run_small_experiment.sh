#!/usr/bin/env bash
set -e
# Ensure the CSV and JSONL outputs are generated for the small run required by the integration test.
python -m code.agent --library-sizes 50 --task-sample 100 --pruning off --overlap HIGH