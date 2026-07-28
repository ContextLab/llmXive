"""
Integration script for Training and Evaluation (T031).
Orchestrates the full pipeline: Load features -> Train Model -> Cross-Validation ->
Permutation Test -> Null Baseline Comparison -> Save Final Results.
"""
import argparse
import json
import logging
import os
import sys
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.dummy import DummyRegressor
from scipy import stats

# Import existing modules from the project API surface
from train import (
    setup_logging as train_setup_logging,
    load_features as train_load_features,
    prepare_data as train_prepare_data,
    train_and_evaluate as train_run_training,
    run_cross_validation as train_run_cv,
    calculate_permutation_pvalue as train_calc_perm_pvalue,
    save_results as train_save_results
)
from evaluate import (
    setup_logging as eval_setup_logging,
    load_features as eval_load_features,
    load_model as eval_load_model,
    calculate_metrics as eval_calc_metrics,
    calculate_baseline_mae as eval_calc_baseline_mae,
    calculate_permutation_pvalue as eval_calc_perm_pvalue,
    evaluate_model as eval_run_eval,
    save_results as eval_save_results
)
from null_baseline import (
    setup_logging as nb_setup_logging,
    load_features as nb_load_features,
    load_rf_results as nb_load_rf_results,
    calculate_mean_baseline_metrics as nb_calc_mean_baseline,
    compare_and_save_results as nb_compare_and_save
)

