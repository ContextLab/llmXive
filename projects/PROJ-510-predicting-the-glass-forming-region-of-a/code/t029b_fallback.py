"""
Task T029b: Retrain if Needed (with Fallback)

This module implements the logic to detect collinearity in the initial model,
identify the least important feature among collinear pairs, and iteratively
retrain the model excluding that feature until collinearity is resolved or
a maximum number of iterations is reached.

It ensures that a stable model (or best available) is saved for downstream tasks.
"""

import os
import sys
import json
import logging
import shutil
import pickle
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import pearsonr

# Import from local modules
from utils import get_logger, ensure_dir
from features import compute_features

# Constants
CORRELATION_THRESHOLD = 0.8
MAX_ITERATIONS = 3
RANDOM_STATE = 42
DATA_PATH = "data/processed/processed_alloys.csv"
MODEL_PATH = "data/models/random_forest_model.pkl"
STABLE_MODEL_PATH = "data/models/random_forest_model_stable.pkl"
BEST_AVAILABLE_MODEL_PATH = "data/models/random_forest_model_best_available.pkl"
DECISION_LOG_PATH = "data/models/collinearity_decision.json"
INITIAL_METRICS_PATH = "data/models/initial_model_metrics.json"

logger = get_logger(__name__)


def load_initial_model() -> Tuple[Any, pd.DataFrame]:
    """Load the initial model and the processed dataset."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Initial model not found at {MODEL_PATH}. Run training pipeline first.")
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Processed data not found at {DATA_PATH}. Run features.py first.")
    
    df = pd.read_csv(DATA_PATH)
    return model, df


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify feature columns in the dataframe.
    Excludes target and non-feature columns.
    """
    exclude_cols = {'critical_cooling_rate', 'composition', 'glass_forming_label', 'source_label'}
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    return feature_cols


