import logging
import sys
import os
import json
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, DummyRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.inspection import permutation_importance
import joblib

from utils import get_logger, ensure_dir

logger = get_logger(__name__)
RANDOM_STATE = 42

def load_data(path: str = "data/processed/processed_alloys.csv") -> pd.DataFrame:
    """Load processed data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)

def train_model(df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Train Random Forest and compute metrics.
    """
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    # Check if columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, 'critical_cooling_rate']
    
    if len(X) < 10:
        raise ValueError("Not enough data to train model.")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    
    # Train RF
    rf = RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
    rf.fit(X_train, y_train)
    
    # Cross Validation
    cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
    cv_rmse = np.sqrt(-cv_scores)
    mean_rmse = np.mean(cv_rmse)
    
    # Test Evaluation
    y_pred = rf.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # Null Model
    null_model = DummyRegressor(strategy='mean', random_state=RANDOM_STATE)
    null_model.fit(X_train, y_train)
    null_pred = null_model.predict(X_test)
    null_rmse = np.sqrt(mean_squared_error(y_test, null_pred))
    
    # Permutation Test for Significance
    # Simple approximation: compare RF RMSE vs Null RMSE
    # A full permutation test (shuffling targets) is expensive, we'll do a quick check
    # or just report the p-value logic as a placeholder if needed.
    # For this task, we calculate p-value via permutation of residuals or simple comparison.
    # Let's implement a simple permutation test on the test set.
    n_permutations = 100
    perm_scores = []
    for _ in range(n_permutations):
        y_perm = y_test.sample(frac=1, random_state=np.random.randint(0, 10000)).values
        perm_rmse = np.sqrt(mean_squared_error(y_perm, y_pred))
        perm_scores.append(perm_rmse)
    
    # P-value: proportion of permuted RMSE <= observed RF RMSE
    # Lower RMSE is better. If RF is better, observed RMSE should be lower than most permuted.
    # We want p = (count(perm <= obs) + 1) / (n + 1)
    obs_rmse = test_rmse
    count = sum(1 for s in perm_scores if s <= obs_rmse)
    p_value = (count + 1) / (n_permutations + 1)
    
    if p_value >= 0.05:
        logger.warning(f"Model not statistically distinguishable from null (p >= 0.05, p={p_value:.3f})")
    else:
        logger.info(f"Model is statistically distinguishable from null (p < 0.05, p={p_value:.3f})")
    
    metrics = {
        'fold_scores': cv_rmse.tolist(),
        'mean_rmse': float(mean_rmse),
        'test_rmse': float(test_rmse),
        'null_rmse': float(null_rmse),
        'p_value_vs_null': float(p_value),
        'feature_importance_ranking': [
            feat for feat, _ in sorted(
                zip(feature_cols, rf.feature_importances_), 
                key=lambda x: x[1], reverse=True
            )
        ]
    }
    
    return rf, metrics

def generate_null_distribution(rf_model, X_test, y_test, n=1000):
    """Generate null distribution for RMSE via permutation."""
    # Placeholder for T024 logic if needed separately
    pass

def run_training(input_path: str = "data/processed/processed_alloys.csv",
                 model_path: str = "data/models/random_forest_model.pkl",
                 metrics_path: str = "data/models/model_metrics.json") -> None:
    """
    Main entry point for training.
    """
    ensure_dir(os.path.dirname(model_path))
    ensure_dir(os.path.dirname(metrics_path))
    
    df = load_data(input_path)
    model, metrics = train_model(df)
    
    # Save model
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

if __name__ == "__main__":
    run_training()
