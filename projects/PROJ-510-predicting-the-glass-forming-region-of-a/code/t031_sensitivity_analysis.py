"""
Task T031: Threshold-Sweep Sensitivity Analysis

Performs a sensitivity analysis on the stable Random Forest model by:
1. Evaluating regression RMSE (constant across thresholds).
2. Sweeping classification thresholds (50, 100, 150 K/s) on the binary target.
3. Training a new RandomForestClassifier for each threshold.
4. Calculating F1 stability margin.
5. Writing results to data/processed/sensitivity_report.csv and data/models/sensitivity_status.json.
"""
import os
import sys
import json
import logging
import pickle
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, mean_squared_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(DATA_DIR, "models")

STABLE_MODEL_PATH = os.path.join(MODELS_DIR, "random_forest_model_stable.pkl")
PROCESSED_DATA_PATH = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
SENSITIVITY_REPORT_PATH = os.path.join(PROCESSED_DIR, "sensitivity_report.csv")
SENSITIVITY_STATUS_PATH = os.path.join(MODELS_DIR, "sensitivity_status.json")

THRESHOLDS = [50, 100, 150]
RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_stable_model(model_path: str) -> Any:
    """Load the stable Random Forest model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Stable model not found at {model_path}. "
                                "Run T029a/T029b to generate random_forest_model_stable.pkl.")
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load the processed alloy dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                "Run ingestion.py and features.py first.")
    return pd.read_csv(data_path)


def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix X and target vector y.
    Assumes the DataFrame contains the engineered thermodynamic features.
    """
    # Identify feature columns (exclude target and non-feature columns)
    exclude_cols = ['composition', 'critical_cooling_rate', 'source_label', 'is_synthetic']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in processed data. "
                         "Ensure thermodynamic features (mixing_enthalpy, etc.) are present.")

    X = df[feature_cols].values
    y = df['critical_cooling_rate'].values
    
    return X, y, feature_cols


def run_regression_rmse(model: Any, X: np.ndarray, y: np.ndarray) -> float:
    """Compute RMSE for the regression task (constant across thresholds)."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    # The model is already trained, so we just predict on the test split
    # Note: In a real pipeline, we'd re-split to ensure consistency with training, 
    # but here we assume the model was trained on a split consistent with this logic.
    # To be strictly correct with the task description "Compute RMSE on the continuous target",
    # we evaluate the existing model on a fresh split of the data.
    
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    return rmse


def run_classification_sweep(
    X: np.ndarray, 
    y: np.ndarray, 
    thresholds: List[int]
) -> List[Dict[str, Any]]:
    """
    Train a RandomForestClassifier for each threshold and compute F1 scores.
    """
    results = []
    
    # Define the train-test split once for consistency across thresholds
    X_train, X_test, y_train_full, y_test_full = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    for threshold in thresholds:
        # Binarize target
        y_train_bin = (y_train_full >= threshold).astype(int)
        y_test_bin = (y_test_full >= threshold).astype(int)

        # Check for class imbalance that might make F1 undefined (e.g., all 0s in test)
        if len(np.unique(y_test_bin)) < 2:
            logger.warning(f"Threshold {threshold}: Test set has only one class. F1 undefined. Skipping.")
            results.append({
                "threshold": threshold,
                "f1_score": None,
                "reason": "single_class_test"
            })
            continue

        # Train classifier
        clf = RandomForestClassifier(
            n_estimators=100, 
            random_state=RANDOM_STATE, 
            n_jobs=-1
        )
        clf.fit(X_train, y_train_bin)

        # Predict and evaluate
        y_pred_bin = clf.predict(X_test)
        f1 = f1_score(y_test_bin, y_pred_bin, zero_division=0)

        results.append({
            "threshold": threshold,
            "f1_score": f1,
            "reason": "success"
        })

    return results


def calculate_stability(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate F1 stability margin and determine pass/fail status.
    """
    valid_scores = [r["f1_score"] for r in results if r["f1_score"] is not None]
    
    if len(valid_scores) < 2:
        logger.warning("Insufficient valid F1 scores to calculate stability.")
        return {
            "stability_met": False,
            "f1_margin_pct": None,
            "threshold_values": THRESHOLDS,
            "run_status": "FAILED",
            "reason": "insufficient_valid_scores"
        }

    max_f1 = max(valid_scores)
    min_f1 = min(valid_scores)
    mean_f1 = np.mean(valid_scores)

    # Prevent division by zero if mean is 0 (unlikely for F1, but safe)
    if mean_f1 == 0:
        margin_pct = 0.0 if max_f1 == 0 else float('inf')
    else:
        margin_pct = (max_f1 - min_f1) / mean_f1

    stability_met = margin_pct <= 0.10
    status = "PASSED" if stability_met else "FAILED"

    return {
        "stability_met": stability_met,
        "f1_margin_pct": float(margin_pct),
        "threshold_values": THRESHOLDS,
        "run_status": status
    }


