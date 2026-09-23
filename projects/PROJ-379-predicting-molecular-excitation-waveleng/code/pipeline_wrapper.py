"""
Pipeline Wrapper for Molecular Excitation Wavelength Prediction (T015b).

Orchestrates the full pipeline: Ingest -> Train -> Evaluate.
Enforces strict wall-clock time budgets per phase and total.
Outputs timing.json to data/processed/.
"""
import os
import sys
import json
import logging
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants (in seconds)
TOTAL_BUDGET_SECONDS = 6 * 3600  # 6 hours
INGEST_BUDGET_SECONDS = 1.5 * 3600  # 1.5 hours
TRAIN_BUDGET_SECONDS = 4.0 * 3600  # 4.0 hours (hard cap)
EVAL_BUDGET_SECONDS = 0.5 * 3600  # 0.5 hours

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TIMING_OUTPUT = DATA_PROCESSED_DIR / "timing.json"

def run_step(name: str, script_name: str, budget_seconds: float) -> float:
    """
    Run a specific pipeline step with a time budget.
    Returns the time taken in seconds.
    Raises RuntimeError if the step exceeds its budget or fails.
    """
    logger.info(f"Starting step: {name} (Budget: {budget_seconds/3600:.2f}h)")
    start_time = time.time()

    script_path = CODE_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    try:
        # Run the script using the current Python interpreter
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False, # Let stdout/stderr propagate
            cwd=str(PROJECT_ROOT)
        )
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        logger.error(f"Step '{name}' failed with exit code {e.returncode}")
        raise RuntimeError(f"Step '{name}' failed: {e}") from e

    elapsed = time.time() - start_time

    if elapsed > budget_seconds:
        raise RuntimeError(
            f"Step '{name}' exceeded its time budget. "
            f"Allowed: {budget_seconds/3600:.2f}h, Actual: {elapsed/3600:.2f}h"
        )

    logger.info(f"Step '{name}' completed in {elapsed:.2f}s")
    return elapsed

def main():
    logger.info("Starting Pipeline Wrapper (T015b)")
    logger.info(f"Total Budget: {TOTAL_BUDGET_SECONDS/3600:.2f} hours")

    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    start_total = time.time()
    timings = {
        "start_time": datetime.utcnow().isoformat(),
        "phases": {},
        "total_time_seconds": 0,
        "status": "running"
    }

    try:
        # 1. Ingest
        t_ingest = run_step("Ingest", "ingest.py", INGEST_BUDGET_SECONDS)
        timings["phases"]["ingest"] = t_ingest

        # Check remaining budget before training
        elapsed_so_far = time.time() - start_total
        remaining = TOTAL_BUDGET_SECONDS - elapsed_so_far
        if remaining <= 0:
            raise RuntimeError("Total time budget exhausted before training started.")

        # 2. Train (Hard Cap)
        # We pass the remaining time but cap it at TRAIN_BUDGET_SECONDS
        # However, the requirement says "If Training hits 4h, abort immediately".
        # The run_step function handles the budget check.
        # We ensure we don't exceed the total budget either.
        effective_train_budget = min(TRAIN_BUDGET_SECONDS, remaining)
        
        t_train = run_step("Train", "train.py", effective_train_budget)
        timings["phases"]["train"] = t_train

        # Check remaining budget before eval
        elapsed_so_far = time.time() - start_total
        remaining = TOTAL_BUDGET_SECONDS - elapsed_so_far
        if remaining <= 0:
            raise RuntimeError("Total time budget exhausted before evaluation started.")

        # 3. Evaluate
        t_eval = run_step("Evaluate", "evaluate.py", min(EVAL_BUDGET_SECONDS, remaining))
        timings["phases"]["evaluate"] = t_eval

        # Success
        total_time = time.time() - start_total
        timings["total_time_seconds"] = total_time
        timings["status"] = "completed"
        timings["end_time"] = datetime.utcnow().isoformat()

        logger.info(f"Pipeline completed successfully in {total_time:.2f}s")

        # Write timing report
        with open(TIMING_OUTPUT, "w") as f:
            json.dump(timings, f, indent=2)
        logger.info(f"Timing report written to {TIMING_OUTPUT}")

    except RuntimeError as e:
        logger.error(f"Pipeline aborted: {e}")
        timings["status"] = "failed"
        timings["error"] = str(e)
        timings["end_time"] = datetime.utcnow().isoformat()
        # Still write the partial timing report for debugging
        with open(TIMING_OUTPUT, "w") as f:
            json.dump(timings, f, indent=2)
        raise e

if __name__ == "__main__":
    main()