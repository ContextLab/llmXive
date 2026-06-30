"""
Train a Random Forest classifier with nested cross-validation.
Implements collinearity filtering, variance thresholding, and RFE.
"""
import os
import sys
import json
import time
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.feature_selection import VarianceThreshold, RFE
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

# Reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Constants
MEMORY_LIMIT_GB = 7.0
MAX_FEATURES = 20
CORRELATION_THRESHOLD = 0.95
VARIANCE_THRESHOLD = 0.01
TIME_LIMIT_MINUTES = 30

def define_decline_label(mmse_scores: pd.DataFrame, mocas_scores: pd.DataFrame = None) -> pd.Series:
    """
    Define cognitive decline label: drop >= 3 points.
    If MOCA is available, use it; otherwise use MMSE.
    """
    if mocas_scores is not None:
        # Prefer MOCA if available
        scores = mocas_scores
    else:
        scores = mmse_scores

    if "baseline" not in scores.columns or "followup" not in scores.columns:
        raise ValueError("Scores must have 'baseline' and 'followup' columns")

    decline = scores["baseline"] - scores["followup"]
    return (decline >= 3).astype(int)

def collinearity_filter(X: np.ndarray, threshold: float = CORRELATION_THRESHOLD):
    """
    Remove features with high correlation (> threshold).
    Keeps the feature with higher variance.
    Returns filtered feature indices.
    """
    if X.shape[1] <= 1:
        return list(range(X.shape[1]))

    corr_matrix = np.corrcoef(X.T)
    np.fill_diagonal(corr_matrix, 0)  # Ignore self-correlation

    keep = set(range(X.shape[1]))
    removed = set()

    for i in range(X.shape[1]):
        if i in removed:
            continue
        for j in range(i + 1, X.shape[1]):
            if j in removed:
                continue
            if abs(corr_matrix[i, j]) > threshold:
                # Keep the one with higher variance
                var_i = np.var(X[:, i])
                var_j = np.var(X[:, j])
                if var_i >= var_j:
                    removed.add(j)
                else:
                    removed.add(i)

    return [i for i in keep if i not in removed]

def inner_cv_pipeline(X, y, param_grid, cv_inner):
    """
    Inner CV loop with feature selection and model training.
    """
    # Step 1: Collinearity filter
    keep_indices = collinearity_filter(X, threshold=CORRELATION_THRESHOLD)
    X_filtered = X[:, keep_indices]

    # Step 2: Variance thresholding
    vt = VarianceThreshold(threshold=VARIANCE_THRESHOLD)
    X_var = vt.fit_transform(X_filtered)

    # Step 3: RFE to select top features
    base_rf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=1)
    rfe = RFE(estimator=base_rf, n_features_to_select=min(MAX_FEATURES, X_var.shape[1]), step=1)
    X_rfe = rfe.fit_transform(X_var, y)

    # Step 4: Grid search on selected features
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1))
    ])

    grid_search = GridSearchCV(
        pipe,
        param_grid,
        cv=cv_inner,
        scoring='roc_auc',
        n_jobs=1,  # Controlled parallelism
        refit=True
    )
    grid_search.fit(X_rfe, y)

    return grid_search.best_estimator_, grid_search.best_params_

def train_and_evaluate_nested_cv(X, y, param_grid=None):
    """
    Perform nested cross-validation.
    Outer CV for evaluation, inner CV for hyperparameter tuning.
    """
    if param_grid is None:
        param_grid = {
            'rf__n_estimators': [50, 100, 200],
            'rf__max_depth': [5, 10, None]
        }

    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_SEED)

    scores = []
    best_models = []

    start_time = time.time()

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Inner CV
        best_model, best_params = inner_cv_pipeline(X_train, y_train, param_grid, inner_cv)

        # Evaluate on test fold
        y_pred_proba = best_model.predict_proba(X_test)[:, 1]
        from sklearn.metrics import roc_auc_score
        try:
            auc = roc_auc_score(y_test, y_pred_proba)
            scores.append(auc)
        except Exception as e:
            print(f"Fold {fold_idx} evaluation failed: {e}", file=sys.stderr)
            scores.append(np.nan)

        best_models.append((best_model, best_params))

        elapsed = time.time() - start_time
        if elapsed > TIME_LIMIT_MINUTES * 60:
            print(f"Time limit exceeded at fold {fold_idx}", file=sys.stderr)
            break

    mean_auc = np.nanmean(scores)
    return mean_auc, scores, best_models

def main():
    """Main entry point for model training."""
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "processed" / "graph_metrics.csv"
    labels_path = project_root / "data" / "processed" / "eligible_subjects.csv"
    output_model_path = project_root / "data" / "processed" / "model.pkl"
    output_params_path = project_root / "data" / "processed" / "model_params.json"

    if not input_path.exists():
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    if not labels_path.exists():
        print(f"Error: {labels_path} not found.", file=sys.stderr)
        sys.exit(1)

    # Load data
    metrics_df = pd.read_csv(input_path)
    labels_df = pd.read_csv(labels_path)

    # Merge to get labels
    merged = metrics_df.merge(labels_df, on="subject_id", how="inner")

    if "decline_label" not in merged.columns:
        # Compute decline label if not present
        mmse = labels_df[["subject_id", "mmse_baseline", "mmse_followup"]]
        merged["decline_label"] = (merged["mmse_baseline"] - merged["mmse_followup"] >= 3).astype(int)

    # Prepare features and labels
    feature_cols = ["degree", "global_efficiency", "clustering_coefficient", "avg_path_length"]
    if not all(col in merged.columns for col in feature_cols):
        print("Missing required feature columns", file=sys.stderr)
        sys.exit(1)

    X = merged[feature_cols].values
    y = merged["decline_label"].values

    if len(np.unique(y)) < 2:
        print("Only one class present in labels. Cannot train classifier.", file=sys.stderr)
        sys.exit(1)

    print(f"Training on {len(X)} samples, {X.shape[1]} features.")

    # Train
    mean_auc, fold_scores, best_models = train_and_evaluate_nested_cv(X, y)

    print(f"Nested CV ROC-AUC: {mean_auc:.4f} (+/- {np.nanstd(fold_scores):.4f})")

    # Save best model from last fold (or average if needed)
    # For simplicity, save the last fold's model
    best_model, best_params = best_models[-1]
    joblib.dump(best_model, output_model_path)

    # Save params
    params_record = {
        "mean_auc": float(mean_auc),
        "fold_scores": [float(s) if not np.isnan(s) else None for s in fold_scores],
        "best_params": best_params
    }
    with open(output_params_path, "w") as f:
        json.dump(params_record, f, indent=2)

    print(f"Model saved to {output_model_path}")
    print(f"Params saved to {output_params_path}")

if __name__ == "__main__":
    main()
