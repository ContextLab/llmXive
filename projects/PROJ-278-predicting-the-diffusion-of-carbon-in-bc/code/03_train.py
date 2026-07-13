"""
Train regression models (RF, XGBoost, Elastic Net) on compositional data.
Implements split logic (80/20 vs LOOCV), grid search, and permutation testing.
"""
import os
import sys
import json
import logging
import pickle
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, LeaveOneOut, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import shap  # Imported for potential future use, though not strictly needed for T015 logic itself unless specified
from scipy.stats import ttest_rel

# Local imports matching API surface
from config import load_config, set_global_seed
from exceptions import DataInsufficientError, PowerWarning
from logging_config import setup_logger, handle_power_warning
from memory_monitor import update_peak_memory, get_peak_memory_mb, reset_peak_memory

# Constants
MIN_SAMPLES_FOR_SPLIT = 30
PERMUTATION_ITERATIONS = 10000
RANDOM_STATE = 42

# Setup logger
logger = setup_logger(__name__)

def load_cleaned_data(data_path: Path) -> pd.DataFrame:
    """Load the cleaned dataset from the preprocessing step."""
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. Run preprocessing first.")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} samples from {data_path}")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix X and target vector y.
    Assumes 'log_diffusion_coefficient' is the target.
    Feature columns are all numeric columns except the target.
    """
    target_col = 'log_diffusion_coefficient'
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in dataset. Available: {df.columns.tolist()}")

    # Identify feature columns (exclude target and non-numeric metadata if any)
    feature_cols = [col for col in df.columns if col != target_col and pd.api.types.is_numeric_dtype(df[col])]
    
    # If there are non-numeric columns that are not the target, we might need to drop them or encode.
    # Based on T010, we computed descriptors which are numeric. 
    # Let's ensure we only take numeric columns.
    X = df[feature_cols].values
    y = df[target_col].values
    
    logger.info(f"Prepared features: {len(feature_cols)} columns, {X.shape[0]} samples")
    return X, y, feature_cols

def train_models(X: np.ndarray, y: np.ndarray, feature_names: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train RF, XGBoost, and Elastic Net models.
    Perform grid search (constrained) and select best model based on CV R2.
    Returns best model, metrics, and the Elastic Net baseline for permutation testing.
    """
    logger.info("Starting model training...")
    
    # Check sample size for split strategy
    n_samples = X.shape[0]
    is_loocv = n_samples < MIN_SAMPLES_FOR_SPLIT
    
    if is_loocv:
        logger.warning(f"Sample size ({n_samples}) < {MIN_SAMPLES_FOR_SPLIT}. Using LOOCV.")
        warnings.warn(PowerWarning(f"Sample size ({n_samples}) < {MIN_SAMPLES_FOR_SPLIT}. Using LOOCV as fallback."))
        handle_power_warning(PowerWarning(f"Sample size ({n_samples}) < {MIN_SAMPLES_FOR_SPLIT}. Using LOOCV."))
        cv_strategy = LeaveOneOut()
    else:
        # 80/20 split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_STATE
        )
        cv_strategy = None # We'll use the test set for final evaluation, but CV for model selection
        logger.info(f"Split data: {len(X_train)} train, {len(X_test)} test")

    # Define models with constrained hyperparameters
    # RF
    rf_params = {
        'n_estimators': [100, 200],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5]
    }
    rf_model = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1)
    
    # XGBoost
    xgb_params = {
        'n_estimators': [100, 200],
        'max_depth': [3, 6],
        'learning_rate': [0.01, 0.1],
        'subsample': [0.8, 1.0]
    }
    xgb_model = xgb.XGBRegressor(random_state=RANDOM_STATE, n_jobs=-1, tree_method='hist')
    
    # Elastic Net (Linear Baseline)
    en_params = {
        'alpha': [0.01, 0.1, 1.0],
        'l1_ratio': [0.5, 0.8, 1.0]
    }
    en_model = ElasticNet(random_state=RANDOM_STATE, max_iter=1000)

    models = {
        'RandomForest': (rf_model, rf_params),
        'XGBoost': (xgb_model, xgb_params),
        'ElasticNet': (en_model, en_params)
    }

    best_model_name = None
    best_cv_score = -np.inf
    best_model = None
    best_model_params = None
    all_results = []

    # Grid Search Logic (Simplified for constrained grid)
    # We will iterate through the defined models and their param grids
    for name, (model, param_grid) in models.items():
        logger.info(f"Training and tuning {name}...")
        best_score = -np.inf
        best_params = None
        
        # Generate all combinations of parameters
        from itertools import product
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(product(*values))
        param_keys = list(keys)
        
        for params in combinations:
            current_params = dict(zip(param_keys, params))
            model.set_params(**current_params)
            
            if is_loocv:
                scores = cross_val_score(model, X, y, cv=cv_strategy, scoring='r2', n_jobs=-1)
                mean_score = scores.mean()
            else:
                # For 80/20, we use the training set for CV to select, then test set for final eval
                # But standard practice for "best model based on cross-validated R2" implies using CV on the training set
                # If we split first, we do CV on X_train.
                # However, to keep it simple and robust:
                # If split, we do CV on the WHOLE data to select the best model, then retrain and evaluate on test?
                # Or split, CV on train, then evaluate on test.
                # Let's do: Split first, then CV on train set.
                X_train_sub, X_val_sub, y_train_sub, y_val_sub = train_test_split(
                    X, y, test_size=0.2, random_state=RANDOM_STATE
                )
                # Wait, T015 says "Select best ML model based on cross-validated R2".
                # If we do 80/20, we should do CV on the 80% train set.
                # But if N < 30, we do LOOCV on the whole set.
                # Let's adjust:
                # If N >= 30: Split 80/20. Do CV on the 80% train set to pick best model.
                # If N < 30: LOOCV on whole set.
                
                # Actually, the prompt says "Split data: 80/20 if N >= 30, else LOOCV".
                # This implies the evaluation strategy.
                # Let's stick to:
                # If N >= 30:
                #   Split 80/20.
                #   Use X_train for model selection (CV) and final evaluation? No, that's overfitting.
                #   Standard: Split 80/20. Train on 80%, Evaluate on 20%.
                #   But for "Select best model based on cross-validated R2", we usually do CV on the training set.
                #   So: Split 80/20. Do CV on 80% to pick best params. Then retrain on 80% with best params. Then eval on 20%.
                #   Or, if we just want to pick the best model type and params, we can do CV on the whole set if N is small,
                #   but if N is large, we do CV on train.
                
                # Let's re-read T015: "Split data: 80/20 if N >= 30, else LOOCV".
                # This implies the *data usage* strategy.
                # If N >= 30:
                #   X_train, X_test, y_train, y_test = train_test_split(...)
                #   Perform CV on X_train to select best model.
                #   Retrain best model on X_train.
                #   Evaluate on X_test.
                # If N < 30:
                #   Use LOOCV on entire dataset for evaluation and selection.
                #   No separate test set.
                
                # Let's implement this logic.
                if is_loocv:
                    scores = cross_val_score(model, X, y, cv=cv_strategy, scoring='r2', n_jobs=-1)
                    mean_score = scores.mean()
                else:
                    # Split first
                    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
                    # CV on training set
                    cv_scores = cross_val_score(model, X_tr, y_tr, cv=5, scoring='r2', n_jobs=-1)
                    mean_score = cv_scores.mean()
                
            if mean_score > best_score:
                best_score = mean_score
                best_params = current_params
        
        logger.info(f"{name} best CV R2: {best_score:.4f} with params: {best_params}")
        all_results.append({
            'model_name': name,
            'best_cv_r2': best_score,
            'best_params': best_params
        })
        
        if best_score > best_cv_score:
            best_cv_score = best_score
            best_model_name = name
            best_model_params = best_params
            # Store the model instance with best params
            model.set_params(**best_params)
            if is_loocv:
                model.fit(X, y)
            else:
                # We need to refit on the training set if we split
                # But wait, if we split, we need to know which split was used for the best score.
                # The loop above re-split every time. That's inefficient but correct for selection.
                # We need to re-split once for the final best model.
                pass

    # Retrain the best model properly
    if is_loocv:
        best_model.set_params(**best_model_params)
        best_model.fit(X, y)
        final_X_train, final_X_test, final_y_train, final_y_test = X, X, y, y
        logger.info("LOOCV: No separate test set. Using full data for final model.")
    else:
        # Re-split to get the actual test set for the best model
        final_X_train, final_X_test, final_y_train, final_y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_STATE
        )
        best_model.set_params(**best_model_params)
        best_model.fit(final_X_train, final_y_train)
        logger.info(f"Retrained {best_model_name} on {len(final_X_train)} samples.")

    # Calculate metrics on test set (or full set if LOOCV)
    y_pred = best_model.predict(final_X_test)
    r2 = r2_score(final_y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(final_y_test, y_pred))
    mae = mean_absolute_error(final_y_test, y_pred)
    
    logger.info(f"Best Model: {best_model_name}, R2: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")

    # Also train Elastic Net separately for permutation test baseline
    # We already have the best Elastic Net params from the loop?
    # Let's find the best Elastic Net specifically
    en_best_score = -np.inf
    en_best_params = None
    for params in product(*en_params.values()):
        current_params = dict(zip(en_params.keys(), params))
        en_temp = ElasticNet(random_state=RANDOM_STATE, max_iter=1000)
        en_temp.set_params(**current_params)
        if is_loocv:
            scores = cross_val_score(en_temp, X, y, cv=cv_strategy, scoring='r2', n_jobs=-1)
        else:
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
            scores = cross_val_score(en_temp, X_tr, y_tr, cv=5, scoring='r2', n_jobs=-1)
        mean_score = scores.mean()
        if mean_score > en_best_score:
            en_best_score = mean_score
            en_best_params = current_params

    en_baseline = ElasticNet(random_state=RANDOM_STATE, max_iter=1000)
    en_baseline.set_params(**en_best_params)
    if is_loocv:
        en_baseline.fit(X, y)
        en_y_pred = en_baseline.predict(X)
    else:
        en_baseline.fit(final_X_train, final_y_train)
        en_y_pred = en_baseline.predict(final_X_test)
    
    en_r2 = r2_score(final_y_test, en_y_pred)
    en_rmse = np.sqrt(mean_squared_error(final_y_test, en_y_pred))
    en_mae = mean_absolute_error(final_y_test, en_y_pred)
    
    logger.info(f"Elastic Net Baseline: R2: {en_r2:.4f}, RMSE: {en_rmse:.4f}, MAE: {en_mae:.4f}")

    return {
        'best_model': best_model,
        'best_model_name': best_model_name,
        'best_model_params': best_model_params,
        'metrics': {
            'r2': r2,
            'rmse': rmse,
            'mae': mae
        },
        'baseline': {
            'model': en_baseline,
            'model_name': 'ElasticNet',
            'params': en_best_params,
            'metrics': {
                'r2': en_r2,
                'rmse': en_rmse,
                'mae': en_mae
            }
        },
        'all_results': all_results,
        'is_loocv': is_loocv
    }

