"""
T023: Train predictive model with Nested CV, Collinearity handling, and RFE.

Implements:
1. Define decline label (drop >= 3 points).
2. Nested CV (Outer K-fold, Inner Grid Search).
3. Inner Loop: Collinearity check (>0.95), Variance Threshold (>0.01), RFE (<=20 features).
4. Grid Search: n_estimators {50, 100, 200}, max_depth {5, 10, None}.
5. Outputs: model.pkl, cv_results.json, model_params.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from sklearn.model_selection import GridSearchCV, KFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

# Import project utilities
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_json, save_pickle
from utils.stats import calculate_correlation_matrix, calculate_feature_variance

# Configuration
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
MODEL_OUTPUT_PATH = Path("data/processed/model.pkl")
CV_RESULTS_PATH = Path("data/processed/cv_results.json")
MODEL_PARAMS_PATH = Path("data/processed/model_params.json")
DECLINE_THRESHOLD = 3
RANDOM_SEED = 42
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01

logger = get_logger("train_model")

class CollinearityTransformer:
    """
    Transformer that removes features with high correlation (> 0.95).
    Keeps the feature with higher variance in the pair.
    """
    def __init__(self, threshold: float = CORRELATION_THRESHOLD):
        self.threshold = threshold
        self.features_to_keep = None
        self.correlation_matrix = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "CollinearityTransformer":
        if X.shape[1] == 0:
            return self

        self.correlation_matrix = calculate_correlation_matrix(X)
        n_features = X.shape[1]
        keep_mask = np.ones(n_features, dtype=bool)
        
        # Simple iterative removal: if corr(i, j) > threshold, remove the one with lower variance
        # To ensure deterministic behavior, we sort indices
        indices = list(range(n_features))
        
        for i in range(n_features):
            if not keep_mask[i]:
                continue
            for j in range(i + 1, n_features):
                if not keep_mask[j]:
                    continue
                
                corr_val = self.correlation_matrix[i, j]
                if abs(corr_val) > self.threshold:
                    # Calculate variance for current subset (or use pre-calculated if available)
                    # Here we compute variance on the fly for simplicity in this transformer
                    var_i = np.var(X[:, i])
                    var_j = np.var(X[:, j])
                    
                    if var_i >= var_j:
                        keep_mask[j] = False
                    else:
                        keep_mask[i] = False
                        break # i is removed, stop checking i
        
        self.features_to_keep = np.where(keep_mask)[0]
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.features_to_keep is None:
            raise RuntimeError("Transformer not fitted.")
        if len(self.features_to_keep) == 0:
            return np.zeros((X.shape[0], 0))
        return X[:, self.features_to_keep]

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        self.fit(X, y)
        return self.transform(X)

def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Loads graph metrics and defines the target label.
    Returns X, y, feature_names.
    """
    if not GRAPH_METRICS_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
    
    df = pd.read_csv(GRAPH_METRICS_PATH)
    
    # Ensure we have the necessary columns for labeling
    # Expected columns from T017/T019: subject_id, mmse_t1, mmse_t2 (or similar)
    # We need to identify the decline.
    # Assuming the CSV has 'subject_id', 'mmse_baseline', 'mmse_followup' or similar.
    # If the specific column names vary, we try to infer or raise a clear error.
    
    # Strategy: Look for columns indicating timepoints or delta
    cols = df.columns.tolist()
    baseline_col = None
    followup_col = None
    
    # Heuristic for column names based on common BIDS/Longitudinal patterns
    for c in cols:
        if 'mmse' in c.lower() or 'moca' in c.lower():
            if 't1' in c.lower() or 'baseline' in c.lower() or 'time1' in c.lower():
                baseline_col = c
            elif 't2' in c.lower() or 'followup' in c.lower() or 'time2' in c.lower():
                followup_col = c
            elif 'delta' in c.lower() or 'change' in c.lower():
                # If delta exists, we might use it directly, but spec says "drop >= 3"
                pass
    
    if not baseline_col or not followup_col:
        # Fallback: assume first two numeric columns that aren't subject_id are scores?
        # Or raise a specific error if we can't find them.
        # Let's try to find any pair of columns that look like scores.
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) >= 2:
            # Assume first two are the scores if we can't find specific names
            baseline_col = numeric_cols[0]
            followup_col = numeric_cols[1]
            logger.log("warning", message=f"Using inferred columns: {baseline_col}, {followup_col}")
        else:
            raise ValueError(f"Could not identify baseline and followup score columns in {cols}")

    # Calculate decline
    # Decline = Baseline - Followup (Positive means drop)
    # Label = 1 if (Baseline - Followup) >= DECLINE_THRESHOLD else 0
    delta = df[baseline_col] - df[followup_col]
    y = (delta >= DECLINE_THRESHOLD).astype(int).values
    
    # Features: All numeric columns except the scores used for labeling and subject_id
    # We need to exclude the score columns from X
    feature_cols = [c for c in df.columns if c not in [baseline_col, followup_col, 'subject_id']]
    # Ensure only numeric features
    feature_cols = [c for c in feature_cols if c in df.select_dtypes(include=[np.number]).columns]
    
    if len(feature_cols) == 0:
        raise ValueError("No features found for modeling.")
    
    X = df[feature_cols].values
    feature_names = feature_cols
    
    logger.log("info", message=f"Loaded {X.shape[0]} subjects, {X.shape[1]} features. Target distribution: {np.bincount(y)}")
    return X, y, feature_names

