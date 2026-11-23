#!/bin/bash
# Trigger script for GPU escape hatch
# This script is called by train_llm.py when CPU training exceeds 4 hours
# It logs the failure and initiates a GPU run for validation purposes only

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DATA_ARTIFACTS="$PROJECT_ROOT/data/artifacts"
LOG_FILE="$DATA_ARTIFACTS/gpu_escape_log.json"
TRAINING_METRICS="$DATA_ARTIFACTS/training_metrics.json"

# Ensure artifacts directory exists
mkdir -p "$DATA_ARTIFACTS"

# Get current timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create the escape log entry
cat > "$LOG_FILE" << EOF
{
  "event": "gpu_escape_triggered",
  "timestamp": "$TIMESTAMP",
  "reason": "CPU training time exceeded 4-hour constraint",
  "cpu_constraint_met": false,
  "training_metrics_path": "$TRAINING_METRICS",
  "note": "GPU run is for validation only; primary CPU constraint is NOT MET",
  "status": "initiating_gpu_run"
}
EOF

echo "GPU escape hatch triggered. Logging to $LOG_FILE"
echo "Primary CPU constraint (FR-003) marked as NOT MET."

# Check if GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected. Initiating GPU training run..."
    # Run the training script with GPU flag
    # Note: This is a separate execution context for validation
    python "$PROJECT_ROOT/code/models/train_llm.py" --use-gpu --validation-only
    GPU_STATUS=$?
else
    echo "WARNING: No GPU detected. Cannot initiate GPU run."
    echo "CPU constraint remains NOT MET."
    # Still log the attempt
    cat > "$LOG_FILE" << EOF
    {
      "event": "gpu_escape_triggered",
      "timestamp": "$TIMESTAMP",
      "reason": "CPU training time exceeded 4-hour constraint",
      "cpu_constraint_met": false,
      "training_metrics_path": "$TRAINING_METRICS",
      "note": "GPU run is for validation only; primary CPU constraint is NOT MET",
      "status": "gpu_unavailable",
      "error": "No GPU detected on system"
    }
    EOF
    exit 1
fi

if [ $GPU_STATUS -eq 0 ]; then
    echo "GPU validation run completed successfully."
    # Update log with completion status
    cat > "$LOG_FILE" << EOF
    {
      "event": "gpu_escape_triggered",
      "timestamp": "$TIMESTAMP",
      "reason": "CPU training time exceeded 4-hour constraint",
      "cpu_constraint_met": false,
      "training_metrics_path": "$TRAINING_METRICS",
      "note": "GPU run is for validation only; primary CPU constraint is NOT MET",
      "status": "gpu_run_completed",
      "validation_success": true
    }
    EOF
else
    echo "GPU validation run failed."
    # Update log with failure status
    cat > "$LOG_FILE" << EOF
    {
      "event": "gpu_escape_triggered",
      "timestamp": "$TIMESTAMP",
      "reason": "CPU training time exceeded 4-hour constraint",
      "cpu_constraint_met": false,
      "training_metrics_path": "$TRAINING_METRICS",
      "note": "GPU run is for validation only; primary CPU constraint is NOT MET",
      "status": "gpu_run_failed",
      "validation_success": false,
      "error_code": $GPU_STATUS
    }
    EOF
    exit $GPU_STATUS
fi