def compute_correlation_matrix(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Compute Pearson correlation matrix for feature columns."""
    return df[feature_cols].corr(method='pearson')


def find_collinear_pairs(correlation_matrix: pd.DataFrame) -> List[Tuple[str, str]]:
    """
    Identify pairs of features with |correlation| > CORRELATION_THRESHOLD.
    Returns a list of tuples (feature1, feature2).
    """
    pairs = []
    features = correlation_matrix.columns
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            f1, f2 = features[i], features[j]
            corr_val = correlation_matrix.loc[f1, f2]
            if abs(corr_val) > CORRELATION_THRESHOLD:
                pairs.append((f1, f2))
    return pairs


def get_shap_importance(model: RandomForestRegressor, feature_names: List[str]) -> Dict[str, float]:
    """
    Compute mean absolute SHAP values for feature importance.
    Since SHAP is expensive and might not be available in all environments,
    we approximate using permutation importance or feature_importances_ from RF.
    For this task, we use feature_importances_ from the Random Forest as a proxy.
    """
    importances = model.feature_importances_
    importance_dict = {name: float(imp) for name, imp in zip(feature_names, importances)}
    return importance_dict


def find_least_important_collinear_feature(
    collinear_pairs: List[Tuple[str, str]], 
    importance_dict: Dict[str, float]
) -> str:
    """
    Among the collinear pairs, find the feature with the lowest mean absolute importance.
    """
    candidate_features = set()
    for f1, f2 in collinear_pairs:
        candidate_features.add(f1)
        candidate_features.add(f2)
    
    if not candidate_features:
        raise ValueError("No candidate features found among collinear pairs.")
    
    # Find the one with minimum importance
    min_feature = min(candidate_features, key=lambda f: importance_dict.get(f, 0.0))
    return min_feature


def train_model_with_features(X: pd.DataFrame, y: pd.Series, feature_subset: List[str]) -> RandomForestRegressor:
    """Train a Random Forest model using only the specified subset of features."""
    X_subset = X[feature_subset]
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    model.fit(X_subset, y)
    return model


def retrain_and_check_collinearity(
    initial_model: RandomForestRegressor,
    df: pd.DataFrame,
    dropped_features: List[str]
) -> Tuple[bool, RandomForestRegressor, str]:
    """
    Retrain model excluding dropped features, then check for remaining collinearity.
    Returns: (is_stable, new_model, dropped_feature_name)
    """
    feature_cols = get_feature_columns(df)
    available_features = [f for f in feature_cols if f not in dropped_features]
    
    if len(available_features) < 2:
        logger.warning("Insufficient features remaining for retraining.")
        return False, initial_model, None
    
    X = df[available_features]
    y = df['critical_cooling_rate']
    
    new_model = train_model_with_features(X, y, available_features)
    
    # Check collinearity on the new feature set
    corr_matrix = compute_correlation_matrix(df, available_features)
    new_pairs = find_collinear_pairs(corr_matrix)
    
    is_stable = len(new_pairs) == 0
    return is_stable, new_model, None


def run_fallback() -> Dict[str, Any]:
    """
    Main execution logic for T029b.
    1. Load initial model and data.
    2. Check for collinearity.
    3. If collinearity exists, iteratively drop least important feature and retrain.
    4. Stop after max iterations or when stable.
    5. Save the resulting model and decision log.
    """
    logger.info("Starting T029b: Collinearity detection and retraining fallback.")
    
    try:
        initial_model, df = load_initial_model()
    except Exception as e:
        logger.error(f"Failed to load initial model or data: {e}")
        return {"status": "failed", "error": str(e)}
    
    feature_cols = get_feature_columns(df)
    corr_matrix = compute_correlation_matrix(df, df)
    collinear_pairs = find_collinear_pairs(corr_matrix)
    
    decision_log = {
        "retrain_required": len(collinear_pairs) > 0,
        "initial_collinear_pairs": [(f1, f2) for f1, f2 in collinear_pairs],
        "dropped_feature": None,
        "iterations": 0,
        "status": "stable" if len(collinear_pairs) == 0 else "processing"
    }
    
    if len(collinear_pairs) == 0:
        logger.info("No collinearity detected. Copying initial model to stable model.")
        ensure_dir(STABLE_MODEL_PATH)
        shutil.copy(MODEL_PATH, STABLE_MODEL_PATH)
        decision_log["status"] = "stable"
        with open(DECISION_LOG_PATH, 'w') as f:
            json.dump(decision_log, f, indent=2)
        return decision_log
    
    # Record initial metrics
    initial_metrics = {
        "model_path": MODEL_PATH,
        "feature_count": len(feature_cols),
        "collinear_pairs_count": len(collinear_pairs)
    }
    with open(INITIAL_METRICS_PATH, 'w') as f:
        json.dump(initial_metrics, f, indent=2)
    
    dropped_features = []
    current_model = initial_model
    iterations = 0
    status = "processing"
    
    while iterations < MAX_ITERATIONS and len(collinear_pairs) > 0:
        logger.info(f"Iteration {iterations + 1}: {len(collinear_pairs)} collinear pairs detected.")
        
        importance_dict = get_shap_importance(current_model, feature_cols)
        feature_to_drop = find_least_important_collinear_feature(collinear_pairs, importance_dict)
        
        logger.info(f"Dropping feature: {feature_to_drop}")
        dropped_features.append(feature_to_drop)
        
        # Retrain with remaining features
        available_features = [f for f in feature_cols if f not in dropped_features]
        if len(available_features) < 2:
            logger.warning("Insufficient features remaining. Stopping retraining.")
            status = "best_available"
            break
        
        X = df[available_features]
        y = df['critical_cooling_rate']
        current_model = train_model_with_features(X, y, available_features)
        
        # Re-check collinearity
        corr_matrix = compute_correlation_matrix(df, available_features)
        collinear_pairs = find_collinear_pairs(corr_matrix)
        
        iterations += 1
        
        if len(collinear_pairs) == 0:
            status = "stable"
            logger.info("Collinearity resolved. Model is stable.")
            break
    
    decision_log["dropped_feature"] = dropped_features[-1] if dropped_features else None
    decision_log["all_dropped_features"] = dropped_features
    decision_log["iterations"] = iterations
    decision_log["status"] = status
    
    # Save the resulting model
    output_model_path = STABLE_MODEL_PATH
    if status == "best_available":
        output_model_path = BEST_AVAILABLE_MODEL_PATH
        logger.warning(f"Stability not fully achieved after {iterations} iterations. Saving as best_available.")
    
    ensure_dir(output_model_path)
    with open(output_model_path, 'wb') as f:
        pickle.dump(current_model, f)
    
    # If status is best_available, also copy to stable path as per T029c requirement
    if status == "best_available":
        ensure_dir(STABLE_MODEL_PATH)
        shutil.copy(BEST_AVAILABLE_MODEL_PATH, STABLE_MODEL_PATH)
        logger.warning(f"Copied best_available model to {STABLE_MODEL_PATH} for downstream compatibility.")
    
    with open(DECISION_LOG_PATH, 'w') as f:
        json.dump(decision_log, f, indent=2)
    
    logger.info(f"T029b completed. Status: {status}. Model saved to {output_model_path}.")
    return decision_log


def main():
    """Entry point for the script."""
    ensure_dir("data/models")
    ensure_dir("data/processed")
    
    result = run_fallback()
    
    if result.get("status") == "failed":
        logger.error(f"Task failed: {result.get('error')}")
        sys.exit(1)
    
    logger.info("Task T029b completed successfully.")


if __name__ == "__main__":
    main()