from __future__ import annotations

import json
import os
import sys
import time
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from scipy.stats import pearsonr
from joblib import Parallel, delayed

# Local imports matching the provided API surface
from utils.logger import get_logger, log_operation
from utils.stats import check_collinearity, calculate_correlation_matrix, calculate_feature_variance

# Constants
DECLINE_THRESHOLD = 3  # Drop of >= 3 points defines decline
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01
RANDOM_SEED = 42
OUTPUT_MODEL_PATH = Path("data/processed/model.pkl")
OUTPUT_CV_RESULTS_PATH = Path("data/processed/cv_results.json")
OUTPUT_MODEL_PARAMS_PATH = Path("data/processed/model_params.json")
INPUT_FEATURES_PATH = Path("data/processed/graph_metrics.csv")
INPUT_ELIGIBLE_PATH = Path("data/processed/eligible_subjects.csv")

logger = get_logger("train_model")


def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load features and labels from the processed graph metrics CSV.
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Label vector (n_samples,) - 1 if decline >= 3, else 0
        feature_names: List of feature column names
    """
    if not INPUT_FEATURES_PATH.exists():
        logger.log("error", message=f"Input file not found: {INPUT_FEATURES_PATH}")
        raise FileNotFoundError(f"Input file not found: {INPUT_FEATURES_PATH}")

    df = pd.read_csv(INPUT_FEATURES_PATH)

    # Ensure we have the necessary columns.
    # The schema requires a 'subject_id' and the graph metrics.
    # We assume the label needs to be derived or is present.
    # Based on T017/T019 context, we expect 'subject_id', 'mmse_t1', 'mmse_t2', etc.
    # However, the task says "Define decline label (drop >= 3 points)".
    # We must calculate y based on the data.

    # Check for required score columns. If they exist, compute y.
    # If y is already computed in the CSV, use it.
    if "declined" in df.columns:
        y = df["declined"].values
    elif "mmse_t1" in df.columns and "mmse_t2" in df.columns:
        # Calculate decline
        diff = df["mmse_t1"].values - df["mmse_t2"].values
        y = (diff >= DECLINE_THRESHOLD).astype(int).values
    else:
        # Fallback: try to find any score column pair or fail
        logger.log("error", message="Could not find MMSE/MOCA columns to compute decline label.")
        raise ValueError("Missing score columns to compute decline label.")

    # Identify feature columns (exclude subject_id and score columns if present)
    exclude_cols = ["subject_id", "mmse_t1", "mmse_t2", "moca_t1", "moca_t2", "declined"]
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    if not feature_cols:
        logger.log("error", message="No feature columns found in input data.")
        raise ValueError("No feature columns found.")

    X = df[feature_cols].values
    feature_names = feature_cols

    logger.log("info", operation="load_features", rows=len(X), features=len(feature_names))
    return X, y, feature_names


class CollinearityTransformer:
    """
    Transformer that removes highly correlated features (> 0.95).
    Keeps the feature with higher variance.
    Must be fit and transform.
    """
    def __init__(self, threshold: float = CORRELATION_THRESHOLD):
        self.threshold = threshold
        self.keep_indices_ = None
        self.feature_names_in_ = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        if X.shape[0] < 2:
            self.keep_indices_ = np.arange(X.shape[1])
            return self

        corr_matrix = calculate_correlation_matrix(X)
        n_features = X.shape[1]
        mask = np.ones(n_features, dtype=bool)

        # Iterate to remove collinear pairs
        # Simple greedy approach: if corr(i, j) > threshold, drop the one with lower variance
        for i in range(n_features):
            if not mask[i]:
                continue
            for j in range(i + 1, n_features):
                if not mask[j]:
                    continue
                if abs(corr_matrix[i, j]) > self.threshold:
                    # Calculate variance
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    if var_i >= var_j:
                        mask[j] = False
                    else:
                        mask[i] = False
                        break # i is dropped, move to next i

        self.keep_indices_ = np.where(mask)[0]
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.keep_indices_ is None:
            raise RuntimeError("Transformer not fitted.")
        return X[:, self.keep_indices_]

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        self.fit(X, y)
        return self.transform(X)


def train_and_evaluate_nested_cv(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str]
) -> Tuple[Any, Dict[str, Any], Dict[str, Any]]:
    """
    Implements Nested Cross-Validation.
    Outer: K-fold (Stratified)
    Inner: Grid Search with Feature Selection (Collinearity -> Variance -> RFE)
    """
    logger.log("start", operation="nested_cv", n_samples=X.shape[0], n_features=X.shape[1])

    # Outer CV
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    # Inner CV for Grid Search
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)

    # Pipeline: Collinearity -> Variance Threshold -> RFE -> RF
    # Note: RFE is expensive, so we limit features first.
    pipe = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=CORRELATION_THRESHOLD)),
        ('variance', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), n_features_to_select=MAX_FEATURES)),
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])

    # Grid Search Parameters
    param_grid = {
        'clf__n_estimators': [50, 100, 200],
        'clf__max_depth': [5, 10, None]
    }

    grid_search = GridSearchCV(
        pipe,
        param_grid,
        cv=inner_cv,
        scoring='roc_auc',
        n_jobs=2, # Use 2 cores as per constraints
        refit=True
    )

    outer_scores = []
    cv_results_list = []
    best_params_list = []

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Fit grid search on inner train
        grid_search.fit(X_train, y_train)
        
        # Evaluate on outer test
        y_pred_proba = grid_search.predict_proba(X_test)[:, 1]
        try:
            auc = roc_auc_score(y_test, y_pred_proba)
            outer_scores.append(auc)
        except ValueError:
            # Handle cases where only one class exists in test fold
            outer_scores.append(0.5) 

        # Record results for this fold
        fold_results = {
            "fold": fold_idx,
            "outer_auc": outer_scores[-1],
            "best_params": grid_search.best_params_,
            "cv_mean_score": grid_search.best_score_
        }
        cv_results_list.append(fold_results)
        best_params_list.append(grid_search.best_params_)

    # Aggregate results
    mean_auc = np.mean(outer_scores)
    std_auc = np.std(outer_scores)
    
    # Select the most frequent best params or average them?
    # We'll pick the one from the fold with highest AUC as the "final" model params
    best_fold_idx = np.argmax(outer_scores)
    final_params = best_params_list[best_fold_idx]

    logger.log("complete", operation="nested_cv", mean_auc=mean_auc, std_auc=std_auc)

    # Train final model on FULL data using the best params found (or re-run grid on full data?)
    # Standard practice: Retrain best estimator on full data with best params
    final_model = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=CORRELATION_THRESHOLD)),
        ('variance', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=RandomForestClassifier(n_estimators=10, random_state=RANDOM_SEED), n_features_to_select=MAX_FEATURES)),
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(random_state=RANDOM_SEED))
    ])
    
    # Set params manually
    final_model.set_params(**final_params)
    final_model.fit(X, y)

    return final_model, cv_results_list, final_params


def persist_model(model: Any, path: Path):
    """Save the trained model to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.log("info", operation="persist_model", path=str(path))


def write_cv_results(results: List[Dict[str, Any]], path: Path):
    """Write CV results to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.log("info", operation="write_cv_results", path=str(path))


def write_model_params(params: Dict[str, Any], path: Path):
    """Write model parameters to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.log("info", operation="write_model_params", path=str(path))


@log_operation("train_model_main")
def main():
    start_time = time.time()
    try:
        # 1. Load Data
        X, y, feature_names = load_features()
        
        # 2. Train Model with Nested CV
        model, cv_results, final_params = train_and_evaluate_nested_cv(X, y, feature_names)
        
        # 3. Persist Artifacts
        persist_model(model, OUTPUT_MODEL_PATH)
        write_cv_results(cv_results, OUTPUT_CV_RESULTS_PATH)
        write_model_params(final_params, OUTPUT_MODEL_PARAMS_PATH)
        
        elapsed = time.time() - start_time
        logger.log("success", operation="main", elapsed_seconds=elapsed)
        print(f"Training complete. AUC: {np.mean([r['outer_auc'] for r in cv_results]):.3f}")
        
    except Exception as e:
        logger.log("error", operation="main", error=str(e))
        raise


if __name__ == "__main__":
    main()