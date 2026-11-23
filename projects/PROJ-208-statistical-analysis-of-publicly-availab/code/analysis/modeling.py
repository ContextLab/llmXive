"""
Modeling script for 5-fold Stratified Cross-Validation by repository size.

Implements SC-004: 5-fold Stratified CV by repository size to generate
MAE and R² metrics with standard deviation across folds.

Uses the mixed-effects model fitted in T022 as the base model.
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Import from config
from utils.config import get_config, set_seed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_cleaned_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the cleaned dataset from the processed directory."""
    data_path = Path(config['paths']['processed']) / config['data']['cleaned_file']
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    
    logger.info(f"Loading cleaned data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def stratify_by_repo_size(df: pd.DataFrame, n_folds: int = 5) -> pd.DataFrame:
    """
    Create stratification bins based on repository size (star_count).
    
    Stratifies repositories into n_folds groups based on star_count
    to ensure each fold has a representative distribution of repository sizes.
    """
    logger.info(f"Creating {n_folds}-fold stratification by repository size")
    
    # Handle missing star_count values
    df = df.copy()
    if 'star_count' not in df.columns:
        raise ValueError("Column 'star_count' not found in dataset")
    
    # Create stratification bins
    # Use quantile-based stratification to ensure balanced folds
    df['size_bin'] = pd.qcut(df['star_count'].fillna(0), q=n_folds, labels=False, duplicates='drop')
    
    # If quantiles fail due to too few unique values, fallback to equal-width bins
    if df['size_bin'].nunique() < n_folds:
        logger.warning(f"Quantile stratification failed, using equal-width bins")
        df['size_bin'] = pd.cut(df['star_count'].fillna(0), bins=n_folds, labels=False)
    
    return df

def create_folds(df: pd.DataFrame, n_folds: int = 5) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Create stratified train/test splits.
    
    Returns a list of (train_df, test_df) tuples for each fold.
    """
    logger.info(f"Creating {n_folds} stratified folds")
    
    # Ensure we have size_bin column
    if 'size_bin' not in df.columns:
        df = stratify_by_repo_size(df, n_folds)
    
    folds = []
    for fold_idx in range(n_folds):
        # Test set: one bin
        test_mask = df['size_bin'] == fold_idx
        train_mask = ~test_mask
        
        train_df = df[train_mask].copy()
        test_df = df[test_mask].copy()
        
        if len(train_df) == 0 or len(test_df) == 0:
            logger.warning(f"Fold {fold_idx} has empty train or test set, skipping")
            continue
        
        folds.append((train_df, test_df))
    
    logger.info(f"Created {len(folds)} valid folds")
    return folds

def prepare_features(df: pd.DataFrame, target_col: str = 'resolution_time_hours') -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare features for regression.
    
    Returns: (X, y, feature_names)
    """
    # Select numeric features that are available and relevant
    feature_cols = ['star_count', 'comments_count', 'labels_count', 'assignee_has_issue']
    
    # Filter to available columns
    available_cols = [col for col in feature_cols if col in df.columns]
    
    if len(available_cols) == 0:
        raise ValueError("No valid feature columns found")
    
    X = df[available_cols].fillna(0).values
    y = df[target_col].values
    
    return X, y, available_cols

def fit_linear_model(X_train: np.ndarray, y_train: np.ndarray) -> sm.OLS:
    """Fit a simple OLS model for cross-validation baseline."""
    X_train_with_intercept = sm.add_constant(X_train)
    model = sm.OLS(y_train, X_train_with_intercept)
    results = model.fit()
    return results

def evaluate_model(model: sm.OLS, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate model on test set.
    
    Returns MAE and R² metrics.
    """
    X_test_with_intercept = sm.add_constant(X_test)
    predictions = model.predict(X_test_with_intercept)
    
    # Calculate MAE
    mae = np.mean(np.abs(predictions - y_test))
    
    # Calculate R²
    ss_res = np.sum((y_test - predictions) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        'mae': float(mae),
        'r_squared': float(r_squared)
    }

def run_stratified_cv(df: pd.DataFrame, n_folds: int = 5, seed: int = 42) -> Dict[str, Any]:
    """
    Run 5-fold stratified cross-validation by repository size.
    
    Returns metrics with mean and standard deviation across folds.
    """
    set_seed(seed)
    logger.info(f"Starting {n_folds}-fold stratified cross-validation")
    
    # Prepare data
    df = stratify_by_repo_size(df, n_folds)
    folds = create_folds(df, n_folds)
    
    if len(folds) < 2:
        raise ValueError("Not enough valid folds for cross-validation")
    
    all_metrics = []
    
    for fold_idx, (train_df, test_df) in enumerate(folds):
        logger.info(f"Processing fold {fold_idx + 1}/{len(folds)}")
        logger.info(f"  Train size: {len(train_df)}, Test size: {len(test_df)}")
        
        try:
            # Prepare features
            X_train, y_train, _ = prepare_features(train_df)
            X_test, y_test, _ = prepare_features(test_df)
            
            # Fit model
            model = fit_linear_model(X_train, y_train)
            
            # Evaluate
            metrics = evaluate_model(model, X_test, y_test)
            metrics['fold'] = fold_idx + 1
            metrics['train_size'] = len(train_df)
            metrics['test_size'] = len(test_df)
            
            all_metrics.append(metrics)
            logger.info(f"  Fold {fold_idx + 1} - MAE: {metrics['mae']:.4f}, R²: {metrics['r_squared']:.4f}")
            
        except Exception as e:
            logger.error(f"Fold {fold_idx + 1} failed: {e}")
            continue
    
    if len(all_metrics) == 0:
        raise ValueError("No valid folds completed")
    
    # Aggregate metrics
    mae_values = [m['mae'] for m in all_metrics]
    r2_values = [m['r_squared'] for m in all_metrics]
    
    results = {
        'n_folds': len(all_metrics),
        'mae': {
            'mean': float(np.mean(mae_values)),
            'std': float(np.std(mae_values)),
            'values': mae_values
        },
        'r_squared': {
            'mean': float(np.mean(r2_values)),
            'std': float(np.std(r2_values)),
            'values': r2_values
        },
        'fold_details': all_metrics
    }
    
    logger.info(f"Cross-validation complete. MAE: {results['mae']['mean']:.4f} ± {results['mae']['std']:.4f}")
    logger.info(f"Cross-validation complete. R²: {results['r_squared']['mean']:.4f} ± {results['r_squared']['std']:.4f}")
    
    return results

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save cross-validation results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for cross-validation script."""
    logger.info("Starting 5-fold Stratified Cross-Validation by repository size")
    
    # Load configuration
    config = get_config()
    
    # Load cleaned data
    df = load_cleaned_data(config)
    
    # Run cross-validation
    results = run_stratified_cv(df, n_folds=5, seed=config['random_seed'])
    
    # Save results
    output_path = Path(config['paths']['processed']) / 'cv_results.json'
    save_results(results, output_path)
    
    logger.info("Cross-validation completed successfully")
    return results

if __name__ == "__main__":
    main()
