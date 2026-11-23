"""
T017 Implementation: NaN and State Explosion Validator.

This module provides utilities to verify that logged metrics contain no NaN values
and to gracefully handle state explosion warnings during simulation runs.

It implements the logic required for Task T017:
1. Scan metric logs (JSON/CSV) for NaN values.
2. Parse logs for 'State Explosion' warnings.
3. Gracefully handle these conditions (flagging, logging, or terminating)
   without crashing the pipeline.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import existing data models and logging setup from the project
# Assuming T007 created src/data_models.py and T010 created logging infrastructure
try:
    from src.data_models import MetricRecord
    from src.config import get_logger
except ImportError:
    # Fallback for standalone execution if imports fail
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
            logger.addHandler(handler)
        return logger

logger = get_logger(__name__)

# Constants for state explosion detection
STATE_EXPLOSION_THRESHOLD = 1e6  # Example threshold for state size
WARNING_KEYWORDS = [
    "State Explosion",
    "Memory Limit",
    "OOM",
    "State Size Exceeded",
    "Unstable Configuration"
]


def check_metrics_for_nan(
    metrics_data: Dict[str, Any] | pd.DataFrame | List[Dict],
    tolerance: float = 1e-9
) -> Tuple[bool, List[str]]:
    """
    Check a collection of metric records for NaN values.

    Args:
        metrics_data: Can be a dict, DataFrame, or list of dicts containing metrics.
        tolerance: Floating point tolerance for considering a value as NaN/Inf.

    Returns:
        Tuple of (is_clean, list_of_error_messages).
        is_clean is True if no NaN/Inf values are found.
    """
    errors = []

    if isinstance(metrics_data, pd.DataFrame):
        df = metrics_data
    elif isinstance(metrics_data, dict):
        df = pd.DataFrame([metrics_data])
    elif isinstance(metrics_data, list):
        if not metrics_data:
            return True, []
        df = pd.DataFrame(metrics_data)
    else:
        errors.append(f"Unsupported metrics data type: {type(metrics_data)}")
        return False, errors

    # Check for NaN and Inf
    nan_mask = df.isna()
    inf_mask = np.isinf(df.select_dtypes(include=[np.number]).values)
    
    # Convert inf mask back to DataFrame structure for alignment
    inf_df = pd.DataFrame(inf_mask, index=df.index, columns=df.select_dtypes(include=[np.number]).columns)
    
    # Combine
    problematic = nan_mask | inf_df

    if problematic.any().any():
        for col in problematic.columns:
            if problematic[col].any():
                indices = problematic[problematic[col]].index.tolist()
                errors.append(f"Column '{col}' contains NaN/Inf at indices: {indices}")
        
        logger.warning(f"Metrics validation failed: {len(errors)} error(s) found.")
        return False, errors
    
    logger.info("Metrics validation passed: No NaN or Inf values detected.")
    return True, []


def detect_state_explosion_warnings(log_path: str) -> List[Dict[str, Any]]:
    """
    Scan a log file for state explosion warnings and extract relevant context.

    Args:
        log_path: Path to the log file (text or JSON lines).

    Returns:
        List of dictionaries containing warning details.
    """
    warnings_found = []

    if not os.path.exists(log_path):
        logger.warning(f"Log file not found: {log_path}")
        return warnings_found

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Check for keywords
                is_warning = any(keyword.lower() in line_stripped.lower() for keyword in WARNING_KEYWORDS)
                
                if is_warning:
                    warning_entry = {
                        "line_number": line_num,
                        "content": line_stripped,
                        "severity": "WARNING",
                        "type": "State Explosion Detected"
                    }
                    
                    # Try to parse as JSON if it looks like structured logging
                    if line_stripped.startswith('{'):
                        try:
                            json_data = json.loads(line_stripped)
                            warning_entry.update(json_data)
                        except json.JSONDecodeError:
                            pass
                    
                    warnings_found.append(warning_entry)
                    logger.warning(f"State explosion warning detected at line {line_num}: {line_stripped[:100]}...")

    except Exception as e:
        logger.error(f"Error reading log file {log_path}: {e}")

    return warnings_found


def handle_state_explosion(
    warnings: List[Dict[str, Any]],
    metrics_path: Optional[str] = None,
    action: str = "flag"
) -> bool:
    """
    Gracefully handle state explosion warnings based on the configured action.

    Args:
        warnings: List of detected warnings.
        metrics_path: Optional path to the metrics file to update.
        action: One of 'flag', 'terminate', 'ignore'.
                - 'flag': Mark the run as unstable in the metrics/log.
                - 'terminate': Return False to signal the pipeline should stop.
                - 'ignore': Log and continue (not recommended).

    Returns:
        True if the run can continue, False if it must be terminated.
    """
    if not warnings:
        return True

    logger.warning(f"Handling {len(warnings)} state explosion warnings.")

    if action == "ignore":
        return True

    elif action == "flag":
        # Update metrics file if provided to mark as unstable
        if metrics_path and os.path.exists(metrics_path):
            try:
                # Try to load as JSON lines first, then CSV
                df = None
                if metrics_path.endswith('.json'):
                    # Attempt JSON load
                    try:
                        with open(metrics_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                df = pd.DataFrame(data)
                    except json.JSONDecodeError:
                        pass
                
                if df is None:
                    df = pd.read_csv(metrics_path)

                # Add or update a column
                df['is_unstable'] = True
                df['explosion_warning_count'] = len(warnings)
                
                # Save back
                if metrics_path.endswith('.json'):
                    df.to_json(metrics_path, orient='records', lines=True)
                else:
                    df.to_csv(metrics_path, index=False)
                
                logger.info(f"Marked metrics file {metrics_path} as unstable.")
            except Exception as e:
                logger.error(f"Failed to update metrics file: {e}")
        
        return True

    elif action == "terminate":
        logger.error("State explosion detected. Terminating run.")
        return False

    else:
        logger.error(f"Unknown action '{action}' for state explosion handling.")
        return True


def validate_run_artifacts(
    run_id: str,
    base_dir: str = "data/raw",
    metrics_file: str = "metrics.csv",
    log_file: str = "run.log",
    action: str = "flag"
) -> Dict[str, Any]:
    """
    Main entry point to validate a specific simulation run.
    
    Args:
        run_id: Unique identifier for the run.
        base_dir: Base directory where run data is stored.
        metrics_file: Name of the metrics file.
        log_file: Name of the log file.
        action: How to handle state explosions.

    Returns:
        Dictionary with validation results.
    """
    run_dir = Path(base_dir) / run_id
    metrics_path = run_dir / metrics_file
    log_path = run_dir / log_file

    result = {
        "run_id": run_id,
        "nan_check_passed": False,
        "explosion_warnings": [],
        "run_status": "unknown",
        "details": []
    }

    # 1. Check Metrics for NaN
    if metrics_path.exists():
        try:
            df = pd.read_csv(metrics_path)
            is_clean, errors = check_metrics_for_nan(df)
            result["nan_check_passed"] = is_clean
            if not is_clean:
                result["details"].extend(errors)
        except Exception as e:
            result["details"].append(f"Error reading metrics: {e}")
    else:
        result["details"].append(f"Metrics file not found: {metrics_path}")

    # 2. Check Logs for State Explosion
    if log_path.exists():
        warnings = detect_state_explosion_warnings(str(log_path))
        result["explosion_warnings"] = warnings
        
        if warnings:
            can_continue = handle_state_explosion(
                warnings, 
                str(metrics_path) if metrics_path.exists() else None,
                action
            )
            result["run_status"] = "stable" if can_continue else "terminated"
            if not can_continue:
                result["details"].append("Run terminated due to state explosion.")
        else:
            result["run_status"] = "stable"
    else:
        result["details"].append(f"Log file not found: {log_path}")

    # Final Status
    if result["nan_check_passed"] and result["run_status"] == "stable":
        result["overall_status"] = "PASS"
    else:
        result["overall_status"] = "FAIL"

    return result


def main():
    """
    CLI entry point for T017 validation.
    Usage: python src/analysis/NaN_and_explosion_validator.py --run_id <id> --base_dir <dir>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate simulation run for NaN and State Explosion.")
    parser.add_argument("--run_id", type=str, required=True, help="Run ID to validate")
    parser.add_argument("--base_dir", type=str, default="data/raw", help="Base directory for run data")
    parser.add_argument("--metrics_file", type=str, default="metrics.csv", help="Metrics filename")
    parser.add_argument("--log_file", type=str, default="run.log", help="Log filename")
    parser.add_argument("--action", type=str, default="flag", choices=["flag", "terminate", "ignore"], help="Action on explosion")

    args = parser.parse_args()

    result = validate_run_artifacts(
        run_id=args.run_id,
        base_dir=args.base_dir,
        metrics_file=args.metrics_file,
        log_file=args.log_file,
        action=args.action
    )

    # Output result to stdout as JSON for easy parsing by CI/CD
    print(json.dumps(result, indent=2))

    # Exit with error code if validation failed
    if result["overall_status"] == "FAIL":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