def train_and_evaluate_nested_cv(
    X: np.ndarray, 
    y: np.ndarray, 
    feature_names: List[str]
) -> Tuple[Any, Dict[str, Any]]:
    """
    Implements Nested Cross-Validation.
    Outer: StratifiedKFold (5 folds)
    Inner: GridSearchCV with Collinearity, Variance, RFE steps.
    """
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    
    # Grid Search Parameters
    param_grid = {
        'randomforestclassifier__n_estimators': [50, 100, 200],
        'randomforestclassifier__max_depth': [5, 10, None]
    }
    
    # Define the pipeline for the inner loop
    # Steps:
    # 1. CollinearityTransformer (Custom)
    # 2. VarianceThreshold
    # 3. RFE (with a base estimator, e.g., RF or LogisticRegression)
    # 4. RandomForestClassifier
    
    # Note: RFE needs an estimator to select features. We use a simple RF for selection.
    base_estimator = RandomForestClassifier(random_state=RANDOM_SEED, n_estimators=10)
    
    # We cannot easily put a custom transformer (CollinearityTransformer) in a sklearn Pipeline 
    # if it's not a sklearn estimator. We wrap it or handle it manually in the inner loop.
    # To keep it clean and compatible with GridSearchCV, we will implement the inner loop 
    # manually to ensure the Collinearity step happens correctly before Variance/RFE.
    
    outer_results = []
    all_fold_metrics = []
    best_params_history = []

    logger.log("info", message="Starting Nested CV...")

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # --- Inner Loop: Feature Selection + Model Training ---
        # We need to find best params using only train data
        
        # 1. Collinearity Check on Train
        collinearity_filter = CollinearityTransformer(threshold=CORRELATION_THRESHOLD)
        X_train_coll = collinearity_filter.fit_transform(X_train)
        
        if X_train_coll.shape[1] == 0:
            logger.log("warning", message=f"Fold {fold_idx}: All features removed by collinearity check.")
            continue

        # 2. Variance Threshold on Collinearity-filtered data
        var_thresh = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
        X_train_var = var_thresh.fit_transform(X_train_coll)
        
        if X_train_var.shape[1] == 0:
            logger.log("warning", message=f"Fold {fold_idx}: All features removed by variance threshold.")
            continue

        # 3. RFE to select <= 20 features
        # We need to map the remaining features back to original names for logging if needed,
        # but for the model, we just use the reduced matrix.
        rfe = RFE(estimator=RandomForestClassifier(random_state=RANDOM_SEED, n_estimators=10), 
                  n_features_to_select=min(MAX_FEATURES, X_train_var.shape[1]))
        X_train_rfe = rfe.fit_transform(X_train_var)
        
        # 4. Grid Search on RFE output
        # We need a classifier.
        rf_clf = RandomForestClassifier(random_state=RANDOM_SEED)
        
        # We use a simple GridSearchCV here
        gs = GridSearchCV(
            estimator=rf_clf,
            param_grid=param_grid,
            cv=3, # Inner CV folds
            scoring='roc_auc',
            n_jobs=2,
            refit=True
        )
        
        gs.fit(X_train_rfe, y_train)
        
        best_params = gs.best_params_
        best_model = gs.best_estimator_
        
        # Evaluate on Test Set
        # Apply the SAME transformations to Test set
        # Note: Collinearity/Var/RFE must be fit on Train, then transform Test
        X_test_coll = collinearity_filter.transform(X_test)
        X_test_var = var_thresh.transform(X_test_coll)
        X_test_rfe = rfe.transform(X_test_var)
        
        if X_test_rfe.shape[1] == 0:
            logger.log("warning", message=f"Fold {fold_idx}: Test set has no features after selection.")
            continue

        y_pred = best_model.predict(X_test_rfe)
        y_proba = best_model.predict_proba(X_test_rfe)
        
        # Metrics
        try:
            auc = roc_auc_score(y_test, y_proba[:, 1])
        except ValueError:
            auc = 0.0 # Handle edge cases
        
        f1 = f1_score(y_test, y_pred)
        acc = accuracy_score(y_test, y_pred)
        
        outer_results.append({
            "fold": fold_idx,
            "auc": auc,
            "f1": f1,
            "accuracy": acc,
            "n_features_selected": X_test_rfe.shape[1],
            "best_params": best_params
        })
        
        all_fold_metrics.append({
            "auc": auc,
            "f1": f1,
            "accuracy": acc
        })
        best_params_history.append(best_params)

    # Aggregate results
    mean_auc = np.mean([r["auc"] for r in outer_results])
    mean_f1 = np.mean([r["f1"] for r in outer_results])
    mean_acc = np.mean([r["accuracy"] for r in outer_results])
    
    cv_results = {
        "mean_auc": float(mean_auc),
        "mean_f1": float(mean_f1),
        "mean_accuracy": float(mean_acc),
        "folds": outer_results,
        "total_folds": len(outer_results)
    }
    
    # Determine final model params (most frequent or best mean)
    # For simplicity, we take the params from the fold with highest AUC
    best_fold = max(outer_results, key=lambda x: x["auc"])
    final_params = best_fold["best_params"]
    
    # Train Final Model on ALL data with best params
    logger.log("info", message=f"Training final model on full data with params: {final_params}")
    
    # Re-run the full pipeline on full data
    coll_full = CollinearityTransformer(threshold=CORRELATION_THRESHOLD)
    X_coll = coll_full.fit_transform(X)
    
    var_full = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_var = var_full.fit_transform(X_coll)
    
    n_select = min(MAX_FEATURES, X_var.shape[1])
    rfe_full = RFE(estimator=RandomForestClassifier(random_state=RANDOM_SEED, n_estimators=10), 
                   n_features_to_select=n_select)
    X_rfe = rfe_full.fit_transform(X_var)
    
    final_clf = RandomForestClassifier(
        random_state=RANDOM_SEED,
        n_estimators=final_params.get('randomforestclassifier__n_estimators', 100),
        max_depth=final_params.get('randomforestclassifier__max_depth', None)
    )
    final_clf.fit(X_rfe, y)
    
    # Store the full pipeline for persistence
    # We need to store the transformers and the final classifier
    final_model = {
        "collinearity": coll_full,
        "variance": var_full,
        "rfe": rfe_full,
        "classifier": final_clf,
        "feature_names": feature_names,
        "params": final_params
    }
    
    return final_model, cv_results

