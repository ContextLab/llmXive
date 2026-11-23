import os
import sys
import json
import logging
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, LeaveOneOut, cross_val_score
from sklearn.linear_model import LinearRegression, ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor
from scipy.stats import ttest_rel
import psutil

# Import local utilities and exceptions
from logging_config import setup_logger, handle_power_warning
from exceptions import DataInsufficientError, PowerWarning
from config import get_config, get_path
from memory_monitor import update_peak_memory, get_peak_memory_mb, reset_peak_memory, log_peak_memory, final_log

logger = setup_logger(__name__)

# Permutation test constant
PERMUTATION_ITERATIONS = 10000

def load_cleaned_data():
    """Load the cleaned dataset from data/processed/dataset_cleaned.csv."""
    config = get_config()
    data_path = get_path(config, "processed", "dataset_cleaned.csv")
    if not os.path.exists(data_path):
        raise DataInsufficientError(f"Cleaned dataset not found at {data_path}. Run 02_preprocess.py first.")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} samples from {data_path}")
    return df

def prepare_features(df):
    """Separate features (X) and target (y) from the dataframe."""
    # Target is log_D
    target_col = "log_D"
    if target_col not in df.columns:
        raise DataInsufficientError(f"Target column '{target_col}' not found in dataset.")
    
    # Features are all columns except target and metadata (structure, composition)
    # Based on schema: composition, structure, log_D, atomic_radius_variance, VEC, 
    # electronegativity_spread, mixing_entropy, inv_temperature, microstructure_controlled, single_crystal
    feature_cols = [
        "atomic_radius_variance", "VEC", "electronegativity_spread", 
        "mixing_entropy", "inv_temperature"
    ]
    
    # Check if required feature columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise DataInsufficientError(f"Missing feature columns: {missing_cols}")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    logger.info(f"Prepared features: {feature_cols}")
    logger.info(f"Feature matrix shape: {X.shape}, Target shape: {y.shape}")
    return X, y, feature_cols

def train_models(X, y, feature_cols):
    """Train RF, XGBoost, Elastic Net, and Linear Regression models."""
    # Load split strategy from split_config.json
    config = get_config()
    split_config_path = get_path(config, "processed", "split_config.json")
    if not os.path.exists(split_config_path):
        raise DataInsufficientError(f"Split config not found at {split_config_path}. Run 02_preprocess.py first.")
    
    with open(split_config_path, 'r') as f:
        split_config = json.load(f)
    
    strategy = split_config.get("strategy", "80/20")
    n_samples = len(y)
    
    logger.info(f"Using split strategy: {strategy} (N={n_samples})")
    
    # Determine train/test split
    if strategy == "LOOCV":
        logger.warning(f"Sample size {n_samples} < 30. Using LOOCV.")
        warnings.warn(PowerWarning(f"Sample size {n_samples} is small (<30). Using LOOCV strategy."))
        # For LOOCV, we'll do cross-validation but also need a holdout for final evaluation
        # We'll use the last sample as test, rest as train for the final model comparison
        # However, LOOCV implies using all but one for training. For the final report, 
        # we'll train on all but one and test on that one, but for model selection we use CV.
        # To be consistent with the "same split" requirement for baseline:
        # We'll use the first n-1 as train, last 1 as test for the final comparison.
        train_idx = list(range(n_samples - 1))
        test_idx = [n_samples - 1]
    else:
        # 80/20 split
        train_idx, test_idx = train_test_split(
            np.arange(len(y)), test_size=0.2, random_state=config.get("random_seed", 42)
        )
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Define models
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=100, max_depth=5, random_state=config.get("random_seed", 42)
        ),
        "XGBoost": XGBRegressor(
            n_estimators=100, max_depth=3, random_state=config.get("random_seed", 42),
            verbosity=0, n_jobs=1
        ),
        "ElasticNet": ElasticNet(
            alpha=0.1, random_state=config.get("random_seed", 42), max_iter=1000
        ),
        "LinearRegression": LinearRegression()  # Unregularized OLS baseline
    }
    
    # Grid search for hyperparameters (constrained as per spec)
    # We'll do a simple grid search using cross-validation on the training set
    best_model_name = None
    best_cv_score = -np.inf
    best_model = None
    
    # For LOOCV, use LeaveOneOut() for CV; otherwise use 5-fold
    cv = LeaveOneOut() if strategy == "LOOCV" else 5
    
    model_configs = {
        "RandomForest": [
            {"n_estimators": 100, "max_depth": 5},
            {"n_estimators": 100, "max_depth": 10},
            {"n_estimators": 200, "max_depth": 5},
            {"n_estimators": 200, "max_depth": 10}
        ],
        "XGBoost": [
            {"n_estimators": 100, "max_depth": 3},
            {"n_estimators": 100, "max_depth": 5}
        ],
        "ElasticNet": [
            {"alpha": 0.1},
            {"alpha": 1.0}
        ]
    }
    
    logger.info("Starting grid search for hyperparameters...")
    
    for model_name, configs in model_configs.items():
        for config_params in configs:
            model = models[model_name]
            # Update model parameters
            for key, value in config_params.items():
                setattr(model, key, value)
            
            # Cross-validation
            scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='r2')
            mean_score = np.mean(scores)
            
            logger.info(f"{model_name} (n_estimators={config_params.get('n_estimators', 'N/A')}, "
                        f"max_depth={config_params.get('max_depth', 'N/A')}, "
                        f"alpha={config_params.get('alpha', 'N/A')}): CV R² = {mean_score:.4f}")
            
            if mean_score > best_cv_score:
                best_cv_score = mean_score
                best_model_name = model_name
                best_model = model
    
    # Train the best model on the full training set
    best_model.fit(X_train, y_train)
    logger.info(f"Best model: {best_model_name} with CV R² = {best_cv_score:.4f}")
    
    # Train the Linear Regression baseline on the SAME split
    baseline_model = LinearRegression()
    baseline_model.fit(X_train, y_train)
    logger.info("Trained Linear Regression baseline on the same split.")
    
    # Evaluate models on test set
    y_pred_best = best_model.predict(X_test)
    y_pred_baseline = baseline_model.predict(X_test)
    
    r2_best = r2_score(y_test, y_pred_best)
    rmse_best = np.sqrt(mean_squared_error(y_test, y_pred_best))
    mae_best = mean_absolute_error(y_test, y_pred_best)
    
    r2_baseline = r2_score(y_test, y_pred_baseline)
    rmse_baseline = np.sqrt(mean_squared_error(y_test, y_pred_baseline))
    mae_baseline = mean_absolute_error(y_test, y_pred_baseline)
    
    logger.info(f"Best Model ({best_model_name}) - Test R²: {r2_best:.4f}, RMSE: {rmse_best:.4f}, MAE: {mae_best:.4f}")
    logger.info(f"Baseline Model (Linear) - Test R²: {r2_baseline:.4f}, RMSE: {rmse_baseline:.4f}, MAE: {mae_baseline:.4f}")
    
    # Perform permutation test (10,000 iterations)
    logger.info(f"Starting permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    p_value = perform_permutation_test(
        best_model, baseline_model, X_test, y_test, 
        n_iterations=PERMUTATION_ITERATIONS, random_state=config.get("random_seed", 42)
    )
    logger.info(f"Permutation test p-value: {p_value:.4f}")
    
    # Save models
    output_dir = get_path(config, "outputs", create=True)
    with open(os.path.join(output_dir, "best_model.pkl"), 'wb') as f:
        pickle.dump(best_model, f)
    with open(os.path.join(output_dir, "baseline_model.pkl"), 'wb') as f:
        pickle.dump(baseline_model, f)
    logger.info(f"Saved models to {output_dir}")
    
    # Prepare results
    results = {
        "best_model": best_model_name,
        "baseline_model": "LinearRegression",
        "r2": float(r2_best),
        "rmse": float(rmse_best),
        "mae": float(mae_best),
        "p_value": float(p_value),
        "split_strategy": strategy,
        "n_samples": n_samples,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "cv_r2_best": float(best_cv_score),
        "baseline_r2": float(r2_baseline)
    }
    
    # Save results
    results_path = os.path.join(output_dir, "model_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved model results to {results_path}")
    
    return best_model, baseline_model, results, feature_cols

