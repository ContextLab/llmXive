"""
T029: Save a consolidated metrics summary (R², MAE, RMSE, corrected p-values, significance flags) to results/metrics.json.

This script aggregates model evaluation results from the trained models (Random Forest, Gradient Boosting)
and the statistical tests performed against the baseline. It loads predictions and test data,
computes the required metrics, and writes a consolidated JSON report to results/metrics.json.

Dependencies:
- code/utils/metrics.py (for statistical tests if re-running, though usually results are passed or loaded)
- code/02_train_models.py (produces the model artifacts and predictions)
- code/02_statistical_evaluation.py (produces the statistical test results)

Note: This task assumes that T028 (statistical tests) has been run and its results are available,
or that this script performs the final aggregation of metrics computed in previous steps.
Given the pipeline flow, we will load the model predictions, compute R2/MAE/RMSE, and load
the statistical test results from the intermediate output of T028 (or re-calculate if necessary).

To ensure robustness, this script will:
1. Load test data from data/processed/test.csv.
2. Load model predictions (saved as pickles or json by the training/evaluation step).
3. Calculate R², MAE, RMSE for each model.
4. Load or re-compute the Bonferroni-corrected p-values and significance flags.
5. Save the consolidated summary to results/metrics.json.
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Add project root to path to allow imports from code/ and utils/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import setup_logging, get_config
from code.utils.metrics import paired_t_test, bonferroni_correct

# Configure logging
logger = setup_logging()
config = get_config()

# Paths
DATA_DIR = project_root / "data" / "processed"
RESULTS_DIR = project_root / "results"
TEST_DATA_PATH = DATA_DIR / "test.csv"
MODELS_DIR = project_root / "state" / "projects" / config.project_id / "models"
PREDICTIONS_DIR = project_root / "state" / "projects" / config.project_id / "predictions"
STAT_RESULTS_PATH = RESULTS_DIR / "statistical_test_results.json"
METRICS_OUTPUT_PATH = RESULTS_DIR / "metrics.json"

def load_test_data() -> pd.DataFrame:
    """Load the test dataset."""
    import pandas as pd
    if not TEST_DATA_PATH.exists():
        raise FileNotFoundError(f"Test data not found at {TEST_DATA_PATH}. Run T017 first.")
    return pd.read_csv(TEST_DATA_PATH)

def load_model_predictions(model_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load predictions for a specific model.
    Expects a file named {model_name}_predictions.npy or .pickle in the predictions directory.
    Returns (y_true, y_pred).
    """
    import pandas as pd
    # Try to find the prediction file
    # Convention: predictions are saved as {model_name}_predictions.npy
    pred_file = PREDICTIONS_DIR / f"{model_name}_predictions.npy"
    true_file = PREDICTIONS_DIR / f"{model_name}_true.npy" # Or we can just load from test data if IDs match

    if not pred_file.exists():
        raise FileNotFoundError(f"Predictions for {model_name} not found at {pred_file}. Run training/evaluation first.")

    y_pred = np.load(pred_file)
    
    # Load true values. We assume the order matches the test set or is stored.
    # If stored separately:
    if true_file.exists():
        y_true = np.load(true_file)
    else:
        # Fallback: load from test data if we can match IDs, but for simplicity in this pipeline,
        # we assume the prediction file was saved in the same order as the test set split.
        # A more robust way is to save the index.
        df_test = load_test_data()
        # If the prediction file contains only values, we assume order matches df_test
        y_true = df_test['packing_coefficient'].values

    return y_true, y_pred

def load_statistical_results() -> Optional[Dict[str, Any]]:
    """Load the statistical test results if they exist."""
    if STAT_RESULTS_PATH.exists():
        with open(STAT_RESULTS_PATH, 'r') as f:
            return json.load(f)
    return None

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R2, MAE, RMSE."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse)
    }

def main():
    logger.info("Starting T029: Save consolidated metrics summary.")
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Test Data
    try:
        df_test = load_test_data()
        logger.info(f"Loaded test data with {len(df_test)} rows.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    models_to_evaluate = ["random_forest", "gradient_boosting", "mean_baseline"]
    all_metrics = {}
    statistical_summary = {}

    # 2. Evaluate each model
    for model_name in models_to_evaluate:
        logger.info(f"Evaluating {model_name}...")
        try:
            y_true, y_pred = load_model_predictions(model_name)
            metrics = calculate_metrics(y_true, y_pred)
            all_metrics[model_name] = metrics
            logger.info(f"{model_name} R2: {metrics['r2']:.4f}, MAE: {metrics['mae']:.4f}, RMSE: {metrics['rmse']:.4f}")
        except FileNotFoundError as e:
            logger.warning(f"Could not load predictions for {model_name}: {e}. Skipping.")
            all_metrics[model_name] = None

    # 3. Handle Statistical Tests
    # T028 should have produced statistical test results. We try to load them.
    # If not, we re-calculate if we have the predictions.
    stat_results = load_statistical_results()
    
    alpha = 0.05
    n_models = 2 # RF and GB compared to baseline
    alpha_corrected = alpha / n_models

    if stat_results:
        logger.info("Loading statistical test results from file.")
        statistical_summary = stat_results.get("tests", {})
        # Ensure the corrected alpha is recorded in the summary
        statistical_summary["alpha_corrected"] = alpha_corrected
    else:
        logger.info("Statistical results file not found. Attempting to re-calculate if predictions exist.")
        # Re-calculate logic
        if all_metrics.get("random_forest") and all_metrics.get("mean_baseline"):
            # We need the raw predictions for the paired t-test
            _, rf_pred = load_model_predictions("random_forest")
            _, baseline_pred = load_model_predictions("mean_baseline")
            _, y_true = load_model_predictions("random_forest") # True values are same

            # Paired t-test: RF vs Baseline
            t_stat, p_val_rf = paired_t_test(y_true, rf_pred, y_true, baseline_pred)
            
            if all_metrics.get("gradient_boosting"):
                _, gb_pred = load_model_predictions("gradient_boosting")
                t_stat_gb, p_val_gb = paired_t_test(y_true, gb_pred, y_true, baseline_pred)
            else:
                p_val_gb = None

            # Bonferroni correction
            p_values = [p for p in [p_val_rf, p_val_gb] if p is not None]
            corrected_p_values = bonferroni_correct(p_values, n_models)
            
            # Map back
            corrected_map = {}
            idx = 0
            if p_val_rf is not None:
                corrected_map["random_forest_vs_baseline"] = {
                    "p_value": p_val_rf,
                    "corrected_p_value": corrected_p_values[idx],
                    "significant": corrected_p_values[idx] < alpha_corrected
                }
                idx += 1
            if p_val_gb is not None:
                corrected_map["gradient_boosting_vs_baseline"] = {
                    "p_value": p_val_gb,
                    "corrected_p_value": corrected_p_values[idx],
                    "significant": corrected_p_values[idx] < alpha_corrected
                }

            statistical_summary = {
                "alpha": alpha,
                "n_comparisons": n_models,
                "alpha_corrected": alpha_corrected,
                "tests": corrected_map
            }

    # 4. Construct Final Report
    report = {
        "models": all_metrics,
        "statistical_analysis": statistical_summary,
        "metadata": {
            "generated_at": str(pd.Timestamp.now()),
            "test_set_size": len(df_test),
            "alpha": alpha,
            "alpha_corrected": alpha_corrected
        }
    }

    # 5. Save to results/metrics.json
    with open(METRICS_OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Consolidated metrics saved to {METRICS_OUTPUT_PATH}")

if __name__ == "__main__":
    main()