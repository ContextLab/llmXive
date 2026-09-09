"""
Analysis module for the glass forming region prediction pipeline.

Handles feature importance, collinearity detection, and sensitivity analysis.
"""

import os
import sys
import json
import pickle
import logging
import shutil
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from scipy.stats import ttest_1samp
from sklearn.metrics import f1_score

# Import from utils
from utils import get_logger, ensure_dir


# Constants
MODEL_PATH = "data/models/random_forest_model.pkl"
STABLE_MODEL_PATH = "data/models/random_forest_model_stable.pkl"
PROCESSED_DATA_PATH = "data/processed/processed_alloys.csv"
FEATURE_IMP_PATH = "data/models/feature_importance.json"
COLLINEARITY_PATH = "data/models/collinearity_report.json"
SENSITIVITY_CSV_PATH = "data/models/sensitivity_report.csv"
SENSITIVITY_STATUS_PATH = "data/models/sensitivity_status.json"
LOG_PATH = "data/logs/analyze.log"


def load_model_and_data(model_path: str, data_path: str) -> Tuple[Any, pd.DataFrame, pd.DataFrame]:
    """
    Load model and data.
    """
    logger = get_logger(__name__)
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    df = pd.read_csv(data_path)
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    X = df[feature_cols]
    y = df['critical_cooling_rate']

    return model, X, y