def setup_logging(log_file=None):
    """Configure logging for the integration script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger('integrate_train_eval')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    return logger

def ensure_directories(base_path):
    """Ensure required output directories exist."""
    data_processed = base_path / 'data' / 'processed'
    results = base_path / 'results'
    data_processed.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    return data_processed, results

def run_integration_pipeline(base_path, logger):
    """
    Execute the full training and evaluation pipeline.
    1. Load cleaned data (features + target).
    2. Train Random Forest (T027a, T027b).
    3. Save model (T027c).
    4. Run Cross-Validation (T028).
    5. Run Permutation Test (T030a).
    6. Run Null Baseline Comparison (T030c).
    7. Aggregate results and write to results/results.json (T031).
    """
    logger.info("Starting Integration Pipeline (T031)...")

    # Paths
    data_path = base_path / 'data' / 'processed'
    results_path = base_path / 'results'
    cleaned_data_path = data_path / 'cleaned_data.parquet'
    model_path = results_path / 'model.pkl'
    results_json_path = results_path / 'results.json'
    split_config_path = data_path / 'split_config.json'

    # Check dependencies
    if not cleaned_data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {cleaned_data_path}. "
                                "Please ensure T024 (fidelity_loss) has completed.")

    # 1. Load Features
    logger.info("Loading features from cleaned_data.parquet...")
    df = train_load_features(str(cleaned_data_path))
    
    # Identify target and features
    target_col = 'fidelity_loss'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Columns: {df.columns.tolist()}")
    
    feature_cols = [c for c in df.columns if c not in [target_col, 'sample_id']]
    X = df[feature_cols].values
    y = df[target_col].values

    logger.info(f"Data loaded: {len(df)} samples, {len(feature_cols)} features.")

    # 2. Prepare Data (Stratified Split)
    logger.info("Preparing data split (Quantile Binning for Stratification)...")
    
    # Quantile binning for stratification
    n_bins = 5
    y_bins = pd.qcut(y, q=n_bins, labels=False, duplicates='drop')
    
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, np.arange(len(y)),
        test_size=0.2,
        random_state=42,
        stratify=y_bins
    )

    # Save split config (T027a requirement)
    split_config = {
        "test_size": 0.2,
        "random_state": 42,
        "n_train": len(idx_train),
        "n_test": len(idx_test),
        "stratification_bins": n_bins
    }
    with open(split_config_path, 'w') as f:
        json.dump(split_config, f, indent=2)
    logger.info(f"Split configuration saved to {split_config_path}")

    # 3. Train Model (T027b)
    logger.info("Training Random Forest Regressor...")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2  # CPU-only
    )
    rf_model.fit(X_train, y_train)

    # 4. Save Model (T027c)
    logger.info(f"Saving model to {model_path}...")
    with open(model_path, 'wb') as f:
        pickle.dump(rf_model, f)
    logger.info("Model saved.")

    # 5. Cross-Validation (T028)
    logger.info("Running 5-Fold Stratified Cross-Validation...")
    cv_scores = train_run_cv(
        X, y, 
        n_splits=5, 
        random_state=42,
        model_type='rf',
        n_estimators=100,
        max_depth=None
    )
    cv_r2_mean = np.mean(cv_scores)
    cv_r2_std = np.std(cv_scores)
    logger.info(f"CV R²: {cv_r2_mean:.4f} (+/- {cv_r2_std:.4f})")

    # 6. Evaluate on Test Set (T029)
    logger.info("Evaluating on Test Set...")
    y_pred = rf_model.predict(X_test)
    test_r2 = r2_score(y_test, y_pred)
    test_mae = mean_absolute_error(y_test, y_pred)
    logger.info(f"Test R²: {test_r2:.4f}, Test MAE: {test_mae:.4f}")

    # 7. Permutation Test (T030a)
    logger.info("Running Permutation Test (n=1000)...")
    p_value = train_calc_perm_pvalue(
        X_test, y_test, rf_model, 
        n_permutations=1000, 
        random_state=42
    )
    logger.info(f"Permutation Test p-value: {p_value:.4f}")

    # 8. Null Baseline Comparison (T030c)
    logger.info("Running Null Baseline Comparison (Mean Predictor)...")
    
    # Train Mean Predictor on TRAIN set
    mean_pred = DummyRegressor(strategy='mean')
    mean_pred.fit(X_train, y_train)
    
    # Evaluate on TEST set
    y_pred_mean = mean_pred.predict(X_test)
    mean_r2 = r2_score(y_test, y_pred_mean)
    mean_mae = mean_absolute_error(y_test, y_pred_mean)
    
    # Statistical Significance Test (Paired T-Test on Residuals)
    residuals_rf = y_test - y_pred
    residuals_mean = y_test - y_pred_mean
    
    t_stat, t_p_value = stats.ttest_rel(residuals_mean, residuals_rf) # Positive t means RF is better (smaller residuals)
    
    logger.info(f"Mean Predictor - R²: {mean_r2:.4f}, MAE: {mean_mae:.4f}")
    logger.info(f"Paired T-Test (Residuals): t={t_stat:.4f}, p={t_p_value:.4f}")

    # 9. Aggregate Results
    results = {
        "task_id": "T031",
        "pipeline_status": "completed",
        "model_config": {
            "type": "RandomForestRegressor",
            "n_estimators": 100,
            "max_depth": None,
            "random_state": 42,
            "n_jobs": 2
        },
        "data_split": {
            "train_size": len(idx_train),
            "test_size": len(idx_test),
            "stratification_bins": 5
        },
        "cross_validation": {
            "r2_mean": float(cv_r2_mean),
            "r2_std": float(cv_r2_std)
        },
        "test_set_metrics": {
            "r2": float(test_r2),
            "mae": float(test_mae),
            "permutation_p_value": float(p_value)
        },
        "null_baseline": {
            "strategy": "mean",
            "r2": float(mean_r2),
            "mae": float(mean_mae),
            "comparison": {
                "r2_improvement": float(test_r2 - mean_r2),
                "mae_improvement": float(mean_mae - test_mae),
                "statistical_significance": {
                    "test": "paired_t_test_residuals",
                    "t_statistic": float(t_stat),
                    "p_value": float(t_p_value),
                    "significant_at_0.05": bool(t_p_value < 0.05)
                }
            }
        },
        "artifacts": {
            "model_path": str(model_path),
            "split_config_path": str(split_config_path),
            "results_path": str(results_json_path)
        }
    }

    # 10. Write Final Results (T031)
    logger.info(f"Writing final results to {results_json_path}...")
    with open(results_json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Integration Pipeline (T031) completed successfully.")
    return results

def parse_args():
    parser = argparse.ArgumentParser(description="T031: Integrate Training and Evaluation Pipeline")
    parser.add_argument(
        "--base-path", 
        type=str, 
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Base path of the project"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Optional log file path"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging(args.log_file)
    base_path = Path(args.base_path)
    
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)

    try:
        run_integration_pipeline(base_path, logger)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()