def write_outputs(
    regression_rmse: float,
    classification_results: List[Dict[str, Any]],
    stability_info: Dict[str, Any]
):
    """Write the sensitivity report CSV and status JSON."""
    # Prepare CSV data
    csv_data = []
    for res in classification_results:
        if res["f1_score"] is not None:
            # Calculate margin for the row (same as global margin)
            margin = stability_info["f1_margin_pct"]
            status = "PASS" if stability_info["stability_met"] else "FAIL"
            csv_data.append({
                "threshold": res["threshold"],
                "f1_score": res["f1_score"],
                "f1_margin_pct": margin,
                "stability_status": status
            })
        else:
            csv_data.append({
                "threshold": res["threshold"],
                "f1_score": np.nan,
                "f1_margin_pct": np.nan,
                "stability_status": "SKIP"
            })

    df_report = pd.DataFrame(csv_data)
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(SENSITIVITY_REPORT_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(SENSITIVITY_STATUS_PATH), exist_ok=True)

    df_report.to_csv(SENSITIVITY_REPORT_PATH, index=False)
    logger.info(f"Wrote sensitivity report to {SENSITIVITY_REPORT_PATH}")

    # Write status JSON
    with open(SENSITIVITY_STATUS_PATH, 'w') as f:
        json.dump(stability_info, f, indent=2)
    logger.info(f"Wrote sensitivity status to {SENSITIVITY_STATUS_PATH}")


def run_sensitivity_analysis():
    """Main entry point for T031."""
    logger.info("Starting Threshold-Sweep Sensitivity Analysis (T031)")

    # 1. Load Data
    logger.info(f"Loading stable model from {STABLE_MODEL_PATH}")
    model = load_stable_model(STABLE_MODEL_PATH)

    logger.info(f"Loading processed data from {PROCESSED_DATA_PATH}")
    df = load_processed_data(PROCESSED_DATA_PATH)

    # 2. Prepare Features
    X, y, feature_cols = prepare_features(df)
    logger.info(f"Prepared {len(feature_cols)} features from {len(X)} samples")

    # 3. Regression Metric (Constant)
    logger.info("Computing Regression RMSE...")
    rmse = run_regression_rmse(model, X, y)
    logger.info(f"Regression RMSE (constant): {rmse:.4f}")

    # 4. Classification F1 Stability Sweep
    logger.info(f"Running classification sweep for thresholds: {THRESHOLDS}")
    classification_results = run_classification_sweep(X, y, THRESHOLDS)

    # 5. Calculate Metrics
    logger.info("Calculating stability metrics...")
    stability_info = calculate_stability(classification_results)

    # 6. Write Outputs
    write_outputs(rmse, classification_results, stability_info)

    # Summary
    logger.info("Sensitivity Analysis Complete.")
    logger.info(f"  Stability Met: {stability_info['stability_met']}")
    logger.info(f"  F1 Margin %: {stability_info['f1_margin_pct']}")
    logger.info(f"  Run Status: {stability_info['run_status']}")

    return stability_info


def main():
    """Entry point for script execution."""
    try:
        run_sensitivity_analysis()
        logger.info("T031 completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"T031 failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()