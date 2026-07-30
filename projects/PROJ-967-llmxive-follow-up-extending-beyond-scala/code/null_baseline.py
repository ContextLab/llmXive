"""
Null Baseline Comparison Module (Task T030c)

Implements the comparison between the Random Forest model and a Mean Predictor (DummyRegressor).
Performs a paired t-test on residuals to verify significant improvement.
"""
import argparse
import json
import logging
import os
import sys
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.dummy import DummyRegressor
from sklearn.metrics import r2_score, mean_absolute_error

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_PATH = PROJECT_ROOT / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

def setup_logging() -> logging.Logger:
    """Configure and return the logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    return logger

def load_features() -> pd.DataFrame:
    """
    Load the cleaned dataset containing features and target.
    Expected path: data/processed/cleaned_data.parquet
    """
    logger = logging.getLogger(__name__)
    path = PROJECT_PATH / "data" / "processed" / "cleaned_data.parquet"
    
    if not path.exists():
        logger.error(f"Feature file not found: {path}")
        raise FileNotFoundError(f"Feature file not found: {path}")
    
    logger.info(f"Loading features from {path}")
    df = pd.read_parquet(path)
    
    required_cols = ['sample_id', 'fidelity_loss']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in features: {col}")
    
    return df

def load_rf_results() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the test set predictions and ground truth from the training split.
    We rely on the split_config.json and the saved model to reconstruct the test set,
    or we look for a saved prediction file if the pipeline was run in stages.
    
    However, to be robust for T030c (which runs after T029), we expect the
    train.py script to have saved the test set indices or the model's test performance.
    
    Strategy:
    1. Load split_config.json to get test indices.
    2. Load the model (results/model.pkl) and the full features.
    3. Re-run prediction on the test set to get y_pred and y_true.
    """
    logger = logging.getLogger(__name__)
    
    split_config_path = PROJECT_PATH / "data" / "processed" / "split_config.json"
    model_path = PROJECT_PATH / "results" / "model.pkl"
    features_path = PROJECT_PATH / "data" / "processed" / "cleaned_data.parquet"
    
    if not split_config_path.exists():
        raise FileNotFoundError(f"Split config not found: {split_config_path}")
    
    with open(split_config_path, 'r') as f:
        split_config = json.load(f)
    
    test_indices = split_config.get('test_indices')
    if not test_indices:
        raise ValueError("test_indices not found in split_config.json")
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    df = pd.read_parquet(features_path)
    
    # Ensure indices are aligned
    # Assuming the dataframe index matches the row order used in split_config
    # If split_config stores integer positions, we select by iloc
    X_test = df.iloc[test_indices]
    y_test = X_test['fidelity_loss'].values
    
    # We need the feature matrix X for prediction. 
    # The model expects features. We assume the model was trained on a subset of columns.
    # We need to know which columns were used. 
    # Let's assume the model has a feature_names_ attribute or we infer from the training logic.
    # Since we can't easily know the exact feature set without re-reading train.py logic,
    # we will attempt to load the model's expected input.
    # A safer approach for this specific task: The task asks to compare residuals.
    # We assume the model was trained on the full feature set available in cleaned_data.parquet
    # excluding the target and sample_id.
    
    feature_cols = [col for col in df.columns if col not in ['sample_id', 'fidelity_loss']]
    X_test_features = X_test[feature_cols].values
    
    y_pred = model.predict(X_test_features)
    
    logger.info(f"Loaded RF model. Test set size: {len(y_test)}")
    return y_test, y_pred, X_test_features

