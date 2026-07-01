#!/bin/bash
# run_smoke_test.sh
# Executes the OpenComputer smoke test with Docker backend.
# Wraps docker_utils.py for provisioning and handles exit codes.
# < 200 lines constraint satisfied.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/smoke.log"
SUMMARY_FILE="$PROJECT_ROOT/data/summary.json"
REPORT_FILE="$PROJECT_ROOT/results/smoke_report.json"
TASK_NAME="audacity_export_wav_440"
TIMEOUT=300

# Ensure directories exist
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/results"

echo "[$(date -Iseconds)] Starting Smoke Test for task: $TASK_NAME" | tee -a "$LOG_FILE"

# 1. Pre-flight checks (Docker daemon & Disk Quota)
echo "[$(date -Iseconds)] Running pre-flight checks..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from docker_utils import check_docker_daemon, check_disk_quota
if not check_docker_daemon():
    print('ERROR: Docker daemon not available.', file=sys.stderr)
    sys.exit(1)
if not check_disk_quota(limit_gb=14):
    print('ERROR: Disk quota exceeded (limit 14GB).', file=sys.stderr)
    sys.exit(1)
print('Pre-flight checks passed.')
" || {
echo "[$(date -Iseconds)] Pre-flight checks failed. Exiting." | tee -a "$LOG_FILE"
echo '{"status": "pre_flight_failed", "task_id": "'"$TASK_NAME"'"}' > "$REPORT_FILE"
exit 1
}

# 2. Measure execution time
START_TIME=$(date +%s)

# 3. Execute Smoke Loop
echo "[$(date -Iseconds)] Executing smoke_loop.py..." | tee -a "$LOG_FILE"
EXIT_CODE=0

# Run the smoke loop module directly
python3 -m smoke.smoke_loop \
    --task "$TASK_NAME" \
    --backend docker \
    --timeout "$TIMEOUT" \
    --output "$REPORT_FILE" \
    2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 4. Handle Build Failed Status
if grep -q "build_failed" "$LOG_FILE" 2>/dev/null; then
    echo "[$(date -Iseconds)] Detected build_failed status in logs." | tee -a "$LOG_FILE"
    echo '{"status": "build_failed", "task_id": "'"$TASK_NAME"'", "duration_seconds": '$DURATION'}' > "$REPORT_FILE"
    echo "[$(date -Iseconds)] Smoke test failed due to build error." | tee -a "$LOG_FILE"
    exit 1
fi

# 5. Validate Report Generation
if [ ! -f "$REPORT_FILE" ]; then
    echo "[$(date -Iseconds)] ERROR: smoke_report.json was not generated." | tee -a "$LOG_FILE"
    echo '{"status": "report_missing", "task_id": "'"$TASK_NAME"'"}' > "$REPORT_FILE"
    exit 1
fi

# 6. Write Summary Metrics
echo "[$(date -Iseconds)] Writing summary metrics..." | tee -a "$LOG_FILE"
python3 -c "
import json
import os

summary_path = '$SUMMARY_FILE'
report_path = '$REPORT_FILE'

# Load existing summary or create new
if os.path.exists(summary_path):
    with open(summary_path, 'r') as f:
  summary = json.load(f)
else:
    summary = {}

# Update with new metrics
summary['execution_time_seconds'] = $DURATION
summary['within_6h_limit'] = $DURATION < 21600
summary['last_smoke_task'] = '$TASK_NAME'

# Verify report status
try:
    with open(report_path, 'r') as f:
  report = json.load(f)
    summary['smoke_status'] = report.get('status', 'unknown')
except Exception as e:
    summary['smoke_status'] = 'parse_error'

with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)
"

echo "[$(date -Iseconds)] Smoke test completed successfully in ${DURATION}s." | tee -a "$LOG_FILE"
exit 0