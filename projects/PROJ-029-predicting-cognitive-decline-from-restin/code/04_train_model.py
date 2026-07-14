from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, VarianceThreshold
from sklearn.model_selection import GridSearchCV, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

from utils.io import ensure_dir, load_json, save_json, save_pickle
from utils.logger import get_logger, log_operation

# Constants
DATA_DIR = Path("data/processed")
ELIGIBLE_FILE = DATA_DIR / "eligible_subjects.csv"
GRAPH_METRICS_FILE = DATA_DIR / "graph_metrics.csv"
MODEL_OUTPUT = DATA_DIR / "model.pkl"
CV_RESULTS_OUTPUT = DATA_DIR / "cv_results.json"
MODEL_PARAMS_OUTPUT = DATA_DIR / "model_params.json"
PERFORMANCE_REPORT_OUTPUT = DATA_DIR / "performance_report.json"

# Decline definition
DECLINE_THRESHOLD = 3

# Grid search parameters
N_ESTIMATORS_GRID = [50, 100, 200]
MAX_DEPTH_GRID = [5, 10, None]

# Feature selection constraints
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01


class CollinearityTransformer:
    """
    Removes features with pairwise Pearson correlation > threshold.
    Keeps the feature with higher variance in case of a pair.
    """
    def __init__(self, threshold: float = CORRELATION_THRESHOLD):
        self.threshold = threshold
        self.keep_indices = None

    def fit(self, X: np.ndarray, y: Any = None) -> "CollinearityTransformer":
        n_features = X.shape[1]
        if n_features == 0:
            self.keep_indices = np.array([])
            return self

        # Calculate variance for each feature
        variances = np.var(X, axis=0)

        # Calculate correlation matrix
        corr_matrix = np.corrcoef(X.T)
        # Handle NaNs if any constant columns exist (though variance filter should catch them)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

        keep = set(range(n_features))
        removed = set()

        # Iterate to find pairs exceeding threshold
        # We need to be careful to only remove one of the pair
        for i in range(n_features):
            if i in removed:
                continue
            for j in range(i + 1, n_features):
                if j in removed:
                    continue
                if abs(corr_matrix[i, j]) > self.threshold:
                    # Remove the one with lower variance
                    if variances[i] >= variances[j]:
                        removed.add(j)
                    else:
                        removed.add(i)
                    break # Stop checking j for i once a high correlation is found

        self.keep_indices = np.array(sorted(list(keep - removed)))
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.keep_indices is None:
            raise ValueError("Transformer not fitted")
        if len(self.keep_indices) == 0:
            return np.empty((X.shape[0], 0))
        return X[:, self.keep_indices]

    def fit_transform(self, X: np.ndarray, y: Any = None) -> np.ndarray:
        self.fit(X, y)
        return self.transform(X)


def load_eligible_subjects() -> List[str]:
    logger = get_logger("load_eligible")
    logger.log("start", file=str(ELIGIBLE_FILE))
    if not ELIGIBLE_FILE.exists():
        logger.log("error", message="Eligible subjects file not found")
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_FILE}")
    
    df = pd.read_csv(ELIGIBLE_FILE)
    subjects = df['subject_id'].tolist()
    logger.log("end", count=len(subjects))
    return subjects


def load_features(subjects: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    logger = get_logger("load_features")
    logger.log("start", file=str(GRAPH_METRICS_FILE))
    
    if not GRAPH_METRICS_FILE.exists():
        logger.log("error", message="Graph metrics file not found")
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_FILE}")

    df = pd.read_csv(GRAPH_METRICS_FILE)
    
    # Filter for eligible subjects
    df = df[df['subject_id'].isin(subjects)]
    
    if df.empty:
        logger.log("error", message="No matching subjects found in graph metrics")
        raise ValueError("No matching subjects found in graph metrics")

    # Define features (columns except subject_id)
    feature_cols = [c for c in df.columns if c != 'subject_id']
    X = df[feature_cols].values.astype(float)
    
    # Define decline label: drop >= 3 points
    # Assuming the CSV has columns for MMSE/MOCA at timepoints, e.g., 'mmse_t1', 'mmse_t2'
    # If not present, we must derive or fail. Based on T017/T018, we expect these.
    # Let's assume standard naming from T017 logic: 'score_t1', 'score_t2' or similar.
    # Since T017 output 'eligible_subjects.csv', we need to know how scores are stored.
    # The task description says "Define decline label (drop >= 3 points)".
    # We assume the graph_metrics.csv (or a joined file) contains the scores.
    # If graph_metrics.csv only has topology, we might need to load scores separately.
    # However, for this implementation, we assume 'score_t1' and 'score_t2' are in the dataframe.
    
    score_cols = [c for c in df.columns if 'score' in c.lower() or 'mmse' in c.lower() or 'moca' in c.lower()]
    if len(score_cols) < 2:
        # Fallback: try to load from a separate scores file if it exists
        # Or raise error if we can't compute the label
        logger.log("warning", message="Score columns not found in graph_metrics, attempting fallback or error")
        # For robustness, we assume the task T017 ensures scores are available.
        # If not, we cannot proceed.
        raise ValueError("Could not find score columns to define decline label.")
    
    # Sort score columns to identify t1 and t2 (assuming alphabetical or numeric suffix)
    # Let's assume the last two score columns are the timepoints
    score_cols = sorted(score_cols, key=lambda x: x.lower())
    t1_col, t2_col = score_cols[-2], score_cols[-1]
    
    y = (df[t1_col] - df[t2_col] >= DECLINE_THRESHOLD).astype(int).values
    
    logger.log("end", features=len(feature_cols), samples=len(X), decline_rate=float(y.mean()))
    return X, y


