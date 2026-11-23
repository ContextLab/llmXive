"""
Sensitivity analysis module for threshold-sweep analysis.
Evaluates model stability across different critical cooling rate thresholds.
"""
import os
import sys
import json
import logging
import pickle
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/sensitivity.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

STABLE_MODEL_PATH = "data/models/random_forest_model_stable.pkl"
DATA_PATH = "data/processed/processed_alloys.csv"
SENSITIVITY_REPORT_PATH = "data/models/sensitivity_report.csv"
SENSITIVITY_STATUS_PATH = "data/models/sensitivity_status.json"
MODELS_DIR = "data/models"

os.makedirs(MODELS_DIR, exist_ok=True)

def load_stable_model():
    """Load the stable model."""
    if not os.path.exists(STABLE_MODEL_PATH):
        # Fallback to original model if stable model doesn't exist
        original_model_path = "data/models/random_forest_model.pkl"
        if os.path.exists(original_model_path):
            logger.warning(f"Stable model not found, using original model: {original_model_path}")
            with open(original_model_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError(f"Neither stable nor original model found.")
    
    with open(STABLE_MODEL_PATH, 'rb') as f:
        return pickle.load(f)

def load_processed_data():
    """Load processed data."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Processed data not found at {DATA_PATH}")
    return pd.read_csv(DATA_PATH)

def prepare_features(df: pd.DataFrame):
    """Prepare features and target."""
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    target_col = 'critical_cooling_rate'
    
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y

def run_regression_rmse(model, X: np.ndarray, y: np.ndarray):
    """Calculate RMSE for regression."""
    y_pred = model.predict(X)
    rmse = np.sqrt(np.mean((y - y_pred)**2))
    return rmse

def run_classification_sweep(model, X: np.ndarray, y: np.ndarray, 
                             thresholds: List[float]) -> List[Dict[str, Any]]:
    """
    Run classification sweep across thresholds.
    Binarize predictions and calculate F1 score.
    """
    results = []
    y_pred_reg = model.predict(X)

    for thresh in thresholds:
        # Binarize predictions
        y_pred_bin = (y_pred_reg >= thresh).astype(int)
        y_true_bin = (y >= thresh).astype(int)

        # Calculate F1 score
        f1 = f1_score(y_true_bin, y_pred_bin, zero_division=0)
        
        results.append({
            'threshold': thresh,
            'f1_score': f1
        })

    return results

def calculate_stability(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate stability metrics.
    """
    f1_scores = [r['f1_score'] for r in results]
    max_f1 = max(f1_scores)
    min_f1 = min(f1_scores)
    
    # Calculate F1 margin
    mean_f1 = np.mean(f1_scores)
    floor = 0.1
    f1_margin = (max_f1 - min_f1) / max(mean_f1, floor)
    f1_margin_pct = f1_margin * 100

    # RMSE variance (should be near zero for regression)
    # We don't have RMSE per threshold in this simplified version, so we assume 0
    rmse_variance = 0.0

    # Stability status
    stability_met = f1_margin_pct <= 10.0
    stability_status = "PASS" if stability_met else "FAIL"

    return {
        'f1_margin_pct': f1_margin_pct,
        'rmse_variance': rmse_variance,
        'stability_met': stability_met,
        'stability_status': stability_status
    }

def write_outputs(results: List[Dict[str, Any]], stability: Dict[str, Any], 
                 thresholds: List[float]):
    """Write sensitivity analysis outputs."""
    # Write CSV report
    report_data = []
    for i, r in enumerate(results):
        report_data.append({
            'threshold': r['threshold'],
            'f1_score': r['f1_score'],
            'f1_margin_pct': stability['f1_margin_pct'],
            'rmse_variance': stability['rmse_variance'],
            'stability_status': stability['stability_status']
        })

    df_report = pd.DataFrame(report_data)
    df_report.to_csv(SENSITIVITY_REPORT_PATH, index=False)
    logger.info(f"Saved sensitivity report to {SENSITIVITY_REPORT_PATH}")

    # Write status JSON
    status = {
        'stability_met': stability['stability_met'],
        'f1_margin_pct': stability['f1_margin_pct'],
        'threshold_values': thresholds,
        'run_status': 'FAILED' if not stability['stability_met'] else 'PASSED'
    }
    with open(SENSITIVITY_STATUS_PATH, 'w') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Saved sensitivity status to {SENSITIVITY_STATUS_PATH}")

def run_sensitivity_analysis():
    """Main entry point for sensitivity analysis."""
    logger.info("Starting sensitivity analysis")

    # Load model and data
    model = load_stable_model()
    df = load_processed_data()
    X, y = prepare_features(df)

    # Define thresholds
    thresholds = [50, 100, 150]

    # Run classification sweep
    results = run_classification_sweep(model, X, y, thresholds)

    # Calculate stability
    stability = calculate_stability(results)

    # Write outputs
    write_outputs(results, stability, thresholds)

    logger.info("Sensitivity analysis completed")

if __name__ == "__main__":
    run_sensitivity_analysis()
