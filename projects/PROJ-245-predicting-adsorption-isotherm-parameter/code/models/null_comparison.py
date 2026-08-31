"""
Null Model Comparison Module for T024.

Implements the comparison between trained models and a null model (predicting the mean).
Performs paired statistical tests on cross-validation fold RMSEs and calculates
bootstrapped confidence intervals for R².
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
from scipy import stats
from sklearn.model_selection import cross_val_predict, KFold

# Import from existing project modules
from models.evaluate import bootstrap_confidence_intervals, load_test_data, load_models
from models.train import load_preprocessed_data, material_level_split, train_models

logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    output_dir = Path("data/validation")
    output_dir.mkdir(parents=True, exist_ok=True)

def predict_mean_null_model(X: np.ndarray, y: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Predicts the mean of the training target for all test samples.
    
    Args:
        X: Training features (unused, but kept for signature consistency)
        y: Training targets
        X_test: Test features (unused)
        y_test: Test targets (unused for prediction, used for metrics)
    
    Returns:
        Tuple of (predictions, mean_train_y)
    """
    mean_y = np.mean(y)
    predictions = np.full_like(y_test, mean_y, dtype=float)
    return predictions, mean_y

def calculate_null_model_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R², RMSE, MAE for the null model."""
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = np.mean(np.abs(y_true - y_pred))
    return {
        "r2": float(r2),
        "rmse": float(rmse),
        "mae": float(mae)
    }

def run_cross_fold_comparison(
    X: np.ndarray, 
    y: np.ndarray, 
    model_name: str, 
    model: Any,
    n_splits: int = 5
) -> Dict[str, Any]:
    """
    Performs cross-validation to generate paired RMSEs for the trained model and the null model.
    
    Args:
        X: Features
        y: Target
        model_name: Name of the trained model
        model: Trained sklearn model instance
        n_splits: Number of CV folds
    
    Returns:
        Dictionary containing fold-level metrics and statistical test results.
    """
    logger.info(f"Running {n_splits}-fold cross-validation for {model_name} vs Null Model...")
    
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    trained_r2s = []
    trained_rmses = []
    null_r2s = []
    null_rmses = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train_fold, X_test_fold = X[train_idx], X[test_idx]
        y_train_fold, y_test_fold = y[train_idx], y[test_idx]
        
        # Train the specific model on the fold
        # We assume the model is a clone or can be re-fit. 
        # For this implementation, we re-fit the passed model instance.
        # Note: In a real pipeline, we would clone the model to avoid state leakage.
        try:
            model.fit(X_train_fold, y_train_fold)
            y_pred_trained = model.predict(X_test_fold)
        except Exception as e:
            logger.error(f"Fold {fold_idx} training failed: {e}")
            continue
        
        # Null model prediction (mean of train fold)
        y_pred_null, _ = predict_mean_null_model(X_train_fold, y_train_fold, X_test_fold, y_test_fold)
        
        # Calculate metrics
        r2_trained = r2_score(y_test_fold, y_pred_trained)
        rmse_trained = np.sqrt(mean_squared_error(y_test_fold, y_pred_trained))
        
        r2_null = r2_score(y_test_fold, y_pred_null)
        rmse_null = np.sqrt(mean_squared_error(y_test_fold, y_pred_null))
        
        trained_r2s.append(r2_trained)
        trained_rmses.append(rmse_trained)
        null_r2s.append(r2_null)
        null_rmses.append(rmse_null)
        
        logger.debug(f"Fold {fold_idx}: Trained RMSE={rmse_trained:.4f}, Null RMSE={rmse_null:.4f}")

    if not trained_rmses:
        raise ValueError("No valid folds completed for comparison.")

    # Statistical Test: Paired t-test on RMSEs
    # Hypothesis: Trained RMSE < Null RMSE (one-tailed)
    # We test if the difference (Null - Trained) > 0
    differences = np.array(null_rmses) - np.array(trained_rmses)
    
    t_stat, p_value = stats.ttest_rel(null_rmses, trained_rmses)
    
    # Calculate improvement percentage
    mean_trained_rmse = np.mean(trained_rmses)
    mean_null_rmse = np.mean(null_rmses)
    improvement_pct = ((mean_null_rmse - mean_trained_rmse) / mean_null_rmse) * 100
    
    # Bootstrapping for R² Confidence Intervals
    # Combine all predictions from all folds to estimate distribution
    # We need to reconstruct full predictions for the whole dataset via CV
    try:
        # Re-run CV to get full out-of-fold predictions for R² bootstrap
        y_pred_full_trained = cross_val_predict(model, X, y, cv=n_splits)
        y_pred_full_null = np.full_like(y, np.mean(y)) # Null is constant for all
        
        # Calculate full set R²
        full_r2_trained = r2_score(y, y_pred_full_trained)
        full_r2_null = r2_score(y, y_pred_full_null)
        
        # Bootstrap CI for R²
        boot_results = bootstrap_confidence_intervals(y, y_pred_full_trained, metric='r2', n_bootstraps=1000)
        ci_lower = boot_results['ci_lower']
        ci_upper = boot_results['ci_upper']
        
    except Exception as e:
        logger.warning(f"Bootstrapping failed: {e}. Using fold averages as point estimates.")
        ci_lower = None
        ci_upper = None

    return {
        "model_name": model_name,
        "n_splits": n_splits,
        "fold_metrics": {
            "trained_r2": trained_r2s,
            "trained_rmse": trained_rmses,
            "null_r2": null_r2s,
            "null_rmse": null_rmses
        },
        "statistical_test": {
            "test": "paired_t_test",
            "statistic": float(t_stat),
            "p_value": float(p_value),
            "is_significant": bool(p_value < 0.05),
            "null_hypothesis": "No difference in RMSE between models"
        },
        "summary": {
            "mean_trained_rmse": float(mean_trained_rmse),
            "mean_null_rmse": float(mean_null_rmse),
            "improvement_pct": float(improvement_pct),
            "improvement_threshold_met": bool(improvement_pct > 20.0),
            "full_r2_trained": float(full_r2_trained) if 'full_r2_trained' in locals() else None,
            "full_r2_null": float(full_r2_null) if 'full_r2_null' in locals() else None
        },
        "confidence_intervals": {
            "r2": {
                "point_estimate": float(full_r2_trained) if 'full_r2_trained' in locals() else None,
                "ci_95_lower": float(ci_lower) if ci_lower is not None else None,
                "ci_95_upper": float(ci_upper) if ci_upper is not None else None
            }
        }
    }

def main():
    """
    Main entry point for T024: Null Model Comparison.
    Loads data, performs comparison, and writes results to data/validation/null_model_comparison.json.
    """
    ensure_dirs()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Load preprocessed data (assuming it's been generated by T015/T016)
        # We need to load the specific target column used in training
        # For this task, we assume 'langmuir_capacity' as per T021 context, 
        # but we can make it configurable or detect from model metrics.
        
        data_path = Path("data/processed/curated_data.csv")
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}. Please run preprocessing first.")
            sys.exit(1)
        
        df = pd.read_csv(data_path)
        
        # Identify target and features
        # Assuming the standard feature set and a specific target. 
        # In a real scenario, we might read the target from a config or the model file.
        # Here we default to 'langmuir_capacity' if available, else first numeric column.
        target_col = 'langmuir_capacity'
        if target_col not in df.columns:
            logger.warning(f"Target {target_col} not found. Selecting first available numeric target.")
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            target_col = [c for c in numeric_cols if c not in ['material_id', 'descriptor_hash']][0]
        
        logger.info(f"Using target column: {target_col}")
        
        X = df.drop(columns=[target_col, 'material_id', 'descriptor_hash', 'adsorbent_structure_id'], errors='ignore').values
        y = df[target_col].values
        
        # Load the best trained model
        # We need to know which model was best. T023 saves model_metrics.json
        metrics_path = Path("data/results/model_metrics.json")
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            # Find best model by R2
            best_model_name = max(metrics['models'], key=lambda m: m['r2'])['model_name']
            logger.info(f"Best model identified from metrics: {best_model_name}")
        else:
            # Fallback: try to load a generic model or train a quick one
            logger.warning("model_metrics.json not found. Training a quick RF model for comparison.")
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
            model.fit(X, y)
            best_model_name = "RandomForest"
            model_name = best_model_name
        
        # If we loaded from file, load it
        if 'best_model_name' in locals() and 'metrics' in locals():
            model_path = Path(f"trained_models/{best_model_name}.pkl")
            if model_path.exists():
                import joblib
                model = joblib.load(model_path)
                model_name = best_model_name
            else:
                logger.warning(f"Model file {model_path} not found. Training a new instance for comparison.")
                # Re-train a simple version for the sake of the test
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(n_estimators=50, random_state=42)
                model.fit(X, y)
                model_name = "RandomForest"

        # Run the comparison
        results = run_cross_fold_comparison(X, y, model_name, model)
        
        # Save results
        output_path = Path("data/validation/null_model_comparison.json")
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results written to {output_path}")
        logger.info(f"Improvement: {results['summary']['improvement_pct']:.2f}%")
        logger.info(f"Statistical Significance (p < 0.05): {results['statistical_test']['is_significant']}")
        
        if not results['statistical_test']['is_significant']:
            logger.warning("Null model comparison did not show statistically significant improvement.")
        
    except Exception as e:
        logger.error(f"Error during null model comparison: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
