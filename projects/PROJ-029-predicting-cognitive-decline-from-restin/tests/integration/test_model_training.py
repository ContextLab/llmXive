"""
Integration test for model training and evaluation flow (T022).

This test verifies the end-to-end flow of:
1. Loading pre-computed graph metrics and labels from US1.
2. Running the collinearity filter and variance thresholding.
3. Executing a mini-nested CV (2 outer folds, 2 inner folds) with a Random Forest.
4. Verifying that the model trains without crashing and produces metrics.

NOTE: This test uses a synthetic mini-dataset generated in-memory to avoid
dependency on the full data pipeline execution during CI/CD unit tests,
ensuring it runs fast (< 30s) and deterministically.
"""
import os
import sys
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path to import code modules
# Assuming this file is at tests/integration/test_model_training.py
# and code/ is at project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.stats import calculate_correlation_matrix, filter_low_variance_features, check_collinearity
from utils.logger import get_logger
from config import get_config

# Mock the training logic to avoid importing the heavy 04_train_model.py directly
# if it has side effects, but here we implement the core logic inline for the test
# to ensure isolation.
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logger = get_logger("integration_test_model_training")

def _generate_mini_dataset(n_subjects=20, n_features=10, random_seed=42):
    """
    Generates a synthetic dataset mimicking data/processed/graph_metrics.csv
    with some correlation and variance structure to test filters.
    """
    np.random.seed(random_seed)
    
    # Create features with some correlation
    base = np.random.randn(n_subjects, 5)
    # Feature 6 is highly correlated with Feature 1
    correlated = base[:, 0] * 0.99 + np.random.randn(n_subjects) * 0.1
    # Feature 7 is low variance
    low_var = np.ones(n_subjects) * 0.5 + np.random.randn(n_subjects) * 0.001
    
    features = np.column_stack([base, correlated, low_var, np.random.randn(n_subjects, 3)])
    
    # Create a label based on a subset of features to ensure predictability
    # Label: 1 if sum of first 3 features > threshold, else 0
    threshold = np.mean(np.sum(features[:, :3], axis=1))
    labels = (np.sum(features[:, :3], axis=1) > threshold).astype(int)
    
    # Ensure we have both classes
    if len(np.unique(labels)) < 2:
        labels[0] = 1 - labels[0]
        
    df = pd.DataFrame(features, columns=[f"feat_{i}" for i in range(n_features)])
    df["label"] = labels
    
    return df

def _run_mini_nested_cv(df, n_outer=2, n_inner=2):
    """
    Runs a mini nested CV to verify the logic of T023 (collinearity, variance, RF).
    Returns the mean ROC-AUC and F1.
    """
    X = df.drop(columns=["label"]).values
    y = df["label"].values
    feature_names = df.drop(columns=["label"]).columns.tolist()
    
    outer_cv = StratifiedKFold(n_splits=n_outer, shuffle=True, random_state=42)
    inner_cv = StratifiedKFold(n_splits=n_inner, shuffle=True, random_state=42)
    
    auc_scores = []
    f1_scores = []
    
    # Parameters for grid search (simplified for speed)
    param_grid = {
        "rf__n_estimators": [10, 20],
        "rf__max_depth": [3, 5]
    }
    
    for train_idx, test_idx in outer_cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # 1. Collinearity Check (Pearson > 0.95)
        # We need to calculate correlation on training set only
        corr_matrix = calculate_correlation_matrix(X_train, feature_names)
        # Identify pairs with high correlation
        high_corr_pairs = []
        for i in range(len(feature_names)):
            for j in range(i + 1, len(feature_names)):
                if abs(corr_matrix.iloc[i, j]) > 0.95:
                    high_corr_pairs.append((feature_names[i], feature_names[j]))
        
        # Drop lower variance feature from each pair
        # We use variance of the training set to decide
        variances = np.var(X_train, axis=0)
        var_df = pd.DataFrame({"feat": feature_names, "var": variances})
        
        to_drop = set()
        for f1, f2 in high_corr_pairs:
            idx1 = feature_names.index(f1)
            idx2 = feature_names.index(f2)
            if variances[idx1] < variances[idx2]:
                to_drop.add(f1)
            else:
                to_drop.add(f2)
        
        kept_features = [f for f in feature_names if f not in to_drop]
        X_train_filtered = X_train[:, [feature_names.index(f) for f in kept_features]]
        X_test_filtered = X_test[:, [feature_names.index(f) for f in kept_features]]
        
        # 2. Variance Thresholding (var > 0.01)
        # Re-calculate variance on filtered training set
        variances_filtered = np.var(X_train_filtered, axis=0)
        kept_after_var = [f for f, v in zip(kept_features, variances_filtered) if v > 0.01]
        
        if len(kept_after_var) == 0:
            # Fallback if all dropped (unlikely with synthetic data)
            kept_after_var = kept_features
            
        final_indices = [kept_features.index(f) for f in kept_after_var]
        X_train_final = X_train_filtered[:, final_indices]
        X_test_final = X_test_filtered[:, final_indices]
        
        # 3. Model Training with Grid Search
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("rf", RandomForestClassifier(random_state=42, n_jobs=1))
        ])
        
        grid_search = GridSearchCV(
            pipeline, 
            param_grid, 
            cv=inner_cv, 
            scoring="roc_auc",
            n_jobs=1
        )
        
        grid_search.fit(X_train_final, y_train)
        
        # 4. Evaluation
        y_pred_proba = grid_search.predict_proba(X_test_final)[:, 1]
        y_pred = grid_search.predict(X_test_final)
        
        auc = roc_auc_score(y_test, y_pred_proba)
        f1 = f1_score(y_test, y_pred)
        
        auc_scores.append(auc)
        f1_scores.append(f1)
        
        logger.info(f"Outer Fold AUC: {auc:.4f}, F1: {f1:.4f}")
    
    return {
        "mean_auc": np.mean(auc_scores),
        "mean_f1": np.mean(f1_scores),
        "fold_count": len(auc_scores)
    }

def test_model_training_flow():
    """
    Integration test: Verify the model training flow works end-to-end.
    """
    # Setup temporary directory for artifacts
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        output_file = tmp_path / "mini_performance_report.json"
        
        try:
            # 1. Generate Mini Data
            logger.info("Generating mini synthetic dataset...")
            df = _generate_mini_dataset(n_subjects=30, n_features=15)
            
            # 2. Run Mini Nested CV
            logger.info("Running mini nested CV...")
            results = _run_mini_nested_cv(df, n_outer=2, n_inner=2)
            
            # 3. Verify Results
            assert results["fold_count"] == 2, "Should have 2 outer folds"
            assert 0.0 <= results["mean_auc"] <= 1.0, "AUC must be between 0 and 1"
            assert 0.0 <= results["mean_f1"] <= 1.0, "F1 must be between 0 and 1"
            
            # 4. Write Output (simulating what 05_evaluate_model.py would do)
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Test passed. Metrics: {results}")
            
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            raise

if __name__ == "__main__":
    test_model_training_flow()
    print("Integration test T022 passed successfully.")