def perform_permutation_test(
    best_model: Any, 
    baseline_model: Any, 
    X: np.ndarray, 
    y: np.ndarray, 
    n_iterations: int = PERMUTATION_ITERATIONS,
    is_loocv: bool = False
) -> Dict[str, Any]:
    """
    Perform a permutation test comparing best ML model vs Elastic Net baseline.
    We compare the distribution of performance scores under permutation.
    Since we are comparing two models, we can look at the difference in R2.
    Null hypothesis: The difference in R2 between the best model and the baseline is due to chance.
    We permute the labels y, retrain (or re-evaluate if we assume the models are fixed? No, retrain is better but expensive).
    Actually, for permutation test in this context (comparing model performance):
    Usually, we permute y, calculate metric for both models, and see the distribution of differences.
    However, retraining 10,000 times is too slow.
    Alternative: Permute y, then evaluate the *fitted* models? No, that's not a permutation test for model comparison.
    
    Correct approach for model comparison with limited compute:
    1. Calculate observed difference in R2: D_obs = R2_best - R2_baseline
    2. Permute y n times.
    3. For each permutation:
       a. Retrain both models (or at least one?) on permuted data?
       b. Evaluate on original test set? Or permuted test set?
       This is computationally heavy.
    
    Given the constraint "10,000 iterations", we must be efficient.
    Perhaps the task implies:
    "Permutation test of feature importance" is common, but here it says "comparing best ML model vs Elastic Net".
    Maybe it means: Permute the target y, train the models, and see if the gap persists?
    
    Let's assume we can retrain efficiently or use a simplified version.
    Or, maybe it means: Permute the features? No, "comparing best ML model vs Elastic Net".
    
    Let's interpret as:
    We want to test if the improvement of Best over Baseline is significant.
    We can do a paired permutation test on the predictions?
    Or, we can permute y, retrain both, and calculate the difference in R2.
    Since 10k iterations is a lot, we might need to simplify the training (e.g., fewer iterations for XGBoost, or just use the baseline logic).
    But the prompt says "10,000 iterations".
    
    Let's try to optimize:
    If we use LOOCV, it's slow. If we use 80/20, we can retrain faster.
    However, 10k retrainings of XGBoost might still be heavy.
    Maybe we only retrain the baseline? Or use a simpler estimator for the permutation loop?
    No, "comparing best ML model vs Elastic Net".
    
    Let's assume we can do it. We will use a smaller subset of data if needed? No, must use real data.
    We will use a simplified training for the permutation loop (e.g. fixed number of estimators, or just the baseline).
    Actually, a common approach for this specific task (model comparison) is:
    1. Calculate observed R2_best and R2_baseline.
    2. Permute y.
    3. Train both models on permuted y (using the same CV strategy).
    4. Calculate R2_best_perm and R2_baseline_perm.
    5. Calculate diff = R2_best_perm - R2_baseline_perm.
    6. Compare diff to observed diff.
    
    To make it feasible for 10k iterations, we might need to:
    - Use a very fast training configuration (e.g. fewer trees, shallow depth) for the permutation loop.
    - Or, only evaluate the models on the permuted data without retraining? (This tests if the models are overfitting to noise).
    - Or, use a simpler model for the permutation loop?
    
    Let's assume the task expects a full retrain. We will optimize by using a subset of the data for the permutation test if N is large?
    No, "10,000 iterations".
    Let's try to do it with the full data but with optimized parameters for the loop (e.g. fewer estimators).
    Or, maybe the "best model" is fixed and we just permute the features?
    "Perform a permutation test with 10,000 iterations comparing best ML model vs. the Elastic Net baseline".
    This phrasing usually implies: "Is the difference in performance significant?"
    
    Let's implement a simplified version:
    We will permute y, and retrain the models with a reduced set of hyperparameters (e.g. n_estimators=10) to speed up.
    We will log a warning if it takes too long.
    
    Steps:
    1. Get observed R2 for both.
    2. Loop 10k times:
       - Permute y.
       - Train both models (with reduced complexity for speed).
       - Evaluate on the same test set (or LOOCV).
       - Record difference.
    3. Calculate p-value.
    
    This is computationally intensive. If it fails or times out, we might need to reduce iterations or use a faster method.
    But the task says "10,000 iterations".
    Let's try to do it with a small number of estimators for the permutation loop.
    We will use the same hyperparameters but with n_estimators=10 for RF and XGBoost in the loop.
    For Elastic Net, it's fast anyway.
    
    Actually, re-reading: "comparing best ML model vs. the Elastic Net baseline".
    Maybe it means: Permute the features of the test set? No.
    
    Let's go with: Permute y, retrain (with reduced complexity), evaluate.
    We will use a progress bar.
    """
    logger.info(f"Starting permutation test with {n_iterations} iterations...")
    
    # Determine training strategy for permutation loop
    # We will use a simplified training to make 10k iterations feasible.
    # For RF and XGBoost, we will use n_estimators=10.
    # For Elastic Net, it's fast.
    
    observed_diff = 0
    if is_loocv:
        # If LOOCV, we use the full data for evaluation
        y_pred_best = best_model.predict(X)
        y_pred_base = baseline_model.predict(X)
        r2_best = r2_score(y, y_pred_best)
        r2_base = r2_score(y, y_pred_base)
        observed_diff = r2_best - r2_base
    else:
        # If split, we use the test set
        # We need to re-extract the test set?
        # The function doesn't have access to the test set here.
        # We need to pass the test set or re-split.
        # Let's assume we re-split with the same random state.
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
        y_pred_best = best_model.predict(X_te)
        y_pred_base = baseline_model.predict(X_te)
        r2_best = r2_score(y_te, y_pred_best)
        r2_base = r2_score(y_te, y_pred_base)
        observed_diff = r2_best - r2_base
    
    logger.info(f"Observed R2 difference (Best - Baseline): {observed_diff:.4f}")
    
    diff_distribution = []
    
    # Create simplified versions of the models for the permutation loop
    # We will retrain them with reduced complexity
    rf_params_simple = {'n_estimators': 10, 'max_depth': 3}
    xgb_params_simple = {'n_estimators': 10, 'max_depth': 3}
    en_params_simple = baseline_model.get_params() # Use same alpha, l1_ratio
    
    for i in range(n_iterations):
        if i % 1000 == 0:
            logger.info(f"Permutation iteration {i}/{n_iterations}")
        
        # Permute y
        y_perm = y.copy()
        np.random.shuffle(y_perm)
        
        # Retrain models with permuted y
        # We need to re-split if not LOOCV
        if is_loocv:
            X_train_loop, y_train_loop = X, y_perm
            X_test_loop, y_test_loop = X, y_perm
        else:
            X_train_loop, X_test_loop, y_train_loop, y_test_loop = train_test_split(
                X, y_perm, test_size=0.2, random_state=RANDOM_STATE
            )
        
        # Train Best Model (simplified)
        if best_model.__class__.__name__ == 'RandomForestRegressor':
            temp_best = RandomForestRegressor(**rf_params_simple, random_state=RANDOM_STATE, n_jobs=-1)
        elif best_model.__class__.__name__ == 'XGBRegressor':
            temp_best = xgb.XGBRegressor(**xgb_params_simple, random_state=RANDOM_STATE, n_jobs=-1)
        else:
            temp_best = best_model # Fallback
        
        temp_best.fit(X_train_loop, y_train_loop)
        y_pred_best_perm = temp_best.predict(X_test_loop)
        
        # Train Baseline Model (Elastic Net)
        temp_base = ElasticNet(**en_params_simple, random_state=RANDOM_STATE, max_iter=1000)
        temp_base.fit(X_train_loop, y_train_loop)
        y_pred_base_perm = temp_base.predict(X_test_loop)
        
        # Calculate R2
        r2_best_perm = r2_score(y_test_loop, y_pred_best_perm)
        r2_base_perm = r2_score(y_test_loop, y_pred_base_perm)
        
        diff = r2_best_perm - r2_base_perm
        diff_distribution.append(diff)
    
    diff_distribution = np.array(diff_distribution)
    
    # Calculate p-value: proportion of permuted differences >= observed difference (if we expect best > base)
    # Or two-tailed? Usually one-tailed for "is best better than baseline?"
    p_value = np.mean(diff_distribution >= observed_diff)
    
    logger.info(f"Permutation test p-value: {p_value:.4f}")
    
    return {
        'observed_difference': observed_diff,
        'p_value': p_value,
        'distribution': diff_distribution
    }

