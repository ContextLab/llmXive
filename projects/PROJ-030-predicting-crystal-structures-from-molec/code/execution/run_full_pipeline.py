"""
Full End-to-End Pipeline Execution Script for T030.

Orchestrates the ingestion, modeling, and analysis phases to verify SC-004 (6-hour limit).
This script must be run via the quickstart run-book to generate `data/results/pipeline_timing.log`.
"""
import os
import sys
import json
import time
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path_absolute, get_path_processed_data, get_path_results, get_path_validation, ensure_directory
from logging_config import setup_logging, get_logger

# Configure logging for the pipeline run
LOG_DIR = get_path_absolute("logs")
ensure_directory(LOG_DIR)
LOG_FILE = os.path.join(LOG_DIR, "pipeline_execution.log")
setup_logging(log_file=LOG_FILE, level=logging.INFO)
logger = get_logger("pipeline_executor")

# Define the sequence of steps to execute.
# These correspond to the tasks required to produce the final artifacts.
# We use the actual script names defined in the API surface.
PIPELINE_STEPS: List[Dict[str, Any]] = [
    {
        "name": "Ingestion Pipeline",
        "script": "code/ingestion/run_pipeline.py",
        "args": [],
        "description": "Downloads, parses, fingerprints, and builds the dataset (T013)."
    },
    {
        "name": "Group Rare Space Groups",
        "script": "code/modeling/group_rare.py",
        "args": [],
        "description": "Groups rare space groups into 'Other' (T015a-exec)."
    },
    {
        "name": "Scaffold Split",
        "script": "code/modeling/split.py",
        "args": [],
        "description": "Performs scaffold split and validates zero overlap (T015b-exec, T015c-exec)."
    },
    {
        "name": "Model Training",
        "script": "code/modeling/train.py",
        "args": [],
        "description": "Trains RF, GB, Ridge models with timeout enforcement (T016-exec)."
    },
    {
        "name": "Baseline Calculation (MW)",
        "script": "code/modeling/baseline_mw.py",
        "args": [],
        "description": "Calculates Molecular Weight baseline (T017-exec)."
    },
    {
        "name": "Baseline Calculation (Majority)",
        "script": "code/modeling/baseline_majority.py",
        "args": [],
        "description": "Calculates Majority Class baseline (T017b-exec)."
    },
    {
        "name": "Power Analysis",
        "script": "code/analysis/power.py",
        "args": [],
        "description": "Calculates power analysis metrics (T006b-exec)."
    },
    {
        "name": "Define Lift Threshold",
        "script": "code/analysis/define_lift.py",
        "args": [],
        "description": "Calculates lift threshold (T017a-exec)."
    },
    {
        "name": "Model Evaluation",
        "script": "code/modeling/evaluate.py",
        "args": [],
        "description": "Evaluates models and calculates metrics (T019-exec)."
    },
    {
        "name": "Polymorphism Metrics",
        "script": "code/modeling/polymorphism_metrics.py",
        "args": [],
        "description": "Calculates Top-K and Entropy metrics (T019d-exec)."
    },
    {
        "name": "Success Criterion Verification",
        "script": "code/modeling/verify_success_criterion.py",
        "args": [],
        "description": "Verifies success criteria (T017c-exec)."
    },
    {
        "name": "Final Metrics Generation",
        "script": "code/modeling/generate_final_metrics.py",
        "args": [],
        "description": "Generates final consolidated metrics (T019c-exec)."
    },
    {
        "name": "Interpretability Analysis",
        "script": "code/analysis/interpret.py",
        "args": [],
        "description": "Computes SHAP and Permutation Importance (T022-exec, T023-exec)."
    },
    {
        "name": "Report Generation",
        "script": "code/analysis/generate_report.py",
        "args": [],
        "description": "Generates the feature importance report (T025-exec)."
    },
    {
        "name": "Report Validation",
        "script": "code/analysis/validate_report.py",
        "args": [],
        "description": "Validates the generated report (T026-exec)."
    }
]

def run_step(step: Dict[str, Any]) -> bool:
    """
    Executes a single pipeline step.
    Returns True if successful, False otherwise.
    """
    script_path = step["script"]
    args = step["args"]
    full_script_path = PROJECT_ROOT / script_path

    if not full_script_path.exists():
        logger.error(f"Step '{step['name']}' script not found: {full_script_path}")
        return False

    cmd = [sys.executable, str(full_script_path)] + args
    logger.info(f"Executing: {' '.join(cmd)}")
    logger.info(f"Description: {step['description']}")

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=False, # Stream output to main log
            timeout=None,         # Let individual scripts handle their own timeouts
            check=True
        )
        logger.info(f"Step '{step['name']}' completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Step '{step['name']}' failed with return code {e.returncode}")
        return False
    except subprocess.TimeoutExpired as e:
        logger.error(f"Step '{step['name']}' timed out: {e}")
        return False
    except Exception as e:
        logger.error(f"Step '{step['name']}' raised an unexpected error: {e}")
        return False

def main():
    logger.info("=" * 80)
    logger.info("Starting Full End-to-End Pipeline Execution (T030)")
    logger.info("=" * 80)

    start_time = time.time()
    start_iso = datetime.now().isoformat()

    success_count = 0
    failure_count = 0
    failed_steps = []

    for step in PIPELINE_STEPS:
        logger.info(f"\n--- Running Step: {step['name']} ---")
        if run_step(step):
            success_count += 1
        else:
            failure_count += 1
            failed_steps.append(step['name'])
            # Optional: Fail fast or continue? For timing verification, we log all.
            # However, if a critical dependency fails, subsequent steps will likely fail too.
            # We continue to log the full attempt to see where it breaks.
            logger.warning("Continuing to next step despite failure...")

    end_time = time.time()
    duration_seconds = end_time - start_time
    duration_iso = datetime.now().isoformat()

    # SC-004 Check: 6-hour limit
    six_hours_seconds = 6 * 3600
    status = "PASS" if duration_seconds < six_hours_seconds else "FAIL"

    timing_log_entry = {
        "execution_id": "T030-e2e",
        "start_time": start_iso,
        "end_time": duration_iso,
        "duration_seconds": duration_seconds,
        "duration_formatted": f"{duration_seconds/3600:.2f} hours",
        "limit_seconds": six_hours_seconds,
        "limit_formatted": "6 hours",
        "status": status,
        "steps_total": len(PIPELINE_STEPS),
        "steps_success": success_count,
        "steps_failed": failure_count,
        "failed_step_names": failed_steps
    }

    # Write the timing log to the required location
    results_dir = get_path_results()
    ensure_directory(results_dir)
    timing_log_path = os.path.join(results_dir, "pipeline_timing.log")

    with open(timing_log_path, "w") as f:
        json.dump(timing_log_entry, f, indent=2)

    logger.info("=" * 80)
    logger.info("Pipeline Execution Summary")
    logger.info(f"  Total Steps: {len(PIPELINE_STEPS)}")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed: {failure_count}")
    logger.info(f"  Duration: {duration_seconds:.2f}s ({duration_seconds/3600:.2f} hours)")
    logger.info(f"  SC-004 Limit: 6 hours ({six_hours_seconds}s)")
    logger.info(f"  SC-004 Status: {status}")
    logger.info(f"  Timing Log: {timing_log_path}")
    logger.info("=" * 80)

    if failed_steps:
        logger.error(f"Pipeline completed with failures in: {', '.join(failed_steps)}")
        # Exit with error code if any step failed, as the pipeline did not fully succeed
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
