#!/bin/bash
# Run the full simulation pipeline and verify runtime constraints.
# This script wraps verify_runtime.py and adds a check for the 6-hour threshold.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
echo "Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

echo "Running runtime verification..."
python "$SCRIPT_DIR/verify_runtime.py" "$@"

# Check the generated runtime log for threshold violation
RUNTIME_LOG="$PROJECT_ROOT/data/results/runtime_log.json"

if [ -f "$RUNTIME_LOG" ]; then
    THRESHOLD=$(python -c "import json; print(json.load(open('$RUNTIME_LOG'))['threshold_seconds'])")
    DURATION=$(python -c "import json; print(json.load(open('$RUNTIME_LOG'))['total_duration_seconds'])")
    EXCEEDED=$(python -c "import json; print(json.load(open('$RUNTIME_LOG'))['exceeded_threshold'])")

    echo "Total duration: $DURATION seconds"
    echo "Threshold: $THRESHOLD seconds"

    if [ "$EXCEEDED" = "True" ]; then
        echo "WARNING: Total runtime ($DURATION s) exceeded threshold ($THRESHOLD s)."
        echo "WARNING: Build continues, but consider optimizing the simulation parameters."
    else
        echo "Runtime check passed."
    fi
else
    echo "ERROR: Runtime log not found at $RUNTIME_LOG. Verification failed."
    exit 1
fi

echo "Script completed successfully."
