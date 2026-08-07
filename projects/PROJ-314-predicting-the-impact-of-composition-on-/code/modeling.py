import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from typing import Dict, Any, List, Tuple, Optional
import os
import sys

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code import logger
else:
    from .. import logger

# Constants
DATA_RESULTS_DIR = Path("data/results")
DATA_PROCESSED_DIR = Path("data/processed")
MODEL_TARGET = "weibull_modulus"

def prepare_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Stratified split based on primary_anion_cation_group.
    If N < 50, falls back to hold-out (80/20) without stratification if stratification fails or not possible,
    though the task implies stratified split is the primary method.
    """
    strat_col = "primary_anion_cation_group"
    X = df.drop(columns=[MODEL_TARGET, strat_col] if strat_col in df.columns else [MODEL_TARGET])
    y = df[MODEL_TARGET]
    s = df[strat_col] if strat_col in df.columns else None

    if s is not None and df[strat_col].nunique() > 1:
        try:
            train_idx, test_idx = train_test_split(
                df.index, test_size=0.2, stratify=s, random_state=42
            )
            logger.info("Stratified split successful.")
        except Exception as e:
            logger.warning(f"Stratified split failed ({e}), falling back to random split.")
            train_idx, test_idx = train_test_split(
                df.index, test_size=0.2, random_state=42
            )
    else:
        logger.warning("Stratification column missing or single value. Using random split.")
        train_idx, test_idx = train_test_split(
            df.index, test_size=0.2, random_state=42
        )

    return X.iloc[train_idx], X.iloc[test_idx], y.iloc[train_idx], y.iloc[test_idx]

def train_models(X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
    """
    Train RF and GBM models with limited hyperparameter search.
    Returns models and validation scores.
    """
    models = {}
    cv_results = {}

    # RF
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    models['RandomForest'] = rf
    cv_scores_rf = cross_val_score(rf, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
    cv_results['RandomForest'] = {
        'mean_mae': -cv_scores_rf.mean(),
        'std_mae': cv_scores_rf.std()
    }

    # GBM
    gbm = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    gbm.fit(X_train, y_train)
    models['GradientBoosting'] = gbm
    cv_scores_gbm = cross_val_score(gbm, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
    cv_results['GradientBoosting'] = {
        'mean_mae': -cv_scores_gbm.mean(),
        'std_mae': cv_scores_gbm.std()
    }

    logger.info("Models trained successfully.")
    return models, cv_results

def evaluate_models(models: Dict[str, Any], X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
    """
    Evaluate models on test set and return metrics.
    """
    metrics = {}
    best_model_name = None
    best_mae = float('inf')

    for name, model in models.items():
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        metrics[name] = {'mae': mae, 'r2': r2}
        logger.info(f"{name} - MAE: {mae:.4f}, R2: {r2:.4f}")

        if mae < best_mae:
            best_mae = mae
            best_model_name = name

    metrics['best_model'] = best_model_name
    metrics['best_model_mae'] = best_mae
    return metrics

def run_baseline_predictor(df: pd.DataFrame, test_indices: List[int]) -> float:
    """
    Implements T028b: Create a simple model that predicts the global mean Weibull modulus
    for all test samples. Calculate and save its MAE to data/results/baseline_metrics.json.
    
    Args:
        df: The full processed dataset (to calculate global mean from training or full set).
            Typically, baseline is calculated on the training set mean, but the task says
            "global mean Weibull modulus for all test samples". We will calculate the mean
            of the training set (if available) or the full dataset if split is not provided.
            To be robust, we assume `df` passed here is the training set or the full dataset
            if split wasn't done yet. We will use the mean of the target in the provided `df`.
            If this function is called after split, it should receive the training set.
            However, the task signature implies it might just take the dataframe.
            Let's assume the standard ML practice: Baseline predicts the mean of the TRAINING set.
            We will calculate the mean from the provided `df` (assuming it's the training set
            or we need to split internally if not).
            
            To be safe and compliant with "global mean", we calculate the mean of the target
            variable available in the provided dataframe.
        
        test_indices: List of indices for the test set to predict.
    
    Returns:
        baseline_mae: The Mean Absolute Error of the baseline predictor.
    """
    # Calculate global mean from the provided dataframe (assumed to be training data or full data)
    # If the caller passes the full dataset, this is technically "data leakage" for a proper CV,
    # but the task asks for "global mean". We will calculate mean from the input df.
    # Ideally, this function receives the training split.
    if MODEL_TARGET not in df.columns:
        raise ValueError(f"Target column '{MODEL_TARGET}' not found in dataframe.")
    
    global_mean = df[MODEL_TARGET].mean()
    logger.info(f"Global mean Weibull modulus: {global_mean:.4f}")

    # Predict global mean for all test samples
    # We need to construct a prediction vector of the same length as the test set
    # Since we don't have the test dataframe here, just indices, we assume the caller
    # can map these or we return the metric based on the test set if passed.
    # The task description says: "Calculate and save its MAE".
    # This implies we need the actual test values to calculate MAE.
    # The function signature provided in the prompt for this task is:
    # `run_baseline_predictor()` in `code/modeling.py`.
    # It does not specify arguments. I will infer arguments based on context.
    # To calculate MAE, I need y_true and y_pred.
    # I will assume the function is called with the test set data or indices.
    # Let's adjust the signature to accept the test set data directly to be safe.
    # But the prompt says "Implement `run_baseline_predictor()`".
    # I will implement it to take `y_test` and `y_train` (or full df) to be precise.
    
    # Re-reading task: "predicts the global mean Weibull modulus for all test samples".
    # I will assume the caller passes the test set y values to calculate error.
    # I will modify the function to accept `y_test` and `y_train` (or df_train).
    
    # However, to strictly follow the "Implement ... in code/modeling.py" without changing
    # the public API surface too much, I will assume this function is called from `main`
    # where splits are available.
    
    # Let's assume the function signature is:
    # run_baseline_predictor(y_train: pd.Series, y_test: pd.Series)
    # This is the most logical way to calculate MAE without needing the whole dataframe.
    pass

# Overriding the previous pass with a concrete implementation that fits the pipeline
def run_baseline_predictor(y_train: pd.Series, y_test: pd.Series) -> float:
    """
    T028b Implementation:
    Predicts the global mean (from training set) for all test samples.
    Calculates MAE and saves to data/results/baseline_metrics.json.
    
    Args:
        y_train: Training target series (to calculate global mean).
        y_test: Test target series (to calculate error).
    
    Returns:
        baseline_mae (float): The MAE of the baseline predictor.
    """
    global_mean = y_train.mean()
    logger.info(f"Baseline predictor using global mean: {global_mean:.4f}")
    
    y_pred = pd.Series([global_mean] * len(y_test), index=y_test.index)
    baseline_mae = mean_absolute_error(y_test, y_pred)
    
    logger.info(f"Baseline MAE: {baseline_mae:.4f}")
    
    # Save to data/results/baseline_metrics.json
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_RESULTS_DIR / "baseline_metrics.json"
    
    result = {
        "baseline_mae": float(baseline_mae),
        "global_mean_used": float(global_mean),
        "n_test_samples": len(y_test)
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Baseline metrics saved to {output_path}")
    return baseline_mae

def main():
    """
    Main entry point for the modeling pipeline.
    """
    logger.info("Starting Modeling Pipeline (T028b included).")
    
    # Load processed data
    data_path = DATA_PROCESSED_DIR / "processed_data.csv"
    if not data_path.exists():
        logger.error(f"Processed data not found at {data_path}. Run ingestion first.")
        return
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records.")
    
    # Prepare splits
    X_train, X_test, y_train, y_test = prepare_splits(df)
    
    # Train models
    models, cv_results = train_models(X_train, y_train)
    
    # Evaluate models
    metrics = evaluate_models(models, X_test, y_test)
    
    # T028b: Run Baseline Predictor
    baseline_mae = run_baseline_predictor(y_train, y_test)
    
    # Save metrics
    metrics_path = DATA_RESULTS_DIR / "model_metrics.json"
    metrics['baseline_mae'] = baseline_mae
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Modeling pipeline completed successfully.")

if __name__ == "__main__":
    main()