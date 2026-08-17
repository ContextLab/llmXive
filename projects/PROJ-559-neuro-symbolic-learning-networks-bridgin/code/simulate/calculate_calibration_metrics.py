import os
import sys
import json
import logging
import argparse
import pandas as pd
from typing import Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PILOT_DIR = os.path.join(PROJECT_ROOT, 'data', 'pilot')
METRICS_PATH = os.path.join(DATA_PILOT_DIR, 'calibration_metrics.json')
CALIBRATION_REPORT_PATH = os.path.join(DATA_PILOT_DIR, 'calibration_report.json')

def load_report(path: str = CALIBRATION_REPORT_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Calibration report not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_human_data(path: str = None) -> pd.DataFrame:
    """
    Load the human pilot data from the validated source.
    MUST FAIL LOUDLY if the real data is missing or invalid.
    No synthetic fallback allowed.
    """
    report = load_report()
    has_human = report.get('has_human_data', False)
    
    if not has_human:
        raise FileNotFoundError("ERROR: Human pilot data missing or invalid (has_human_data=False in report). "
                              "Calibration cannot proceed. Pipeline halted.")

    human_path = os.path.join(DATA_PILOT_DIR, 'raw_pilot_data.csv')
    if not os.path.exists(human_path):
        raise FileNotFoundError(f"ERROR: Human data file not found at {human_path} despite report flag. "
                              "Pipeline halted.")
    
    df = pd.read_csv(human_path)
    
    # Validate minimum record count (>=50 as per T031b)
    if len(df) < 50:
        raise ValueError(f"ERROR: Human pilot data has {len(df)} records, but minimum 50 required. "
                       "Pipeline halted.")
    
    logger.info(f"Successfully loaded {len(df)} human pilot records from {human_path}")
    return df

def calculate_rmse_diff(predicted: pd.Series, actual: pd.Series) -> float:
    """
    Calculate the Root Mean Squared Error (RMSE) between predicted and actual performance.
    This serves as the primary metric for calibration difference.
    """
    if len(predicted) != len(actual):
        raise ValueError("Predicted and actual series must have the same length.")
    
    if predicted.isna().any() or actual.isna().any():
        raise ValueError("Data contains NaN values. Cannot calculate RMSE.")
    
    mse = ((predicted - actual) ** 2).mean()
    rmse = mse ** 0.5
    return float(rmse)

def run_metrics_check():
    """
    Main logic for T032: Calculate RMSE difference and absolute RMSE.
    Exits with code 1 if thresholds are failed on valid human data.
    """
    logger.info("Running Calibration Metrics Calculation (T032)...")
    
    try:
        report = load_report()
        pilot_data = load_human_data()
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Ensure required columns exist
    required_cols = ['predicted_accuracy', 'actual_accuracy']
    missing = [c for c in required_cols if c not in pilot_data.columns]
    if missing:
        logger.error(f"Missing required columns in pilot data: {missing}")
        sys.exit(1)
    
    predicted = pilot_data['predicted_accuracy']
    actual = pilot_data['actual_accuracy']
    
    # Calculate RMSE (Absolute RMSE)
    abs_rmse = calculate_rmse_diff(predicted, actual)
    
    # RMSE Difference: In this calibration context, we compare the model's error
    # against a baseline (e.g., 0.0 or a theoretical optimum). 
    # Here we treat the calculated RMSE as the deviation from perfect prediction.
    rmse_diff = abs_rmse 
    
    # Thresholds per task description
    RMSE_DIFF_THRESHOLD = 0.02
    ABS_RMSE_THRESHOLD = 0.15
    
    passed = True
    reason = "All metrics within thresholds."
    
    if rmse_diff > RMSE_DIFF_THRESHOLD:
        passed = False
        reason = f"RMSE difference ({rmse_diff:.4f}) exceeds threshold ({RMSE_DIFF_THRESHOLD})."
    
    if abs_rmse > ABS_RMSE_THRESHOLD:
        passed = False
        reason = f"Absolute RMSE ({abs_rmse:.4f}) exceeds threshold ({ABS_RMSE_THRESHOLD})."
    
    # CRITICAL: If human data was used and thresholds failed, exit with error
    # This enforces FR-010: Simulation cannot proceed without valid calibration.
    if report.get('has_human_data', False) and not passed:
        logger.error(f"Calibration FAILED on human data: {reason}")
        logger.error("Exiting with code 1 to block simulation.")
        sys.exit(1)
    
    # Metrics to save
    metrics = {
        "rmse": float(abs_rmse),
        "rmse_diff": float(rmse_diff),
        "passed": passed,
        "threshold_rmse_diff": RMSE_DIFF_THRESHOLD,
        "threshold_abs_rmse": ABS_RMSE_THRESHOLD,
        "data_source": "human",
        "record_count": len(pilot_data)
    }
    
    os.makedirs(DATA_PILOT_DIR, exist_ok=True)
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {METRICS_PATH}")
    logger.info(f"Result: {'PASSED' if passed else 'FAILED'} - {reason}")
    
    return 0

def main():
    return run_metrics_check()

if __name__ == "__main__":
    sys.exit(main())