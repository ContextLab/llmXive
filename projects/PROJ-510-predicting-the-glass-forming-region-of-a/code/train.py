"""
FINDINGS ARE ASSOCIATIONAL: This study uses observational data; no causal claims are made.

Training script for Glass Forming Region prediction.
Implements Random Forest regression with cross-validation and null model comparison.
"""
import logging
import sys
import os
import json
import pickle
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_ind

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.utils import get_logger, ensure_dir

logger = get_logger(__name__)

# Paths
PROCESSED_DATA_PATH = os.path.join(project_root, "data", "processed", "processed_alloys.csv")
MODEL_DIR = os.path.join(project_root, "data", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest_model.pkl")
CV_METRICS_PATH = os.path.join(MODEL_DIR, "cv_metrics.json")
NULL_PREDICTIONS_PATH = os.path.join(MODEL_DIR, "null_model_predictions.npy")
NULL_RMSE_PATH = os.path.join(MODEL_DIR, "null_model_rmse.json")
STAT_COMPARISON_PATH = os.path.join(MODEL_DIR, "statistical_comparison.json")

def load_data() -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Load processed alloy data and prepare features/target."""
    logger.info(f"Loading data from {PROCESSED_DATA_PATH}")
    if not os.path.exists(PROCESSED_DATA_PATH):
        raise FileNotFoundError(f"Processed data not found at {PROCESSED_DATA_PATH}. Run ingestion.py first.")
    
    df = pd.read_csv(PROCESSED_DATA_PATH)
    
    # Define feature columns
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    
    # Validate columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    if 'critical_cooling_rate' not in df.columns:
        raise ValueError("Missing target column: critical_cooling_rate")
    
    X = df[feature_cols].values
    y = df['critical_cooling_rate'].values
    
    logger.info(f"Loaded {len(df)} samples with {len(feature_cols)} features")
    return df, X, y

def train_model(X_train: np.ndarray, y_train: np.ndarray, random_state: int = 42) -> RandomForestRegressor:
    """Train a Random Forest regressor."""
    logger.info("Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    logger.info("Model training complete.")
    return model

def run_cross_validation(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> Dict[str, Any]:
    """Perform k-fold cross-validation and return metrics."""
    logger.info(f"Running {n_splits}-fold cross-validation...")
    
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=kf, scoring='neg_mean_squared_error')
    
    # Convert negative MSE to RMSE
    rmse_scores = np.sqrt(-scores)
    fold_scores = rmse_scores.tolist()
    mean_rmse = float(np.mean(rmse_scores))
    fold_variance = float(np.var(rmse_scores))
    
    metrics = {
        "fold_scores": fold_scores,
        "mean_rmse": mean_rmse,
        "fold_variance": fold_variance,
        "n_splits": n_splits
    }
    
    logger.info(f"Cross-validation mean RMSE: {mean_rmse:.4f} (+/- {np.std(rmse_scores):.4f})")
    return metrics

def evaluate_on_test(model: RandomForestRegressor, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[float, np.ndarray]:
    """Evaluate model on held-out test set and return RMSE and predictions."""
    logger.info("Evaluating on test set...")
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    logger.info(f"Test set RMSE: {rmse:.4f}")
    return rmse, y_pred

def generate_null_baseline(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, random_state: int = 42) -> Tuple[float, np.ndarray]:
    """Generate null model baseline (mean strategy) and return RMSE and predictions."""
    logger.info("Generating null model baseline (mean strategy)...")
    null_model = DummyRegressor(strategy='mean', random_state=random_state)
    null_model.fit(X_train, y_train)
    
    y_null_pred = null_model.predict(X_test)
    null_rmse = np.sqrt(mean_squared_error(y_test, y_null_pred))
    
    logger.info(f"Null model RMSE: {null_rmse:.4f}")
    return null_rmse, y_null_pred

def compare_models(y_test: np.ndarray, y_rf_pred: np.ndarray, y_null_pred: np.ndarray) -> Dict[str, Any]:
    """
    Compare RF RMSE against null model baseline using a two-sided unpaired t-test.
    SC-002: Statistical significance testing.
    """
    logger.info("Comparing RF model against null baseline...")
    
    # Calculate absolute errors
    abs_errors_rf = np.abs(y_test - y_rf_pred)
    abs_errors_null = np.abs(y_test - y_null_pred)
    
    # Perform two-sided unpaired t-test
    t_stat, p_value = ttest_ind(abs_errors_rf, abs_errors_null)
    
    result = {
        "p_value": float(p_value),
        "test_statistic": float(t_stat),
        "conclusion": "distinguishable" if p_value < 0.05 else "not distinguishable"
    }
    
    if p_value < 0.05:
        logger.info(f"Model is statistically distinguishable from null (p < 0.05, p={p_value:.6f})")
    else:
        logger.warning(f"Model is NOT statistically distinguishable from null (p >= 0.05, p={p_value:.6f})")
    
    return result

def save_model(model: RandomForestRegressor, path: str):
    """Save trained model to disk."""
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def save_metrics(metrics: Dict[str, Any], path: str):
    """Save metrics dictionary to JSON."""
    ensure_dir(path)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {path}")

def run_training():
    """Main entry point for training pipeline."""
    try:
        # Load data
        df, X, y = load_data()
        
        # Train-test split
        logger.info("Splitting data (train/test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Train model
        model = train_model(X_train, y_train)
        
        # Cross-validation
        cv_metrics = run_cross_validation(model, X_train, y_train)
        cv_metrics['random_state'] = 42
        save_metrics(cv_metrics, CV_METRICS_PATH)
        
        # Evaluate on test set
        test_rmse, y_rf_pred = evaluate_on_test(model, X_test, y_test)
        
        # Generate null baseline
        null_rmse, y_null_pred = generate_null_baseline(X_train, y_train, X_test, y_test)
        save_metrics({"null_rmse": null_rmse}, NULL_RMSE_PATH)
        np.save(NULL_PREDICTIONS_PATH, y_null_pred)
        
        # Compare models (T024 implementation)
        comparison = compare_models(y_test, y_rf_pred, y_null_pred)
        save_metrics(comparison, STAT_COMPARISON_PATH)
        
        # Save final model
        save_model(model, MODEL_PATH)
        
        # Final summary
        logger.info("--- Training Complete ---")
        logger.info(f"Test RMSE: {test_rmse:.4f}")
        logger.info(f"Null RMSE: {null_rmse:.4f}")
        logger.info(f"Statistical Significance (p-value): {comparison['p_value']:.6f}")
        logger.info(f"Conclusion: RF model is {comparison['conclusion']} from null baseline.")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_training()