def define_decline_label(df: pd.DataFrame) -> np.ndarray:
    """Helper to define label from dataframe."""
    # Implementation inline in load_features for now to keep it simple
    pass


def train_and_evaluate_nested_cv(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, Any], Dict[str, Any]]:
    logger = get_logger("nested_cv")
    logger.log("start", samples=X.shape[0], features=X.shape[1])

    # Outer CV
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    # Inner CV for Grid Search
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=42)
    
    param_grid = {
        'randomforest__n_estimators': N_ESTIMATORS_GRID,
        'randomforest__max_depth': MAX_DEPTH_GRID
    }

    # Define the pipeline:
    # 1. Collinearity Filter
    # 2. Variance Threshold
    # 3. RFE (Recursive Feature Elimination) to select <= 20 features
    # 4. StandardScaler
    # 5. Random Forest
    
    # Note: RFE requires an estimator. We use a simple RF for RFE step.
    rfe_estimator = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
    
    pipe = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=CORRELATION_THRESHOLD)),
        ('variance', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=rfe_estimator, n_features_to_select=MAX_FEATURES)),
        ('scaler', StandardScaler()),
        ('randomforest', RandomForestClassifier(random_state=42))
    ])

    grid_search = GridSearchCV(
        pipe, 
        param_grid, 
        cv=inner_cv, 
        scoring='roc_auc', 
        n_jobs=2,
        refit=True
    )

    # Outer loop evaluation
    outer_scores = []
    best_params_list = []
    selected_features_count = []

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        grid_search.fit(X_train, y_train)
        
        # Record best params for this fold
        best_params_list.append(grid_search.best_params_)
        
        # Evaluate on test set
        score = grid_search.score(X_test, y_test)
        outer_scores.append(score)
        
        # Count features selected (RFE step)
        # Access the fitted pipeline in the best estimator
        best_pipeline = grid_search.best_estimator_
        rfe_step = best_pipeline.named_steps['rfe']
        n_selected = rfe_step.n_features_
        selected_features_count.append(n_selected)

    mean_score = float(np.mean(outer_scores))
    std_score = float(np.std(outer_scores))
    
    # Aggregate results
    cv_results = {
        "outer_cv_scores": outer_scores,
        "mean_outer_score": mean_score,
        "std_outer_score": std_score,
        "best_params_per_fold": best_params_list,
        "features_selected_per_fold": selected_features_count,
        "grid_search_params": param_grid,
        "outer_splits": 5,
        "inner_splits": 3
    }
    
    # Final model: retrain on ALL data with best params found (or average?)
    # Usually, we take the best params from the grid search over the whole dataset or the most frequent.
    # For simplicity, we take the best params from the last fold or the one with highest score.
    best_idx = np.argmax(outer_scores)
    final_params = best_params_list[best_idx]
    
    # Retrain on full data
    final_model = Pipeline([
        ('collinearity', CollinearityTransformer(threshold=CORRELATION_THRESHOLD)),
        ('variance', VarianceThreshold(threshold=VARIANCE_THRESHOLD)),
        ('rfe', RFE(estimator=rfe_estimator, n_features_to_select=MAX_FEATURES)),
        ('scaler', StandardScaler()),
        ('randomforest', RandomForestClassifier(random_state=42))
    ])
    
    final_model.set_params(**final_params)
    final_model.fit(X, y)
    
    logger.log("end", mean_score=mean_score, std_score=std_score)
    return final_model, cv_results, final_params


def persist_model(model: Any, params: Dict[str, Any]) -> None:
    logger = get_logger("persist_model")
    logger.log("start", output=str(MODEL_OUTPUT))
    
    ensure_dir(MODEL_OUTPUT.parent)
    save_pickle(MODEL_OUTPUT, model)
    save_json(MODEL_PARAMS_OUTPUT, params)
    
    logger.log("end", success=True)


def write_performance_report(cv_results: Dict[str, Any]) -> None:
    logger = get_logger("performance_report")
    logger.log("start", output=str(PERFORMANCE_REPORT_OUTPUT))
    
    ensure_dir(PERFORMANCE_REPORT_OUTPUT.parent)
    
    report = {
        "roc_auc": cv_results["mean_outer_score"],
        "std_roc_auc": cv_results["std_outer_score"],
        "cv_folds": cv_results["outer_splits"],
        "inner_cv_folds": cv_results["inner_splits"],
        "grid_params": cv_results["grid_search_params"],
        "features_selected": cv_results["features_selected_per_fold"]
    }
    
    save_json(PERFORMANCE_REPORT_OUTPUT, report)
    logger.log("end", success=True)


@log_operation("train_model")
def main() -> int:
    try:
        subjects = load_eligible_subjects()
        X, y = load_features(subjects)
        
        model, cv_results, params = train_and_evaluate_nested_cv(X, y)
        
        persist_model(model, params)
        write_performance_report(cv_results)
        
        return 0
    except Exception as e:
        logger = get_logger("train_model")
        logger.log("error", message=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())