def perform_permutation_test(best_model, baseline_model, X_test, y_test, n_iterations=10000, random_state=42):
    """
    Perform a permutation test comparing best ML model vs Linear Regression baseline.
    Null hypothesis: The best model's performance is not significantly better than baseline.
    """
    np.random.seed(random_state)
    
    # Calculate observed performance difference (best - baseline)
    y_pred_best = best_model.predict(X_test)
    y_pred_baseline = baseline_model.predict(X_test)
    
    # Use R² as the metric
    obs_diff = r2_score(y_test, y_pred_best) - r2_score(y_test, y_pred_baseline)
    
    logger.info(f"Observed performance difference (R²): {obs_diff:.4f}")
    
    # Generate null distribution by permuting labels
    # For each iteration, permute y_test, train both models on permuted data (or just evaluate on permuted labels)
    # Since we're comparing on the same test set, we'll permute the test labels and re-evaluate
    
    null_diffs = []
    for i in range(n_iterations):
        # Permute y_test
        y_permuted = y_test.copy()
        np.random.shuffle(y_permuted)
        
        # Evaluate both models on permuted labels
        # Note: In a true permutation test, we'd retrain, but for efficiency on the test set,
        # we evaluate the existing models on permuted labels to simulate the null
        pred_best_perm = best_model.predict(X_test)
        pred_base_perm = baseline_model.predict(X_test)
        
        # Calculate R² on permuted labels
        r2_best_perm = r2_score(y_permuted, pred_best_perm)
        r2_base_perm = r2_score(y_permuted, pred_base_perm)
        
        diff = r2_best_perm - r2_base_perm
        null_diffs.append(diff)
        
        if (i + 1) % 1000 == 0:
            logger.debug(f"Permutation iteration {i+1}/{n_iterations}")
    
    null_diffs = np.array(null_diffs)
    
    # Calculate p-value: proportion of null differences >= observed difference
    # One-tailed test: is best model significantly better?
    p_value = np.sum(null_diffs >= obs_diff) / n_iterations
    
    logger.info(f"Null distribution mean: {np.mean(null_diffs):.4f}, std: {np.std(null_diffs):.4f}")
    logger.info(f"P-value (one-tailed): {p_value:.4f}")
    
    return p_value

def main():
    """Main entry point for the training pipeline."""
    logger.info("Starting training pipeline (T015)...")
    reset_peak_memory()
    
    try:
        # Load data
        df = load_cleaned_data()
        
        # Prepare features
        X, y, feature_cols = prepare_features(df)
        
        # Train models and evaluate
        best_model, baseline_model, results, feature_cols = train_models(X, y, feature_cols)
        
        # Log final memory usage
        final_log()
        
        logger.info("Training pipeline completed successfully.")
        return 0
        
    except DataInsufficientError as e:
        logger.error(f"Data insufficient: {e}")
        handle_power_warning(e)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())