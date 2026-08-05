#!/bin/bash
#
# verify_feasibility.sh
# Runs a dry-run of the Dream-State Learning pipeline with strict resource limits
# to verify feasibility within GitHub Actions free-tier constraints.
#
# Constraints enforced:
# - Max Wall-Clock Time: 5 hours (configurable via env var MAX_WALL_CLOCK_HOURS)
# - Max Memory: 7GB (enforced via memory_monitor module)
# - Dataset: Small GLUE subset (e.g., 'cola' or 'sst2')
# - Model: DistilBERT-base (CPU-optimized)
# - Steps: Reduced to 50 steps for rapid verification
#
# Exit codes:
# 0: Success (completed within limits)
# 1: Time limit exceeded
# 2: Memory limit exceeded
# 3: Other error (configuration, data integrity, etc.)
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CODE_DIR="$PROJECT_ROOT/code"

# Default limits (can be overridden by environment variables)
MAX_WALL_CLOCK_HOURS="${MAX_WALL_CLOCK_HOURS:-5}"
MAX_MEMORY_GB="${MAX_MEMORY_GB:-7}"

echo "=========================================="
echo "Dream-State Learning Feasibility Verification"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Max Wall-Clock Time: ${MAX_WALL_CLOCK_HOURS} hours"
echo "Max Memory: ${MAX_MEMORY_GB} GB"
echo "=========================================="

# Change to project root for consistent path resolution
cd "$PROJECT_ROOT"

# Create a temporary configuration for the dry-run
DRY_RUN_CONFIG="$CODE_DIR/dry_run_config.json"
cat > "$DRY_RUN_CONFIG" <<EOF
{
  "dry_run": true,
  "max_steps": 50,
  "dataset_subset": "cola",
  "model_name": "distilbert-base-uncased",
  "batch_size": 8,
  "seed": 42,
  "max_wall_clock_hours": $MAX_WALL_CLOCK_HOURS,
  "max_memory_gb": $MAX_MEMORY_GB,
  "log_level": "INFO"
}
EOF

echo "Starting feasibility verification dry-run..."
echo "This will execute a minimal training cycle with resource monitoring."
echo ""

# Set Python path to include the code directory
export PYTHONPATH="$CODE_DIR:$PYTHONPATH"

# Run the main script with dry-run configuration
# The script will enforce time and memory limits internally via main.py logic
# and the memory_monitor module
if python3 "$CODE_DIR/main.py" --config "$DRY_RUN_CONFIG" --mode feasibility_check; then
  EXIT_CODE=0
  echo ""
  echo "=========================================="
  echo "✓ Feasibility Verification PASSED"
  echo "  The pipeline completed within resource limits."
  echo "=========================================="
else
  EXIT_CODE=$?
  echo ""
  echo "=========================================="
  echo "✗ Feasibility Verification FAILED"
  echo "  Exit code: $EXIT_CODE"
  echo "  Possible reasons:"
  echo "    - Time limit exceeded (code: 1)"
  echo "    - Memory limit exceeded (code: 2)"
  echo "    - Configuration or data error (code: 3)"
  echo "=========================================="
fi

# Cleanup temporary config
rm -f "$DRY_RUN_CONFIG"

exit $EXIT_CODE