def persist_model(model: Any, path: Path) -> None:
    """Saves the model pipeline to disk."""
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.log("info", message=f"Model saved to {path}")

def write_cv_results(results: Dict[str, Any], path: Path) -> None:
    """Saves CV results to JSON."""
    ensure_dir(path)
    save_json(results, str(path))
    logger.log("info", message=f"CV results saved to {path}")

def write_model_params(params: Dict[str, Any], path: Path) -> None:
    """Saves final model parameters to JSON."""
    ensure_dir(path)
    save_json(params, str(path))
    logger.log("info", message=f"Model params saved to {path}")

@log_operation("train_model")
def main() -> int:
    """Main entry point."""
    start_time = time.time()
    try:
        # 1. Load Data
        X, y, feature_names = load_features()
        
        # 2. Check for class imbalance or insufficient data
        if len(y) < 10:
            logger.log("error", message="Insufficient data for training (n < 10).")
            return 1
        
        # 3. Train Model
        final_model, cv_results = train_and_evaluate_nested_cv(X, y, feature_names)
        
        # 4. Persist Artifacts
        persist_model(final_model, MODEL_OUTPUT_PATH)
        write_cv_results(cv_results, CV_RESULTS_PATH)
        
        # Extract final params for the specific JSON file
        model_params = {
            "best_params": final_model["params"],
            "n_features_used": final_model["rfe"].n_features_to_select,
            "decline_threshold": DECLINE_THRESHOLD,
            "random_seed": RANDOM_SEED
        }
        write_model_params(model_params, MODEL_PARAMS_PATH)
        
        elapsed = time.time() - start_time
        logger.log("info", message=f"Training completed in {elapsed:.2f}s")
        
        # Print summary to stdout
        print(f"Model Training Complete. AUC: {cv_results['mean_auc']:.4f}, F1: {cv_results['mean_f1']:.4f}")
        
        return 0
        
    except Exception as e:
        logger.log("error", message=str(e))
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())