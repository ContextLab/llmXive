"""
T015c: Populate Sensitivity Report
Writes data/sensitivity_report.csv with results from T013f (scores) and T014 (p-values).
"""
import os
import csv
import logging
import json
from typing import List, Dict, Any, Optional

from utils.logging import get_logger, setup_logging

# Ensure logging is set up
setup_logging()
logger = get_logger(__name__)

SENSITIVITY_REPORT_PATH = "data/sensitivity_report.csv"
RUN_STATE_PATH = "data/run_state.json"
VALIDATION_LOG_PATH = "data/shift_validation.log"

def load_run_state() -> List[Dict[str, Any]]:
    """Load the run state from T013f."""
    if not os.path.exists(RUN_STATE_PATH):
        logger.error(f"Run state file not found: {RUN_STATE_PATH}")
        return []
    with open(RUN_STATE_PATH, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {RUN_STATE_PATH}")
            return []

def load_validation_log() -> Dict[str, float]:
    """
    Load the validation log from T014 to get p-values.
    Expected format: lines containing 'env_id=<id> p_value=<value>' or similar.
    We parse the log to extract p-values per environment.
    """
    p_values = {}
    if not os.path.exists(VALIDATION_LOG_PATH):
        logger.warning(f"Validation log not found: {VALIDATION_LOG_PATH}. Assuming p-values are 1.0 (no drop).")
        return p_values

    with open(VALIDATION_LOG_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Simple parsing: look for patterns like "env_id=X p_value=Y"
            # Adjust regex if log format differs, but assuming standard log format
            try:
                parts = line.split()
                env_id = None
                p_val = None
                for part in parts:
                    if part.startswith("env_id="):
                        env_id = part.split("=")[1]
                    elif part.startswith("p_value="):
                        p_val = float(part.split("=")[1])
                if env_id and p_val is not None:
                    p_values[env_id] = p_val
            except (ValueError, IndexError):
                continue
    return p_values

def calculate_drop_rate(pre_score: float, post_score: float) -> float:
    """Calculate the drop rate: (pre - post) / pre."""
    if pre_score == 0:
        return 0.0 if post_score == 0 else 1.0
    return max(0.0, (pre_score - post_score) / pre_score)

def populate_sensitivity_report():
    """
    Main logic for T015c.
    Reads run_state (scores) and validation_log (p-values) and writes sensitivity_report.csv.
    """
    run_state = load_run_state()
    p_values = load_validation_log()

    if not run_state:
        logger.warning("No run state data found. Writing empty report with headers.")
        write_header_only()
        return

    # Group by env_id to aggregate multiple runs if necessary, or just take the first valid entry per env
    # The task implies writing the report with the results. We'll assume one row per env_id
    # using the first valid run state entry for that env_id.
    env_data = {}
    for entry in run_state:
        env_id = entry.get("env_id")
        if not env_id:
            continue
        if env_id not in env_data:
            env_data[env_id] = {
                "pre_shift_score": entry.get("pre_shift_score", 0.0),
                "post_shift_score": entry.get("score", 0.0), # Assuming 'score' is post-shift in this context
                "p_value": p_values.get(env_id, 1.0)
            }

    # Write to CSV
    with open(SENSITIVITY_REPORT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        # Headers as defined in T015b
        writer.writerow(["env_id", "shift_step", "pre_shift_score", "post_shift_score", "drop_rate", "p_value"])

        for env_id, data in env_data.items():
            pre = data["pre_shift_score"]
            post = data["post_shift_score"]
            p_val = data["p_value"]
            drop = calculate_drop_rate(pre, post)
            # shift_step is not explicitly in run_state, default to 0 or extract if available
            shift_step = entry.get("shift_step", 0) if "shift_step" in entry else 0
            
            writer.writerow([
                env_id,
                shift_step,
                f"{pre:.4f}",
                f"{post:.4f}",
                f"{drop:.4f}",
                f"{p_val:.4f}"
            ])

    logger.info(f"Sensitivity report written to {SENSITIVITY_REPORT_PATH}")

def write_header_only():
    """Write an empty CSV with headers if no data is available."""
    with open(SENSITIVITY_REPORT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["env_id", "shift_step", "pre_shift_score", "post_shift_score", "drop_rate", "p_value"])
    logger.info(f"Empty sensitivity report written to {SENSITIVITY_REPORT_PATH}")

def main():
    populate_sensitivity_report()

if __name__ == "__main__":
    main()