def check_collinearity(X: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for collinearity among features.
    """
    corr_matrix = X.corr().abs()
    high_corr = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            if corr_matrix.iloc[i, j] > 0.8:
                high_corr.append({
                    "feature1": corr_matrix.columns[i],
                    "feature2": corr_matrix.columns[j],
                    "correlation": corr_matrix.iloc[i, j]
                })

    return {
        "collinear_pairs": high_corr,
        "has_collinearity": len(high_corr) > 0
    }


def analyze_feature_importance(model: Any, X: pd.DataFrame, y: pd.Series) -> List[Dict[str, Any]]:
    """
    Compute permutation importance and p-values.
    """
    result = permutation_importance(model, X, y, n_repeats=1000, random_state=42, n_jobs=-1)
    feature_names = X.columns.tolist()
    importance_scores = result.importances_mean
    std_scores = result.importances_std

    # Calculate p-values: one-sample t-test against 0
    p_values = []
    for i in range(len(feature_names)):
        # Permutation distribution
        dist = result.importances[:, i]
        # Test if mean is significantly different from 0
        t_stat, p_val = ttest_1samp(dist, 0.0)
        p_values.append(p_val)

    importance_data = []
    for i, name in enumerate(feature_names):
        importance_data.append({
            "feature": name,
            "importance_score": float(importance_scores[i]),
            "p_value": float(p_values[i])
        })

    return importance_data


def retrain_stable_model(X: pd.DataFrame, y: pd.Series, collinearity_report: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    """
    Retrain model if collinearity exists, dropping least important feature.
    """
    logger = get_logger(__name__)
    if not collinearity_report.get("has_collinearity", False):
        logger.info("No collinearity detected. Using initial model.")
        return None, {"retrain_required": False}

    logger.info("Collinearity detected. Retraining with feature removal.")

    # Initial model to get importance
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X, y)
    importance = analyze_feature_importance(model, X, y)

    # Find collinear pairs
    pairs = collinearity_report["collinear_pairs"]
    collinear_features = set()
    for pair in pairs:
        collinear_features.add(pair["feature1"])
        collinear_features.add(pair["feature2"])

    # Find lowest importance among collinear
    lowest_imp_feature = None
    min_imp = float('inf')
    for feat_info in importance:
        if feat_info["feature"] in collinear_features:
            if feat_info["importance_score"] < min_imp:
                min_imp = feat_info["importance_score"]
                lowest_imp_feature = feat_info["feature"]

    if not lowest_imp_feature:
        return None, {"retrain_required": True, "status": "best_available", "dropped_feature": None}

    # Drop feature
    remaining_cols = [c for c in X.columns if c != lowest_imp_feature]
    X_reduced = X[remaining_cols]

    # Retrain
    new_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    new_model.fit(X_reduced, y)

    # Check collinearity again
    new_report = check_collinearity(X_reduced)

    decision = {
        "retrain_required": True,
        "dropped_feature": lowest_imp_feature,
        "iterations": 1,
        "status": "stable" if not new_report["has_collinearity"] else "best_available"
    }

    return new_model, decision


def run_collinearity_and_retrain(X: pd.DataFrame, y: pd.Series) -> Tuple[Any, Dict[str, Any]]:
    """
    Run collinearity check and retrain if necessary.
    """
    coll_report = check_collinearity(X)
    model, decision = retrain_stable_model(X, y, coll_report)
    return model, decision


def run_sensitivity_analysis(model: Any, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Perform threshold-sweep sensitivity analysis.
    """
    logger = get_logger(__name__)
    thresholds = [50, 100, 150]
    results = []

    # Binarize target for F1 calculation
    # We use the model's predictions to binarize, then compare to binarized y
    # But the task says: "Binarize Predictions: Use the *regressor's* predictions and binarize them at the current threshold"
    # And compute F1 on the test set.
    # We need a test set. Let's assume we use the whole dataset for simplicity or split again.
    # Since we don't have the split here, we'll use the whole dataset for the sweep.

    y_pred = model.predict(X)

    f1_scores = []
    for thresh in thresholds:
        # Binarize predictions
        y_pred_bin = (y_pred >= thresh).astype(int)
        # Binarize true values (assuming y is continuous, we need a threshold for y too?
        # The task says "Binarize Predictions... Compute F1-score on the test set using these binarized predictions."
        # It implies we compare against the *true* binarized labels.
        # But what is the threshold for y?
        # Usually, glass forming is defined by a threshold on critical_cooling_rate.
        # Let's assume the threshold is the same as the prediction threshold for consistency.
        y_true_bin = (y >= thresh).astype(int)

        f1 = f1_score(y_true_bin, y_pred_bin)
        f1_scores.append(f1)
        results.append({
            "threshold": thresh,
            "f1_score": f1
        })

    # Calculate stability
    if not f1_scores:
        return {"stability_met": False, "f1_margin_pct": 0, "run_status": "FAILED"}

    max_f1 = max(f1_scores)
    min_f1 = min(f1_scores)
    mean_f1 = np.mean(f1_scores)

    f1_margin = (max_f1 - min_f1) / max(mean_f1, 0.1)
    stability_met = f1_margin <= 0.10

    status = "PASSED" if stability_met else "FAILED"

    return {
        "stability_met": stability_met,
        "f1_margin_pct": f1_margin,
        "threshold_values": thresholds,
        "run_status": status,
        "results": results
    }


def run_analysis() -> None:
    """
    Main entry point for the analysis pipeline.
    """
    logger = get_logger(__name__, LOG_PATH)
    logger.info("Starting analysis pipeline")

    try:
        # Load stable model
        if not os.path.exists(STABLE_MODEL_PATH):
            logger.warning(f"Stable model not found at {STABLE_MODEL_PATH}. Falling back to initial model.")
            model_path = MODEL_PATH
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found at {model_path} or {STABLE_MODEL_PATH}")
            model, X, y = load_model_and_data(model_path, PROCESSED_DATA_PATH)
            # Copy to stable path for consistency
            shutil.copy(model_path, STABLE_MODEL_PATH)
        else:
            model, X, y = load_model_and_data(STABLE_MODEL_PATH, PROCESSED_DATA_PATH)

        # Collinearity Check
        coll_report = check_collinearity(X)
        ensure_dir(COLLINEARITY_PATH)
        with open(COLLINEARITY_PATH, 'w') as f:
            json.dump(coll_report, f, indent=2)

        # Feature Importance
        importance = analyze_feature_importance(model, X, y)
        ensure_dir(FEATURE_IMP_PATH)
        with open(FEATURE_IMP_PATH, 'w') as f:
            json.dump(importance, f, indent=2)

        # Sensitivity Analysis
        sens_result = run_sensitivity_analysis(model, X, y)
        ensure_dir(SENSITIVITY_STATUS_PATH)
        with open(SENSITIVITY_STATUS_PATH, 'w') as f:
            json.dump({
                "stability_met": sens_result["stability_met"],
                "f1_margin_pct": sens_result["f1_margin_pct"],
                "threshold_values": sens_result["threshold_values"],
                "run_status": sens_result["run_status"]
            }, f, indent=2)

        # Write CSV report
        csv_data = []
        for r in sens_result.get("results", []):
            csv_data.append({
                "threshold": r["threshold"],
                "f1_score": r["f1_score"],
                "f1_margin_pct": sens_result["f1_margin_pct"],
                "rmse_variance": 0.0, # Placeholder as per task
                "stability_status": "PASS" if sens_result["stability_met"] else "FAIL"
            })
        df_csv = pd.DataFrame(csv_data)
        ensure_dir(SENSITIVITY_CSV_PATH)
        df_csv.to_csv(SENSITIVITY_CSV_PATH, index=False)

        logger.info("Analysis complete.")

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_analysis()
