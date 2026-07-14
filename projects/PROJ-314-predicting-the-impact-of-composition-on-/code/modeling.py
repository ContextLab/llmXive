import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.dummy import DummyRegressor
import os

from . import logger

def prepare_splits(df: pd.DataFrame, target_col: str = 'weibull_modulus', 
                   stratify_col: str = 'primary_anion_cation_group', 
                   test_size: float = 0.2, random_state: int = 42):
    """
    Prepare stratified splits for training and testing.
    
    Args:
        df: Input DataFrame with features and target
        target_col: Name of the target column
        stratify_col: Column to use for stratification
        test_size: Fraction of data to use for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test, split_info)
    """
    logger.info(f"Preparing data splits with test_size={test_size}")
    
    # Drop rows with missing target
    df_clean = df.dropna(subset=[target_col])
    logger.info(f"Cleaned dataset size: {len(df_clean)}")
    
    X = df_clean.drop(columns=[target_col])
    y = df_clean[target_col]
    
    # Check if stratification column exists and has enough classes
    if stratify_col in df_clean.columns:
        class_counts = df_clean[stratify_col].value_counts()
        min_class_count = class_counts.min()
        
        if min_class_count >= 2:  # Need at least 2 per class for split
            logger.info(f"Using stratified split based on '{stratify_col}'")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, 
                stratify=df_clean[stratify_col]
            )
            split_info = {
                'method': 'stratified',
                'stratify_column': stratify_col,
                'class_distribution': class_counts.to_dict(),
                'train_size': len(X_train),
                'test_size': len(X_test)
            }
        else:
            logger.warning(f"Stratification column '{stratify_col}' has classes with < 2 samples. Using random split.")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            split_info = {
                'method': 'random',
                'reason': 'Insufficient samples per class for stratification',
                'train_size': len(X_train),
                'test_size': len(X_test)
            }
    else:
        logger.warning(f"Stratification column '{stratify_col}' not found. Using random split.")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        split_info = {
            'method': 'random',
            'reason': f"Column '{stratify_col}' not found",
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
        
    return X_train, X_test, y_train, y_test, split_info

def train_models(X_train, y_train, cv_folds=5, random_state=42):
    """
    Train Random Forest and Gradient Boosting models with cross-validation.
    
    Args:
        X_train: Training features
        y_train: Training targets
        cv_folds: Number of cross-validation folds
        random_state: Random seed
        
    Returns:
        Dictionary of trained models and their CV scores
    """
    logger.info("Training models with cross-validation")
    
    # Define models with constrained hyperparameters for runtime
    models = {
        'RandomForest': RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=random_state
        )
    }
    
    cv_results = {}
    
    for name, model in models.items():
        logger.info(f"Training {name}...")
        
        # Cross-validation scores
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, 
                                  scoring='neg_mean_absolute_error')
        cv_mae = -cv_scores.mean()
        cv_std = cv_scores.std()
        
        # Fit the model on full training data
        model.fit(X_train, y_train)
        
        cv_results[name] = {
            'cv_mae': float(cv_mae),
            'cv_std': float(cv_std),
            'model': model
        }
        
        logger.info(f"{name} CV MAE: {cv_mae:.4f} (+/- {cv_std:.4f})")
        
    return cv_results

def evaluate_models(models_cv_results, X_test, y_test, baseline_type='mean'):
    """
    Evaluate trained models against test set and baseline.
    
    Args:
        models_cv_results: Dictionary from train_models containing fitted models and CV results
        X_test: Test features
        y_test: Test targets
        baseline_type: Type of baseline ('mean' or 'median')
        
    Returns:
        Dictionary containing metrics for all models and baseline
    """
    logger.info("Evaluating models on test set")
    
    results = {
        'baseline': {},
        'models': {},
        'comparison': {}
    }
    
    # Evaluate baseline (global mean/median predictor)
    baseline_pred = np.full_like(y_test, y_test.mean())
    baseline_mae = mean_absolute_error(y_test, baseline_pred)
    baseline_r2 = r2_score(y_test, baseline_pred)
    
    results['baseline'] = {
        'type': baseline_type,
        'value': float(y_test.mean()),
        'mae': float(baseline_mae),
        'r2': float(baseline_r2),
        'description': 'Predicts global mean of training set'
    }
    
    logger.info(f"Baseline ({baseline_type}): MAE={baseline_mae:.4f}, R²={baseline_r2:.4f}")
    
    # Evaluate each model
    best_model_name = None
    best_mae = float('inf')
    
    for name, cv_data in models_cv_results.items():
        model = cv_data['model']
        y_pred = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        results['models'][name] = {
            'mae': float(mae),
            'r2': float(r2),
            'cv_mae': cv_data['cv_mae'],
            'cv_std': cv_data['cv_std'],
            'improvement_over_baseline_mae': float(baseline_mae - mae),
            'improvement_over_baseline_pct': float((baseline_mae - mae) / baseline_mae * 100)
        }
        
        logger.info(f"{name}: MAE={mae:.4f}, R²={r2:.4f}, Improvement over baseline: {mae:.2f}%")
        
        # Track best model
        if mae < best_mae:
            best_mae = mae
            best_model_name = name
    
    results['comparison'] = {
        'best_model': best_model_name,
        'best_mae': float(best_mae),
        'baseline_mae': float(baseline_mae),
        'best_improvement_pct': float((baseline_mae - best_mae) / baseline_mae * 100)
    }
    
    return results

def run_permutation_test(model, X, y, n_permutations=1000, random_state=42):
    """
    Perform permutation test to assess model significance.
    
    Args:
        model: Trained model to test
        X: Features
        y: Target
        n_permutations: Number of permutations
        random_state: Random seed
        
    Returns:
        Dictionary with p-value and test results
    """
    logger.info(f"Running permutation test with {n_permutations} permutations")
    
    np.random.seed(random_state)
    
    # Calculate original score
    original_score = mean_absolute_error(y, model.predict(X))
    
    # Permutation scores
    perm_scores = []
    for i in range(n_permutations):
        y_perm = y.sample(frac=1, random_state=random_state + i).reset_index(drop=True)
        perm_score = mean_absolute_error(y_perm, model.predict(X))
        perm_scores.append(perm_score)
    
    perm_scores = np.array(perm_scores)
    
    # Calculate p-value: proportion of permuted scores <= original score
    # (lower MAE is better, so we count how often permuted is as good or better)
    p_value = np.sum(perm_scores <= original_score) / n_permutations
    
    result = {
        'original_mae': float(original_score),
        'permuted_mae_mean': float(perm_scores.mean()),
        'permuted_mae_std': float(perm_scores.std()),
        'p_value': float(p_value),
        'n_permutations': n_permutations,
        'significant': p_value < 0.05,
        'threshold': 0.05
    }
    
    logger.info(f"Permutation test p-value: {p_value:.4f} ({'Significant' if p_value < 0.05 else 'Not significant'})")
    
    return result

def main():
    """
    Main entry point for model evaluation pipeline.
    This function is intended to be called by a higher-level script or CLI.
    """
    logger.info("Starting model evaluation pipeline")
    
    # This would typically load data and models from previous steps
    # For now, we define the functions that can be imported and used
    pass

if __name__ == "__main__":
    main()
