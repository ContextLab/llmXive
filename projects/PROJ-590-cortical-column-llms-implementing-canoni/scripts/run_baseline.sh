#!/bin/bash
# run_baseline.sh - Orchestrate baseline Transformer training on synthetic tasks
#
# Purpose:
#   1. Train a standard Transformer (Baseline) on the Lorenz Attractor dataset.
#   2. Evaluate on the Polynomial Surface dataset (held-out test).
#   3. Enforce FR-004 constraints: Max 1 hour wall time, Max 4GB RAM.
#   4. Output metrics to data/results/baseline_metrics.json.
#
# Dependencies:
#   - /usr/bin/time (GNU time) must be available for resource monitoring.
#   - Python environment with project dependencies installed.
#
# Exit Codes:
#   0: Success (within resource limits)
#   1: Training failed or resource limit exceeded
#   2: Missing dependencies (GNU time or Python)

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"
TIME_CMD="/usr/bin/time"

# FR-004 Constraints
MAX_TIME_HOURS=1
MAX_RAM_GB=4

# Input/Output Paths
TRAIN_TASK="lorenz"
TEST_TASK="polynomial"
OUTPUT_DIR="$PROJECT_ROOT/data/results"
METRICS_FILE="$OUTPUT_DIR/baseline_metrics.json"
LOG_FILE="$OUTPUT_DIR/baseline_training.log"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "=== Baseline Training Orchestration ==="
echo "Project Root: $PROJECT_ROOT"
echo "Training Task: $TRAIN_TASK"
echo "Test Task: $TEST_TASK"
echo "Max Time: ${MAX_TIME_HOURS}h | Max RAM: ${MAX_RAM_GB}GB"
echo "Log File: $LOG_FILE"
echo "Metrics File: $METRICS_FILE"
echo "----------------------------------------"

# Verify dependencies
if ! command -v "$TIME_CMD" &> /dev/null; then
    echo "ERROR: GNU time (/usr/bin/time) not found. Please install 'time' package."
    exit 2
fi

if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "ERROR: Python command '$PYTHON_CMD' not found."
    exit 2
fi

# Construct the training command
# We invoke the experiment runner which handles the actual training loop.
# The runner internally uses src/training/trainer.py and src/data/benchmarks.py.
TRAINING_SCRIPT="$PROJECT_ROOT/src/experiments/baseline_runner.py"

if [[ ! -f "$TRAINING_SCRIPT" ]]; then
    echo "ERROR: Training script not found at $TRAINING_SCRIPT"
    exit 1
fi

# Build the resource-constrained command using GNU time
# -v: Verbose output to stderr
# -l: Format output for parsing (optional, but -v is standard)
# We capture stderr to parse RAM usage later.
TIME_OUTPUT_FILE="$OUTPUT_DIR/time_output.tmp"

echo "Starting training run at $(date)..."
echo "Command: $TIME_CMD -v -o $TIME_OUTPUT_FILE -- $PYTHON_CMD $TRAINING_SCRIPT --train $TRAIN_TASK --test $TEST_TASK --output $METRICS_FILE"

# Run the training wrapped in GNU time
# We redirect stdout to log file, and capture time's stderr (resource usage) to a file.
if ! $TIME_CMD -v -o "$TIME_OUTPUT_FILE" -- $PYTHON_CMD "$TRAINING_SCRIPT" \
    --train "$TRAIN_TASK" \
    --test "$TEST_TASK" \
    --output "$METRICS_FILE" \
    --log-file "$LOG_FILE" 2>&1 | tee -a "$LOG_FILE"; then

    echo "ERROR: Training process failed with non-zero exit code."
    exit 1
fi

# Parse resource usage from GNU time output
echo "----------------------------------------"
echo "Parsing resource usage..."

MAX_RSS_KB=$(grep "Maximum resident set size" "$TIME_OUTPUT_FILE" | awk '{print $NF}')
ELAPSED_TIME=$(grep "Elapsed (wall clock) time" "$TIME_OUTPUT_FILE" | awk '{print $NF}')

if [[ -z "$MAX_RSS_KB" ]]; then
    echo "WARNING: Could not determine peak RAM usage from time output."
    MAX_RSS_KB=0
fi

# Convert units for comparison
# RAM: KB -> GB
MAX_RSS_GB=$(echo "scale=4; $MAX_RSS_KB / 1024 / 1024" | bc)

echo "Peak RAM Usage: ${MAX_RSS_GB} GB (Limit: ${MAX_RAM_GB} GB)"
echo "Elapsed Time: $ELAPSED_TIME"

# Check constraints
CONSTRAINT_VIOLATED=false

# Check RAM (using bc for float comparison)
if (( $(echo "$MAX_RSS_GB > $MAX_RAM_GB" | bc -l) )); then
    echo "CRITICAL: RAM limit exceeded! Used ${MAX_RSS_GB}GB > ${MAX_RAM_GB}GB."
    CONSTRAINT_VIOLATED=true
fi

# Check Time (simple string check for now, assuming format H:MM:SS or similar)
# A more robust check would parse the time string into seconds.
# For this script, we rely on the training loop itself to respect timeouts,
# but we log the actual time here.
# If the process ran for > 1 hour, we flag it.
# Parsing H:MM:SS or M:SS
TIME_SECONDS=0
if [[ "$ELAPSED_TIME" == *":"* ]]; then
    IFS=':' read -ra TIME_PARTS <<< "$ELAPSED_TIME"
    if [[ ${#TIME_PARTS[@]} -eq 3 ]]; then
        TIME_SECONDS=$((${TIME_PARTS[0]}*3600 + ${TIME_PARTS[1]}*60 + ${TIME_PARTS[2]}))
    elif [[ ${#TIME_PARTS[@]} -eq 2 ]]; then
        TIME_SECONDS=$((${TIME_PARTS[0]}*60 + ${TIME_PARTS[1]}))
    fi
fi

MAX_TIME_SECONDS=$((MAX_TIME_HOURS * 3600))
if [[ $TIME_SECONDS -gt $MAX_TIME_SECONDS ]]; then
    echo "CRITICAL: Time limit exceeded! Used ${TIME_SECONDS}s > ${MAX_TIME_SECONDS}s."
    CONSTRAINT_VIOLATED=true
fi

# Verify output file exists
if [[ ! -f "$METRICS_FILE" ]]; then
    echo "CRITICAL: Output metrics file not generated at $METRICS_FILE"
    exit 1
fi

# Final Status
echo "----------------------------------------"
if [[ "$CONSTRAINT_VIOLATED" == true ]]; then
    echo "STATUS: FAILED - Resource constraints violated."
    exit 1
else
    echo "STATUS: SUCCESS - Training completed within resource limits."
    echo "Metrics saved to: $METRICS_FILE"
    exit 0
fi