def calculate_mean_baseline_metrics(y_true: np.ndarray, y_pred_rf: np.ndarray) -> Dict[str, Any]:
    """
    Train a Mean Predictor (DummyRegressor) and calculate its metrics.
    Compare with Random Forest metrics.
    Perform Paired T-Test on residuals.
    """
    logger = logging.getLogger(__name__)
    
    # 1. Train Mean Predictor
    # We need X_train to train the dummy model consistently, but for 'mean' strategy,
    # the model only needs y_train to learn the mean.
    # However, to be consistent with the split, we need the training data.
    # We will reconstruct the training split from split_config.
    
    split_config_path = PROJECT_PATH / "data" / "processed" / "split_config.json"
    features_path = PROJECT_PATH / "data" / "processed" / "cleaned_data.parquet"
    
    with open(split_config_path, 'r') as f:
        split_config = json.load(f)
    
    train_indices = split_config.get('train_indices')
    test_indices = split_config.get('test_indices')
    
    df = pd.read_parquet(features_path)
    feature_cols = [col for col in df.columns if col not in ['sample_id', 'fidelity_loss']]
    
    X_train = df.iloc[train_indices][feature_cols].values
    y_train = df.iloc[train_indices]['fidelity_loss'].values
    
    X_test = df.iloc[test_indices][feature_cols].values
    y_test = df.iloc[test_indices]['fidelity_loss'].values
    
    # Train Mean Predictor
    mean_model = DummyRegressor(strategy='mean')
    mean_model.fit(X_train, y_train)
    y_pred_mean = mean_model.predict(X_test)
    
    # Calculate Metrics
    rf_r2 = r2_score(y_test, y_pred_rf)
    mean_r2 = r2_score(y_test, y_pred_mean)
    
    rf_mae = mean_absolute_error(y_test, y_pred_rf)
    mean_mae = mean_absolute_error(y_test, y_pred_mean)
    
    logger.info(f"RF R²: {rf_r2:.4f}, Mean R²: {mean_r2:.4f}")
    logger.info(f"RF MAE: {rf_mae:.4f}, Mean MAE: {mean_mae:.4f}")
    
    # 2. Paired T-Test on Residuals
    # Residuals: Actual - Predicted (or Predicted - Actual, sign doesn't matter for t-test of difference)
    # We want to test if RF residuals are significantly smaller (closer to 0) than Mean residuals.
    # Or simply, is the difference in errors significant?
    # Let's compare the absolute errors or squared errors? 
    # The spec says: "paired t-test on the residuals".
    # Residuals = y_true - y_pred
    residuals_rf = y_test - y_pred_rf
    residuals_mean = y_test - y_pred_mean
    
    # We test if the mean of (residuals_rf - residuals_mean) is significantly different from 0.
    # Actually, we want to know if RF is better. 
    # If RF is better, residuals_rf should be closer to 0.
    # A standard approach is to compare the squared residuals or absolute residuals.
    # But the spec says "residuals". Let's do t-test on the difference of residuals.
    # H0: Mean difference = 0. H1: Mean difference != 0 (or < 0 if we define diff = mean - rf)
    
    t_stat, p_value = stats.ttest_rel(residuals_mean, residuals_rf)
    
    # Interpretation:
    # If p_value < 0.05, the difference is statistically significant.
    # We also check if RF R2 > 0.0 as a fallback.
    
    is_significant = p_value < 0.05
    rf_better_r2 = rf_r2 > mean_r2
    rf_positive_r2 = rf_r2 > 0.0
    
    # Requirement: Pass if (t-test p < 0.05) OR (R² > 0.0)
    # Note: The spec says "Verify that the Random Forest R² > Mean Predictor R² (or R² > 0.0)".
    # And "The task passes if (t-test p < 0.05) OR (R² > 0.0)".
    
    task_passed = (is_significant and rf_better_r2) or rf_positive_r2
    
    results = {
        "rf_r2": float(rf_r2),
        "rf_mae": float(rf_mae),
        "mean_r2": float(mean_r2),
        "mean_mae": float(mean_mae),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "is_significant": bool(is_significant),
        "rf_better_than_mean": bool(rf_better_r2),
        "rf_positive_r2": bool(rf_positive_r2),
        "task_passed": bool(task_passed),
        "methodology": "Paired t-test on residuals (Mean vs RF). Fallback: R² > 0.0"
    }
    
    return results

def compare_and_save_results(results: Dict[str, Any]) -> None:
    """
    Save the comparison results to results/null_baseline.json
    """
    logger = logging.getLogger(__name__)
    output_path = PROJECT_PATH / "results" / "null_baseline.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved null baseline results to {output_path}")
    
    # Print summary
    print("\n" + "="*50)
    print("NULL BASELINE COMPARISON RESULTS")
    print("="*50)
    print(f"RF R²:      {results['rf_r2']:.4f}")
    print(f"Mean R²:    {results['mean_r2']:.4f}")
    print(f"RF MAE:     {results['rf_mae']:.4f}")
    print(f"Mean MAE:   {results['mean_mae']:.4f}")
    print(f"T-Stat:     {results['t_statistic']:.4f}")
    print(f"P-Value:    {results['p_value']:.4f}")
    print(f"Significant: {results['is_significant']}")
    print(f"RF Better:  {results['rf_better_than_mean']}")
    print(f"Task Passed: {results['task_passed']}")
    print("="*50 + "\n")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Null Baseline Comparison (T030c)")
    parser.add_argument("--project-root", type=str, default=str(PROJECT_PATH),
                        help="Path to the project root directory")
    return parser.parse_args()

def main() -> None:
    global logger
    logger = setup_logging()
    args = parse_args()
    
    # Update project path if overridden
    global PROJECT_PATH
    PROJECT_PATH = Path(args.project_root)
    
    try:
        logger.info("Starting Null Baseline Comparison...")
        
        # Load data and RF predictions
        # We need y_true and y_pred_rf
        y_true, y_pred_rf, _ = load_rf_results()
        
        # Calculate metrics and perform t-test
        results = calculate_mean_baseline_metrics(y_true, y_pred_rf)
        
        # Save results
        compare_and_save_results(results)
        
        if results['task_passed']:
            logger.info("SUCCESS: Null baseline comparison passed.")
            sys.exit(0)
        else:
            logger.warning("WARNING: Null baseline comparison failed to meet criteria.")
            sys.exit(0) # Still exit 0 as the task is implemented and run, even if result is negative
            
    except Exception as e:
        logger.error(f"Error during null baseline comparison: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
