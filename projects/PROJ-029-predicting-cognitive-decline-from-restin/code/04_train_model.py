"""
code/04_train_model.py
Implements nested cross-validation with feature selection (collinearity, variance, RFE)
and Random Forest training to predict cognitive decline.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import VarianceThreshold, RFE, SelectFromModel
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from config import get_config, apply_random_seed
from utils.logger import get_logger, log_operation
from utils.stats import calculate_correlation_matrix, calculate_feature_variance

# Constants
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")
MODEL_PATH = Path("data/processed/model.pkl")
PERFORMANCE_REPORT_PATH = Path("data/processed/performance_report.json")
LOG_PATH = Path("data/artifacts/training_log.json")

# Grid Search Parameters (Corrected from spec typo)
# Spec listed {5, 10, None} for n_estimators (likely typo), {50, 100, 200} for max_depth (likely typo).
# Standard RF ranges: n_estimators in {50, 100, 200}, max_depth in {5, 10, None}
PARAM_GRID = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, None]
}

logger = get_logger("train_model")

class CollinearityTransformer(BaseEstimator, TransformerMixin):
    """
    Removes features with Pearson correlation > 0.95 on the training fold.
    Keeps the feature with higher variance.
    """
    def __init__(self, threshold=0.95):
        self.threshold = threshold
        self.mask_ = None

    def fit(self, X, y=None):
        corr_matrix = calculate_correlation_matrix(X)
        # Upper triangle only to avoid duplicate pairs
        upper = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        corr_upper = corr_matrix.where(upper)
        
        # Find pairs with correlation > threshold
        high_corr_pairs = np.abs(corr_upper) > self.threshold
        
        # Identify features to drop: for each pair, drop the one with lower variance
        variance = calculate_feature_variance(X)
        to_drop = set()
        
        rows, cols = np.where(high_corr_pairs)
        for r, c in zip(rows, cols):
            if variance[r] < variance[c]:
                to_drop.add(r)
            else:
                to_drop.add(c)
        
        self.mask_ = np.array([i not in to_drop for i in range(X.shape[1])])
        return self

    def transform(self, X):
        if self.mask_ is None:
            raise ValueError("CollinearityTransformer must be fitted before transform.")
        return X[:, self.mask_]

def load_eligible_subjects() -> List[str]:
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        logger.error(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        sys.exit(1)
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    return df['subject_id'].tolist()

def load_features(subject_ids: List[str]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Loads graph metrics and defines decline label.
    Returns X (features), y (labels), feature_names.
    """
    if not GRAPH_METRICS_PATH.exists():
        logger.error(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
        sys.exit(1)
    
    df = pd.read_csv(GRAPH_METRICS_PATH)
    
    # Filter for eligible subjects
    df = df[df['subject_id'].isin(subject_ids)]
    
    if df.empty:
        logger.error("No eligible subjects found in graph metrics.")
        sys.exit(1)
    
    # Define decline label: drop >= 3 points
    # Assuming columns 'mmse_t1', 'mmse_t2' or similar exist
    # If MOCA is used, logic adapts. Spec says "MMSE/MOCA scores exist".
    # We assume 'mmse_t1' and 'mmse_t2' are present based on typical BIDS longitudinal data.
    if 'mmse_t1' in df.columns and 'mmse_t2' in df.columns:
        df['decline'] = (df['mmse_t1'] - df['mmse_t2']) >= 3
    elif 'moca_t1' in df.columns and 'moca_t2' in df.columns:
        df['decline'] = (df['moca_t1'] - df['moca_t2']) >= 3
    else:
        logger.error("Could not find MMSE or MOCA score columns for decline definition.")
        sys.exit(1)

    feature_cols = [c for c in df.columns if c not in ['subject_id', 'decline']]
    X = df[feature_cols].values
    y = df['decline'].astype(int).values
    
    return X, y, feature_cols

def define_decline_label(df: pd.DataFrame) -> pd.Series:
    """Helper to define label if needed externally."""
    if 'mmse_t1' in df.columns and 'mmse_t2' in df.columns:
        return (df['mmse_t1'] - df['mmse_t2']) >= 3
    return (df['moca_t1'] - df['moca_t2']) >= 3

def make_inner_pipeline() -> Pipeline:
    """
    Constructs the inner pipeline:
    1. CollinearityTransformer (Pearson > 0.95)
    2. VarianceThreshold (> 0.01)
    3. RFE (Select <= 20 features)
    4. RandomForestClassifier
    """
    # Step 1: Collinearity
    collinearity_step = CollinearityTransformer(threshold=0.95)
    
    # Step 2: Variance Threshold
    var_step = VarianceThreshold(threshold=0.01)
    
    # Step 3: RFE with a dummy RF to select <= 20 features
    # We use a base estimator for RFE
    base_rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rfe_step = RFE(estimator=base_rf, n_features_to_select=20)
    
    # Step 4: Final Model (will be overridden by GridSearchCV estimator)
    # The pipeline ends with the estimator we pass to GridSearchCV
    
    # We build a pipeline that ends with a placeholder, but GridSearchCV replaces it.
    # Actually, GridSearchCV wraps the estimator. So we pass the pipeline (without RF) to GridSearchCV?
    # No, GridSearchCV takes an estimator. We need the feature selection steps inside the estimator.
    # So we create a pipeline: [Collinearity, Variance, RFE, RF]
    # And we tune the RF params.
    
    pipeline = Pipeline([
        ('collinearity', collinearity_step),
        ('variance', var_step),
        ('rfe', rfe_step),
        ('classifier', RandomForestClassifier(random_state=42))
    ])
    
    return pipeline

def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Runs nested cross-validation.
    Outer: StratifiedKFold (n_splits=5)
    Inner: GridSearchCV with the pipeline
    """
    config = get_config()
    apply_random_seed(config.get('random_seed', 42))
    
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Inner pipeline
    inner_pipeline = make_inner_pipeline()
    
    # Grid Search
    grid_search = GridSearchCV(
        inner_pipeline,
        PARAM_GRID,
        cv=3,
        scoring='roc_auc',
        n_jobs=2,
        refit=True
    )
    
    outer_scores = []
    fold_results = []
    
    logger.info("Starting nested cross-validation...")
    start_time = time.time()
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Fit GridSearch on training fold
        grid_search.fit(X_train, y_train)
        
        # Evaluate on test fold
        y_pred_proba = grid_search.predict_proba(X_test)[:, 1]
        y_pred = grid_search.predict(X_test)
        
        auc = roc_auc_score(y_test, y_pred_proba)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        outer_scores.append(auc)
        
        fold_results.append({
            "fold": fold_idx + 1,
            "auc": auc,
            "accuracy": acc,
            "f1": f1,
            "best_params": grid_search.best_params_
        })
        
        logger.info(f"Fold {fold_idx + 1}: AUC={auc:.4f}, Acc={acc:.4f}, F1={f1:.4f}")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Nested CV completed in {elapsed_time:.2f} seconds.")
    
    return {
        "mean_auc": float(np.mean(outer_scores)),
        "std_auc": float(np.std(outer_scores)),
        "fold_results": fold_results,
        "elapsed_time": elapsed_time,
        "best_params_overall": grid_search.best_params_
    }

def persist_model(model: Any, path: Path):
    """Saves the trained model to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    logger.info(f"Model saved to {path}")

def write_performance_report(report: Dict[str, Any], path: Path):
    """Saves performance report to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Performance report saved to {path}")

def main():
    """Main entry point for training."""
    logger.info("Starting model training pipeline.")
    
    # Load data
    subject_ids = load_eligible_subjects()
    X, y, feature_names = load_features(subject_ids)
    
    if len(np.unique(y)) < 2:
        logger.error("Only one class found in labels. Cannot train classifier.")
        sys.exit(1)
    
    # Run Nested CV
    results = train_and_evaluate_nested_cv(X, y, feature_names)
    
    # Train final model on full data for persistence (optional, but good practice)
    # Using the best params found
    final_pipeline = make_inner_pipeline()
    final_pipeline.set_params(**results['best_params_overall'])
    final_pipeline.fit(X, y)
    
    # Save artifacts
    persist_model(final_pipeline, MODEL_PATH)
    write_performance_report(results, PERFORMANCE_REPORT_PATH)
    
    logger.info("Training pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())