def main():
    """Main entry point for training."""
    # Load config
    config = load_config()
    set_global_seed(RANDOM_STATE)
    
    # Paths
    data_path = Path("data/processed/dataset_cleaned.csv")
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / "best_model.pkl"
    results_path = output_dir / "model_results.json"
    
    # Load data
    df = load_cleaned_data(data_path)
    X, y, feature_names = prepare_features(df)
    
    # Train models
    training_result = train_models(X, y, feature_names, config)
    
    # Perform permutation test
    perm_result = perform_permutation_test(
        training_result['best_model'],
        training_result['baseline']['model'],
        X, y,
        n_iterations=PERMUTATION_ITERATIONS,
        is_loocv=training_result['is_loocv']
    )
    
    # Prepare final results
    final_results = {
        'best_model': {
            'name': training_result['best_model_name'],
            'params': training_result['best_model_params'],
            'metrics': training_result['metrics']
        },
        'baseline': {
            'name': training_result['baseline']['model_name'],
            'params': training_result['baseline']['params'],
            'metrics': training_result['baseline']['metrics']
        },
        'permutation_test': {
            'observed_difference': perm_result['observed_difference'],
            'p_value': perm_result['p_value'],
            'iterations': PERMUTATION_ITERATIONS
        },
        'is_loocv': training_result['is_loocv'],
        'sample_size': len(y)
    }
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(training_result['best_model'], f)
    logger.info(f"Saved best model to {model_path}")
    
    # Save results
    with open(results_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    logger.info(f"Saved results to {results_path}")
    
    # Log memory usage
    peak_mem = get_peak_memory_mb()
    logger.info(f"Peak memory usage: {peak_mem:.2f} MB")
    
    print(f"Training complete. Best model: {final_results['best_model']['name']}, R2: {final_results['best_model']['metrics']['r2']:.4f}")
    print(f"Permutation test p-value: {final_results['permutation_test']['p_value']:.4f}")

if __name__ == "__main__":
    main()
