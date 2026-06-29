import os
import json
import logging
import random
import hashlib
import math
from typing import Dict, Any, List, Optional, Tuple

# Configure logging to ensure warnings and errors are visible
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thresholds defined in T032
RMSE_DIFF_THRESHOLD = 0.02
ABSOLUTE_RMSE_THRESHOLD = 0.15

def _calculate_rmse(predictions: List[float], actuals: List[float]) -> float:
    """Calculate Root Mean Squared Error."""
    if len(predictions) != len(actuals) or len(predictions) == 0:
        raise ValueError("Predictions and actuals must be non-empty and of equal length.")
    
    squared_errors = [(p - a) ** 2 for p, a in zip(predictions, actuals)]
    mse = sum(squared_errors) / len(squared_errors)
    return math.sqrt(mse)

def _generate_synthetic_pilot_data(n_participants: int = 50, seed: int = 42) -> Tuple[List[float], List[float]]:
    """
    Generate synthetic pilot data for calibration when human data is missing.
    Returns (bkt_predictions, human_actuals).
    """
    random.seed(seed)
    predictions = []
    actuals = []
    
    # Simulate a scenario where BKT is close but has some noise
    # Target: RMSE around 0.05-0.10 to test thresholds
    base_skill = 0.75
    for _ in range(n_participants):
        # Simulate a human actual probability (0.0 to 1.0)
        human_actual = random.gauss(base_skill, 0.15)
        human_actual = max(0.0, min(1.0, human_actual))
        
        # Simulate BKT prediction with small systematic bias + noise
        bkt_pred = human_actual + random.gauss(0.0, 0.05)
        bkt_pred = max(0.0, min(1.0, bkt_pred))
        
        predictions.append(bkt_pred)
        actuals.append(human_actual)
    
    return predictions, actuals

def _load_human_pilot_data() -> Optional[Tuple[List[float], List[float]]]:
    """
    Attempt to load real human pilot data from data/pilot/human_data.json.
    Returns (bkt_predictions, human_actuals) or None if file missing/invalid.
    """
    data_path = "data/pilot/human_data.json"
    if not os.path.exists(data_path):
        return None
    
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        if 'bkt_predictions' not in data or 'human_actuals' not in data:
            logger.warning(f"Human data file {data_path} missing required keys.")
            return None
        
        preds = data['bkt_predictions']
        actuals = data['human_actuals']
        
        if len(preds) != len(actuals) or len(preds) < 50:
            logger.warning(f"Human data in {data_path} has insufficient or mismatched samples.")
            return None
        
        return preds, actuals
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load human pilot data: {e}")
        return None

def run_calibration() -> Dict[str, Any]:
    """
    Run calibration logic for T032.
    
    1. Checks for human pilot data.
    2. If missing, generates synthetic data and logs a warning.
    3. Calculates RMSE and RMSE difference against thresholds.
    4. Validates:
       - RMSE difference <= 0.02
       - Absolute RMSE <= 0.15
    5. Behavior:
       - If valid human data exists and thresholds fail: Exit with code 1.
       - If synthetic data used (missing human): Log warning if thresholds fail, do NOT exit 1.
       - If thresholds pass: Log success.
    
    Returns a dict with calibration status and metrics.
    """
    logger.info("Starting calibration process (T032).")
    
    # 1. Attempt to load human data
    human_data = _load_human_pilot_data()
    use_synthetic = False
    
    if human_data is None:
        logger.warning("Human pilot data not found. Generating synthetic fallback data.")
        bkt_preds, human_actuals = _generate_synthetic_pilot_data()
        use_synthetic = True
    else:
        bkt_preds, human_actuals = human_data
        logger.info(f"Loaded {len(human_actuals)} human pilot records.")
    
    # 2. Calculate Metrics
    try:
        rmse = _calculate_rmse(bkt_preds, human_actuals)
        # RMSE difference is effectively the RMSE itself in this context (deviation from actual)
        # If we had a 'previous' baseline, we'd subtract, but here RMSE is the primary metric.
        rmse_diff = rmse 
    except ValueError as e:
        logger.error(f"Error calculating metrics: {e}")
        return {
            "calibration_valid": False,
            "error": str(e),
            "exit_code": 1 if not use_synthetic else 0
        }
    
    logger.info(f"Calibration Metrics: RMSE = {rmse:.4f}, RMSE Diff = {rmse_diff:.4f}")
    
    # 3. Validate against thresholds
    is_rmse_diff_ok = rmse_diff <= RMSE_DIFF_THRESHOLD
    is_abs_rmse_ok = rmse <= ABSOLUTE_RMSE_THRESHOLD
    
    is_valid = is_rmse_diff_ok and is_abs_rmse_ok
    
    # 4. Determine outcome based on data source and validity
    if is_valid:
        logger.info("Calibration PASSED: All thresholds met.")
        status = "passed"
    else:
        if use_synthetic:
            logger.warning(f"Calibration WARNED (Synthetic Data): Thresholds failed (RMSE={rmse:.4f}, Diff={rmse_diff:.4f}). "
                           f"Thresholds: Diff <= {RMSE_DIFF_THRESHOLD}, Abs <= {ABSOLUTE_RMSE_THRESHOLD}. "
                           f"Proceeding with synthetic data as per T032 requirements.")
            status = "failed_synthetic_warning"
        else:
            logger.error(f"Calibration FAILED (Human Data): Thresholds violated (RMSE={rmse:.4f}, Diff={rmse_diff:.4f}). "
                         f"Thresholds: Diff <= {RMSE_DIFF_THRESHOLD}, Abs <= {ABSOLUTE_RMSE_THRESHOLD}. "
                         f"Exiting with code 1 as per T032 requirements.")
            status = "failed_human_error"
    
    # 5. Prepare report
    report = {
        "calibration_valid": is_valid,
        "metrics": {
            "rmse": rmse,
            "rmse_diff": rmse_diff,
            "threshold_rmse_diff": RMSE_DIFF_THRESHOLD,
            "threshold_abs_rmse": ABSOLUTE_RMSE_THRESHOLD
        },
        "data_source": "synthetic" if use_synthetic else "human",
        "status": status,
        "thresholds": {
            "rmse_diff_limit": RMSE_DIFF_THRESHOLD,
            "abs_rmse_limit": ABSOLUTE_RMSE_THRESHOLD
        }
    }
    
    # 6. Write report to disk
    report_path = "data/pilot/calibration_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Calibration report written to {report_path}")
    
    # 7. Handle exit logic
    if not is_valid and not use_synthetic:
        # Fail loudly on real human data
        import sys
        sys.exit(1)
    
    return report

if __name__ == "__main__":
    result = run_calibration()
    logger.info(f"Calibration completed with status: {result['status']}")