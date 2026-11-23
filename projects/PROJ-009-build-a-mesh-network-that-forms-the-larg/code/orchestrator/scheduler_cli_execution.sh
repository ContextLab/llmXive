#!/usr/bin/env bash
set -e
# Ensure the required output file exists after running the scheduler CLI.
python code/orchestrator/scheduler.py --config config.yaml --granularity fine --nodes 1 --latency 0
# Verify that dropout_events.json was created
if [ ! -f "$(python - <<PY
import os, json
from llmxive_toolkit import paths
print(paths.data('raw', 'dropout_events.json'))
PY
)" ]; then
    echo "Dropout events file not created"
    exit 1
fi
echo "Scheduler CLI executed successfully and produced dropout_events.json"