"""
T017: Verify no NaN values in logged metrics and graceful handling of state explosion warnings.

This module provides:
1. A validator to scan metric logs for NaN/Inf values.
2. A handler to catch and log state explosion warnings gracefully.
3. Integration logic to be called by the simulation runner.
"""
import logging
import json
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Constants for state explosion detection
STATE_EXPLOSION_THRESHOLD = 1e6  # Example threshold for metric magnitude
MAX_ALLOWED_NAN_COUNT = 0

class StateExplosionWarning(Warning):
    """Custom warning for state explosion events."""
    pass

def validate_metrics_no_nan(metrics_df: pd.DataFrame, log_path: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Validates that the provided DataFrame of metrics contains no NaN or Inf values.

    Args:
        metrics_df: DataFrame containing logged metrics (e.g., coherence_score, diversity_score, step_latency).
        log_path: Optional path to a log file to write validation errors.

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    if metrics_df.empty:
        errors.append("Metrics DataFrame is empty.")
        return False, errors

    # Check for NaN
    nan_mask = metrics_df.isna()
    if nan_mask.any().any():
        nan_columns = nan_mask.columns[nan_mask.any()].tolist()
        for col in nan_columns:
            count = nan_mask[col].sum()
            errors.append(f"Column '{col}' contains {count} NaN values.")

    # Check for Inf
    inf_mask = np.isinf(metrics_df.astype(float))
    if inf_mask.any().any():
        inf_columns = inf_mask.columns[inf_mask.any()].tolist()
        for col in inf_columns:
            count = inf_mask[col].sum()
            errors.append(f"Column '{col}' contains {count} Inf values.")

    if errors:
        if log_path:
            try:
                with open(log_path, 'a') as f:
                    f.write(json.dumps({"validation_error": errors}) + "\n")
            except IOError as e:
                logger.error(f"Failed to write validation errors to {log_path}: {e}")
        return False, errors

    return True, []

def handle_state_explosion_warning(metric_value: float, metric_name: str, context: Dict) -> bool:
    """
    Gracefully handles a potential state explosion event.

    Args:
        metric_value: The current value of the metric that triggered the check.
        metric_name: Name of the metric (e.g., 'population_size', 'energy_deviation').
        context: Dictionary containing simulation context (step, config, etc.).

    Returns:
        True if the run should be terminated gracefully, False otherwise.
    """
    if np.isinf(metric_value) or abs(metric_value) > STATE_EXPLOSION_THRESHOLD:
        warning_msg = f"State explosion detected: {metric_name} = {metric_value} at step {context.get('step', 'N/A')}"
        logger.warning(warning_msg)
        
        # Log the warning to the structured log if available
        if 'log_path' in context:
            try:
                log_entry = {
                    "type": "state_explosion_warning",
                    "metric": metric_name,
                    "value": str(metric_value),
                    "step": context.get('step'),
                    "config": context.get('config', {})
                }
                with open(context['log_path'], 'a') as f:
                    f.write(json.dumps(log_entry) + "\n")
            except IOError:
                pass

        # Raise a warning to be caught by the main loop if necessary
        # In a real scenario, this might trigger a graceful shutdown or rollback
        raise StateExplosionWarning(warning_msg)
    
    return False

def check_metrics_for_explosion(metrics_df: pd.DataFrame) -> List[Dict]:
    """
    Scans a DataFrame of metrics for values indicating state explosion.

    Args:
        metrics_df: DataFrame of metrics.

    Returns:
        List of dictionaries describing explosion events found.
    """
    explosions = []
    numeric_cols = metrics_df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        # Check for Inf
        inf_indices = np.isinf(metrics_df[col]).nonzero()[0]
        for idx in inf_indices:
            explosions.append({
                "type": "inf_value",
                "column": col,
                "row_index": int(idx),
                "value": str(metrics_df[col].iloc[idx])
            })
        
        # Check for threshold exceedance
        threshold_mask = metrics_df[col].abs() > STATE_EXPLOSION_THRESHOLD
        exceedance_indices = threshold_mask.nonzero()[0]
        for idx in exceedance_indices:
            # Avoid double counting if it's also Inf
            if not np.isinf(metrics_df[col].iloc[idx]):
                explosions.append({
                    "type": "threshold_exceeded",
                    "column": col,
                    "row_index": int(idx),
                    "value": str(metrics_df[col].iloc[idx]),
                    "threshold": STATE_EXPLOSION_THRESHOLD
                })
    
    return explosions

def run_validation_on_log(log_path: str) -> Dict:
    """
    Runs the full validation suite on a generated log file.

    Args:
        log_path: Path to the JSONL or CSV log file generated by the simulation.

    Returns:
        Dictionary with validation results.
    """
    result = {
        "path": log_path,
        "nan_check_passed": False,
        "explosion_check_passed": False,
        "errors": [],
        "warnings": []
    }

    if not os.path.exists(log_path):
        result["errors"].append(f"Log file not found: {log_path}")
        return result

    try:
        # Attempt to load as CSV first, then JSONL if needed
        if log_path.endswith('.csv'):
            df = pd.read_csv(log_path)
        else:
            # Assume JSONL for complex logs
            df = pd.read_json(log_path, lines=True)
    except Exception as e:
        result["errors"].append(f"Failed to parse log file: {str(e)}")
        return result

    # 1. Check for NaN
    is_valid, nan_errors = validate_metrics_no_nan(df)
    result["nan_check_passed"] = is_valid
    if not is_valid:
        result["errors"].extend(nan_errors)

    # 2. Check for State Explosion
    explosions = check_metrics_for_explosion(df)
    if explosions:
        result["explosion_check_passed"] = False
        result["warnings"].extend([
            f"Explosion event in {e['column']} at row {e['row_index']}: {e['type']}"
            for e in explosions
        ])
    else:
        result["explosion_check_passed"] = True

    return result

def main():
    """
    CLI entry point for T017 validation.
    Usage: python -m src.analysis.NaN_and_explosion_guard --log-path data/raw/simulation_run.jsonl
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate simulation logs for NaN and State Explosion.")
    parser.add_argument("--log-path", type=str, required=True, help="Path to the simulation log file.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    
    logger.info(f"Running T017 validation on {args.log_path}")
    report = run_validation_on_log(args.log_path)

    print(json.dumps(report, indent=2))

    if report["errors"] or not report["nan_check_passed"] or not report["explosion_check_passed"]:
        logger.error("Validation FAILED.")
        exit(1)
    else:
        logger.info("Validation PASSED.")
        exit(0)

if __name__ == "__main__":
    main()
