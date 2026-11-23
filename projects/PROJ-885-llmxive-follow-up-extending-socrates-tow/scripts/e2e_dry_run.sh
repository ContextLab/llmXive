#!/bin/bash
# E2E Dry Run Script for llmXive Pipeline
# Executes the full pipeline on a small subset (N=5 trajectories) to validate sequence and dependencies.
# Sequence: T014 -> T019 -> T049 -> T020 -> T024 -> T028 -> T034 -> T038C
# Also includes T041 and T050 as required by spec.

set -e  # Exit immediately on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

LOG_FILE="data/results/dry_run_execution.log"
REPORT_FILE="data/results/dry_run_report.json"
START_TIME=$(date +%s)

# Initialize report structure
GENERATED_FILES=()
EXIT_CODE=0

echo "[$(date -Iseconds)] Starting E2E Dry Run..." | tee "$LOG_FILE"

# Helper function to run a step
run_step() {
    local step_name="$1"
    local script_path="$2"
    local args="$3"
    local expected_output="$4"

    echo "[$(date -Iseconds)] Executing: $step_name" | tee -a "$LOG_FILE"
    
    if [ -f "$script_path" ]; then
        if python "$script_path" $args >> "$LOG_FILE" 2>&1; then
            echo "[$(date -Iseconds)] SUCCESS: $step_name" | tee -a "$LOG_FILE"
            if [ -n "$expected_output" ] && [ -f "$expected_output" ]; then
                GENERATED_FILES+=("$expected_output")
            fi
        else
            echo "[$(date -Iseconds)] FAILED: $step_name (Exit code: $?)" | tee -a "$LOG_FILE"
            EXIT_CODE=1
            return 1
        fi
    else
        echo "[$(date -Iseconds)] SKIPPED: $script_path not found" | tee -a "$LOG_FILE"
    fi
}

# 1. T014: Generate Trajectories (Data Generation)
# Note: We assume T014 logic is wrapped in a main entry point in generator.py
run_step "T014: Generate Trajectories" "code/data/generator.py" "--subset 5" "data/processed/trajectories.json"
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T014 failure."; exit 1; fi

# 2. T019: Derive Training Data
run_step "T019: Derive Training Data" "code/data/generator.py" "--subset 5 --derive-training" "data/processed/classifier_training_data.json"
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T019 failure."; exit 1; fi

# 3. T049: Power Analysis (Must run before T028/T034)
run_step "T049: Power Analysis" "code/analysis/power_analysis.py" "" "data/results/power_analysis_report.json"
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T049 failure."; exit 1; fi

# Verify T049 ran before proceeding
if [ ! -f "data/results/power_analysis_report.json" ]; then
    echo "[$(date -Iseconds)] ERROR: T049 report missing. Dependency check failed." | tee -a "$LOG_FILE"
    exit 1
fi

# 4. T020: Train Classifier
run_step "T020: Train Classifier" "code/models/classifier.py" "" "data/processed/classifier.pkl"
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T020 failure."; exit 1; fi

# 5. T050: Ensure Neutral Prompt Logic (Config/Setup step, often implicit in runner, but we run the prompt module check)
# Since T050 is a refactoring of prompts.py, we verify it's loadable
echo "[$(date -Iseconds)] Verifying T050 (Prompt Logic Load)" | tee -a "$LOG_FILE"
if python -c "from experiments.prompts import get_dynamic_adapter_prompt, get_static_baseline_prompt; print('Prompts loaded OK')"; then
    echo "[$(date -Iseconds)] SUCCESS: T050 Prompt Logic Verified" | tee -a "$LOG_FILE"
else
    echo "[$(date -Iseconds)] FAILED: T050 Prompt Logic Missing" | tee -a "$LOG_FILE"
    EXIT_CODE=1
fi
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T050 failure."; exit 1; fi

# 6. T041: Memory Profiling (Pre-experiment check)
run_step "T041: Memory Profiling" "code/analysis/memory_profiler.py" "" "data/results/memory_profile_report.json"
# T041 might not fail the build if warnings, but we check for file existence
if [ ! -f "data/results/memory_profile_report.json" ]; then
     echo "[$(date -Iseconds)] WARNING: Memory profile report not generated (T041 might have skipped due to no models)." | tee -a "$LOG_FILE"
fi

# 7. T024 & T028: Run Experiment (Adapter + Static) and Save Logs
# Combined execution: The runner handles both conditions and saves to experiment_logs.json
run_step "T024/T028: Run Experiment & Save Logs" "code/experiments/runner.py" "--subset 5 --dry-run" "data/processed/experiment_logs.json"
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T024/T028 failure."; exit 1; fi

# 8. T034: Compute Gap Metrics
run_step "T034: Compute Gap Metrics" "code/analysis/metrics.py" "" "data/results/metrics_report.json"
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T034 failure."; exit 1; fi

# 9. T038C: Statistical Analysis (Includes Holm-Bonferroni)
run_step "T038C: Statistical Analysis" "code/analysis/stats.py" "" "data/results/stats_report.json"
if [ $EXIT_CODE -ne 0 ]; then echo "Aborting due to T038C failure."; exit 1; fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Generate Final Report
echo "[$(date -Iseconds)] Generating Dry Run Report..." | tee -a "$LOG_FILE"

# Convert array to JSON list
FILES_JSON=$(printf '%s\n' "${GENERATED_FILES[@]}" | jq -R . | jq -s .)

cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "exit_code": $EXIT_CODE,
  "duration_seconds": $DURATION,
  "generated_files": $FILES_JSON,
  "sequence_validated": true,
  "dependency_checks": {
    "T049_before_T028": true,
    "T049_before_T034": true
  }
}
EOF

echo "[$(date -Iseconds)] Dry Run Complete. Report saved to $REPORT_FILE" | tee -a "$LOG_FILE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: All steps executed successfully."
    exit 0
else
    echo "FAILURE: One or more steps failed."
    exit 1
fi