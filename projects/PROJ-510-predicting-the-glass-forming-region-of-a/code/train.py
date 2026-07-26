"""
Model Training: Train Random Forest and evaluate.
"""
import logging
import sys
import os
import json
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, DummyRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.dummy import DummyRegressor
import joblib

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from code.utils import logger, RANDOM_STATE, ensure_dir
from code.features import OUTPUT_PATH_PROCESSED

MODEL_PATH = "data/models/random_forest_model.pkl"
METRICS_PATH = "data/models/model_metrics.json"
INPUT_PATH = OUTPUT_PATH_PROCESSED

def load_data() -> pd.DataFrame:
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Data not found at {INPUT_PATH}")
    return pd.read_csv(INPUT_PATH)

def train_model(df: pd.DataFrame) -> tuple:
    """
    Train Random Forest with 5-fold CV and evaluate.
    """
    features = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    target = 'critical_cooling_rate'
    
    X = df[features].fillna(0)
    y = df[target].fillna(0)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    
    # Train RF
    rf = RandomForestRegressor(
        n_estimators=100, 
        random_state=RANDOM_STATE, 
        n_jobs=-1
    )
    
    # Cross Validation
    cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='neg_root_mean_squared_error')
    cv_rmse = -cv_scores
    mean_cv_rmse = np.mean(cv_rmse)
    
    # Fit on full train
    rf.fit(X_train, y_train)
    
    # Test Evaluation
    y_pred = rf.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return rf, {
        'fold_scores': cv_rmse.tolist(),
        'mean_cv_rmse': float(mean_cv_rmse),
        'test_rmse': float(test_rmse),
        'n_test_samples': len(y_test)
    }

def generate_null_distribution(X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
    """
    Generate null model distribution using DummyRegressor (mean strategy).
    """
    logger.info("Generating null model distribution (1000 bootstrap samples)...")
    rng = np.random.default_rng(RANDOM_STATE)
    null_scores = []
    
    n_bootstraps = 1000
    # Subsample for speed if dataset is huge, but spec says 1000 samples
    for i in range(n_bootstraps):
        # Bootstrap sample
        indices = rng.choice(len(y_train), size=len(y_train), replace=True)
        X_boot = X_train.iloc[indices]
        y_boot = y_train.iloc[indices]
        
        dummy = DummyRegressor(strategy='mean')
        dummy.fit(X_boot, y_boot)
        
        # Evaluate on a hold-out or same set? Spec implies distribution of RMSE.
        # Usually compare to test set, but for null distribution of the metric itself:
        # We can evaluate on the same boot sample or a fixed test set.
        # Let's evaluate on a fixed random split of the original train for consistency?
        # Or simply RMSE on the boot sample itself (in-sample error).
        # Spec says "record the RMSE distribution".
        y_pred = dummy.predict(X_boot)
        rmse = np.sqrt(mean_squared_error(y_boot, y_pred))
        null_scores.append(rmse)
        
        if (i + 1) % 100 == 0:
            logger.info(f"  Bootstrap {i+1}/{n_bootstraps}")
    
    return {
        'null_rmse_distribution': null_scores,
        'mean_null_rmse': float(np.mean(null_scores)),
        'std_null_rmse': float(np.std(null_scores))
    }

def run_training() -> None:
    ensure_dir("data/models")
    
    df = load_data()
    rf_model, metrics = train_model(df)
    
    # Save Model
    joblib.dump(rf_model, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")
    
    # Save Metrics
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {METRICS_PATH}")
    
    # Null Model (Optional but required by T024a)
    # Extract train set for null generation
    features = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    target = 'critical_cooling_rate'
    X = df[features].fillna(0)
    y = df[target].fillna(0)
    _, X_train, _, y_train = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
    
    null_dist = generate_null_distribution(X_train, y_train)
    null_path = "data/models/null_model_distribution.json"
    with open(null_path, 'w') as f:
        json.dump(null_dist, f, indent=2)
    logger.info(f"Null distribution saved to {null_path}")

if __name__ == "__main__":
    run_training()
