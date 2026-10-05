"""
Task T029: Run quickstart.md validation and log runtime.

This script measures the total runtime of the pipeline (simulated or read from context)
and logs the result to data/processed/runtime.log.

Logic:
1. Check if a previous runtime record exists (e.g., from a previous full run or main.py).
2. If no record exists, this script assumes it is being run as part of the final validation
   of the *entire* pipeline. Since the pipeline steps (T001-T028) are assumed to have
   completed successfully (as per the task list), we measure the time taken to reach
   this point or simulate the validation of the completed state.
3. However, per the task description: "Log total runtime in seconds to data/processed/runtime.log".
   If the pipeline is run as a single `python code/main.py`, the runtime is tracked there.
   Since T029 is the final step, we will check for a `pipeline_start_time` marker or
   simply record the time it takes to verify the existence of all required artifacts
   as a proxy for "validation runtime", OR (more likely) we are expected to read the
   runtime from the `main.py` execution if it was passed, or simply log the current
   validation duration.

Given the constraints of a single-task implementation where the pipeline has already
logically completed (T001-T028 are marked done), this script will:
1. Verify the existence of critical artifacts (T026 research.md, T027 data-model.md, etc.).
2. Measure the time taken for this verification.
3. Log the duration.
4. Check if duration > 21600s (6 hours). If so, log a warning about the subset logic (T007).
   *Note*: In a real sequential run, 6 hours is the total pipeline time. If this script
   only runs the final validation, it won't be 6 hours. The logic implies we should
   check the *total* pipeline runtime.
5. To support the "total runtime" requirement, we will look for a `pipeline_start_time`
   saved by `main.py` or `ingest.py` or similar. If not found, we assume this script
   is being run immediately after `main.py` and we might not have the total time.
   *Correction*: The task says "Run quickstart.md validation". The quickstart likely
   runs the whole pipeline. If this script is the *entry point* for the quickstart,
   it should time the whole thing. If it is the *last step*, it should read the time.
   Let's assume this script is the final step of the pipeline. We will look for a
   `state/pipeline_start_time.json` or similar. If not found, we will assume the
   runtime is unknown and log "N/A" or 0, but the task requires a specific check.

Refined Logic for T029:
1. Read `state/pipeline_start_time.json` (created by `main.py` or similar).
2. Calculate `total_runtime = current_time - start_time`.
3. If the file doesn't exist, assume the pipeline was not run as a timed batch,
   or this is a standalone validation. In that case, we cannot calculate the total
   runtime. However, the task requires logging the runtime.
   Let's assume `main.py` (T001/T002 context) or a wrapper script is responsible
   for timing. Since we are implementing T029, and `main.py` is already "done" (T001-T028),
   we must assume `main.py` saved the start time.
   If `state/pipeline_start_time.json` is missing, we will log a warning that the
   start time was not recorded, and we cannot verify the 6-hour threshold.
   *Alternative*: The task might imply that this script *is* the validator that
   runs the whole pipeline. But T029 depends on T026 (Research Report), which
   depends on the whole pipeline. So T029 is the final step.
   Therefore, we MUST read the start time.

Let's implement the logic to read the start time and log the result.
"""

import os
import sys
import time
import json
from pathlib import Path

import config

# Ensure output directory exists
OUTPUT_DIR = Path(config.DATA_PROCESSED_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = OUTPUT_DIR / "runtime.log"
START_TIME_FILE = Path(config.STATE_DIR) / "pipeline_start_time.json"

def main():
    start_time = None
    total_runtime = None

    # Try to read the start time
    if START_TIME_FILE.exists():
        try:
            with open(START_TIME_FILE, 'r') as f:
                data = json.load(f)
                start_time = data.get("start_time")
                if start_time:
                    start_time = float(start_time)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Could not parse start time from {START_TIME_FILE}: {e}")

    if start_time:
        total_runtime = time.time() - start_time
        runtime_seconds = int(total_runtime)
        msg = f"Total pipeline runtime: {runtime_seconds} seconds"
        
        # Check threshold (6 hours = 21600 seconds)
        if total_runtime > 21600:
            msg += "\nWARNING: Runtime exceeded 6 hours (21600s). The subset logic (T007) should have been triggered earlier."
            print(msg)
        else:
            msg += "\nSuccess: Pipeline completed within 6 hours."
            print(msg)
    else:
        # If start time is missing, we cannot calculate total runtime.
        # We log that we are unable to verify the threshold.
        msg = "Total pipeline runtime: N/A (Start time not recorded in state/pipeline_start_time.json)"
        msg += "\nWARNING: Could not verify 6-hour threshold due to missing start time."
        print(msg)
        runtime_seconds = None

    # Write to log file
    with open(LOG_FILE, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    
    print(f"Runtime log updated: {LOG_FILE}")

if __name__ == "__main__":
    main()
