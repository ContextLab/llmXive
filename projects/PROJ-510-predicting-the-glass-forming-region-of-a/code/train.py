# FINDINGS ARE ASSOCIATIONAL: This study uses observational data; no causal claims are made.

"""
train.py - Model Training and Evaluation Pipeline

Implements Random Forest regression for predicting critical cooling rates
in glass-forming alloys. Handles data loading, cross-validation, model training,
and evaluation against a null baseline.
"""

import logging
import sys
import os
import json
import pickle
from typing import Dict, Any, Tuple, List

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error
from sklearn.dummy import DummyRegressor
from scipy import stats

# Ensure project root is in path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.utils import get_logger, ensure_dir

# Configuration
RANDOM_STATE = 42
DATA_PATH = os.path.join(project_root, 'data', 'processed', 'processed_alloys.csv')
MODEL_DIR = os.path.join(project_root, 'data', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'random_forest_model.pkl')
CV_METRICS_PATH = os.path.join(MODEL_DIR, 'cv_metrics.json')
NULL_PRED_PATH = os.path.join(MODEL_DIR, 'null_model_predictions.npy')
NULL_RMSE_PATH = os.path.join(MODEL_DIR, 'null_model_rmse.json')
STAT_COMPARISON_PATH = os.path.join(MODEL_DIR, 'statistical_comparison.json')
FINAL_METRICS_PATH = os.path.join(MODEL_DIR, 'model_metrics_final.json')

logger = get_logger(__name__)

def load_data() -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load processed alloy data and split into features and target.
    Returns X, y_train, y_test splits.
    """
    logger.info(f"Loading data from {DATA_PATH}")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Processed data not found at {DATA_PATH}. Run ingestion.py first.")

    df = pd.read_csv(DATA_PATH)

    # Define feature columns based on feature engineering tasks
    feature_cols = [
        'mixing_enthalpy',
        'atomic_size_mismatch',
        'electronegativity_variance'
    ]

    # Verify columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")

    X = df[feature_cols].values
    y = df['critical_cooling_rate'].values

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    logger.info(f"Data split: {len(X_train)} train, {len(X_test)} test")
    return X_train, X_test, y_train, y_test

def train_model(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor.
    """
    logger.info("Training Random Forest Regressor...")
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    logger.info("Model training complete.")
    return model

def run_cross_validation(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation and return metrics.
    """
    logger.info("Running cross-validation...")
    # Use negative MSE as scoring for RMSE calculation
    cv_scores = cross_val_score(
        model, X, y, cv=5, scoring='neg_mean_squared_error', n_jobs=-1
    )
    
    # Convert to RMSE
    rmse_scores = np.sqrt(-cv_scores)
    mean_rmse = np.mean(rmse_scores)
    fold_scores = rmse_scores.tolist()

    logger.info(f"Cross-validation RMSE: {mean_rmse:.4f} (+/- {np.std(rmse_scores):.4f})")
    
    return {
        'fold_scores': fold_scores,
        'mean_rmse': float(mean_rmse)
    }

def evaluate_on_test(model: RandomForestRegressor, X_test: np.ndarray, y_test: np.ndarray) -> float:
    """
    Evaluate model on held-out test set and calculate RMSE.
    """
    logger.info("Evaluating on test set...")
    y_pred = model.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    logger.info(f"Test RMSE: {test_rmse:.4f}")
    return test_rmse, y_pred

def generate_null_baseline(y_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Generate predictions using a DummyRegressor (mean strategy).
    """
    logger.info("Generating null baseline (DummyRegressor)...")
    dummy = DummyRegressor(strategy='mean', random_state=RANDOM_STATE)
    # Dummy regressor only needs y_train, but fit() signature requires X
    dummy.fit(np.zeros((len(y_train), 1)), y_train)
    
    y_pred_null = dummy.predict(X_test)
    null_rmse = np.sqrt(mean_squared_error(y_test=y_test, y_pred=y_pred_null)) # type: ignore
    
    logger.info(f"Null model RMSE: {null_rmse:.4f}")
    return y_pred_null, null_rmse

def compare_models(y_test: np.ndarray, y_pred_rf: np.ndarray, y_pred_null: np.ndarray) -> Dict[str, float]:
    """
    Compare RF and Null model errors using a paired t-test.
    """
    logger.info("Performing statistical comparison (paired t-test)...")
    
    # Calculate absolute errors
    errors_rf = np.abs(y_test - y_pred_rf)
    errors_null = np.abs(y_test - y_pred_null)
    
    # Paired t-test (two-sided)
    # Note: scipy.stats.ttest_rel handles paired data
    t_stat, p_value = stats.ttest_rel(errors_rf, errors_null)
    
    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_value:.6f}")
    if p_value < 0.05:
        logger.info("Model is statistically distinguishable from null (p < 0.05)")
    else:
        logger.warning("Model is NOT statistically distinguishable from null (p >= 0.05)")
    
    return {
        'p_value': float(p_value),
        'test_statistic': float(t_stat)
    }

def save_model(model: RandomForestRegressor, path: str) -> None:
    """
    Save the trained model to disk.
    """
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def save_metrics(metrics: Dict[str, Any], path: str) -> None:
    """
    Save metrics to JSON.
    """
    ensure_dir(path)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {path}")

def run_training() -> None:
    """
    Main execution function for the training pipeline.
    """
    try:
        # 1. Load Data
        X_train, X_test, y_train, y_test = load_data()

        # 2. Train Model
        model = train_model(X_train, y_train)

        # 3. Cross-Validation
        # Note: We run CV on the full training data to get fold scores
        cv_metrics = run_cross_validation(model, X_train, y_train)

        # 4. Evaluate on Test Set
        test_rmse, y_pred_rf = evaluate_on_test(model, X_test, y_test)

        # 5. Generate Null Baseline
        y_pred_null, null_rmse = generate_null_baseline(y_train, X_test)

        # 6. Statistical Comparison
        stat_results = compare_models(y_test, y_pred_rf, y_pred_null)

        # 7. Feature Importance Ranking
        feature_importance = model.feature_importances_
        feature_names = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
        sorted_indices = np.argsort(feature_importance)[::-1]
        feature_importance_ranking = [feature_names[i] for i in sorted_indices]

        # 8. Save Artifacts
        # Save Model
        save_model(model, MODEL_PATH)

        # Save CV Metrics
        cv_output = {
            'fold_scores': cv_metrics['fold_scores'],
            'mean_rmse': cv_metrics['mean_rmse'],
            'test_rmse': float(test_rmse)
        }
        save_metrics(cv_output, CV_METRICS_PATH)

        # Save Null Model Predictions and RMSE
        np.save(NULL_PRED_PATH, y_pred_null)
        save_metrics({'null_rmse': float(null_rmse)}, NULL_RMSE_PATH)

        # Save Statistical Comparison
        save_metrics(stat_results, STAT_COMPARISON_PATH)

        # 9. Aggregate Final Metrics
        final_metrics = {
            'fold_scores': cv_metrics['fold_scores'],
            'mean_rmse': cv_metrics['mean_rmse'],
            'test_rmse': float(test_rmse),
            'feature_importance_ranking': feature_importance_ranking,
            'p_value_vs_null': stat_results['p_value'],
            'findings_associational': True,
            'note': 'FINDINGS ARE ASSOCIATIONAL'
        }
        save_metrics(final_metrics, FINAL_METRICS_PATH)

        logger.info("Training pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == '__main__':
    run_training()
