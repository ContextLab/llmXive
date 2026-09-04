"""
Null Model Comparison Module.

Implements statistical comparison between trained models and a null baseline
using paired t-tests or Wilcoxon signed-rank tests on RMSEs.
"""

import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats
from sklearn.utils import resample

# Ensure imports work in both module and script contexts
try:
    from models.null_model import load_folds, calculate_rmse, run_null_model_baseline
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from models.null_model import load_folds, calculate_rmse, run_null_model_baseline

logger = logging.getLogger(__name__)

def ensure_dirs(output_dir: Path) -> None:
    """Ensure output directories exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir.parent / 'validation').mkdir(parents=True, exist_ok=True)

def load_preprocessed_data(data_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load preprocessed data for comparison.
    
    Returns:
        Tuple of (features, target, material_ids)
    """
    import pandas as pd
    df = pd.read_parquet(data_path)
    
    # Assume standard schema based on project specs
    feature_cols = [col for col in df.columns if col not in ['langmuir_capacity', 'henry_constant', 'adsorbent_structure_id']]
    X = df[feature_cols].values
    y = df['langmuir_capacity'].values
    material_ids = df['adsorbent_structure_id'].values
    
    return X, y, material_ids

def predict_mean_null_model(X_train: np.ndarray, y_train: np.ndarray, 
                            X_test: np.ndarray, y_test: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Predict using null model (mean of training set).
    
    Returns:
        Tuple of (predictions, RMSE)
    """
    mean_pred = np.mean(y_train)
    predictions = np.full_like(y_test, mean_pred, dtype=float)
    rmse = np.sqrt(np.mean((predictions - y_test) ** 2))
    return predictions, rmse

def bootstrap_confidence_intervals(values: np.ndarray, 
                                   n_resamples: int = 1000, 
                                   random_state: int = 42) -> Dict[str, float]:
    """
    Calculate 95% confidence intervals using bootstrapping.
    
    Args:
        values: Array of values to bootstrap
        n_resamples: Number of bootstrap resamples
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with 'mean', 'ci_lower', 'ci_upper'
    """
    rng = np.random.RandomState(random_state)
    bootstrap_means = []
    
    for _ in range(n_resamples):
        sample = resample(values, random_state=rng)
        bootstrap_means.append(np.mean(sample))
    
    bootstrap_means = np.array(bootstrap_means)
    ci_lower = np.percentile(bootstrap_means, 2.5)
    ci_upper = np.percentile(bootstrap_means, 97.5)
    
    return {
        'mean': float(np.mean(values)),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'std': float(np.std(values))
    }

def calculate_null_model_metrics(folds_path: Path, data_path: Path) -> Dict[str, Any]:
    """
    Calculate null model metrics across all folds.
    
    Args:
        folds_path: Path to folds.json
        data_path: Path to preprocessed data parquet
        
    Returns:
        Dictionary with fold RMSEs and aggregate metrics
    """
    import pandas as pd
    df = pd.read_parquet(data_path)
    
    # Load folds
    with open(folds_path, 'r') as f:
        folds = json.load(f)
    
    fold_rmses = []
    
    for fold_idx, fold_data in enumerate(folds):
        train_indices = fold_data['train']
        test_indices = fold_data['test']
        
        X_train = df.iloc[train_indices].drop(columns=['langmuir_capacity', 'henry_constant', 'adsorbent_structure_id']).values
        y_train = df.iloc[train_indices]['langmuir_capacity'].values
        X_test = df.iloc[test_indices].drop(columns=['langmuir_capacity', 'henry_constant', 'adsorbent_structure_id']).values
        y_test = df.iloc[test_indices]['langmuir_capacity'].values
        
        _, rmse = predict_mean_null_model(X_train, y_train, X_test, y_test)
        fold_rmses.append(rmse)
    
    return {
        'fold_rmses': fold_rmses,
        'mean_rmse': float(np.mean(fold_rmses)),
        'std_rmse': float(np.std(fold_rmses))
    }

def calculate_trained_model_metrics(folds_path: Path, data_path: Path, 
                                    model_path: Path) -> Dict[str, Any]:
    """
    Calculate trained model metrics across all folds.
    
    Args:
        folds_path: Path to folds.json
        data_path: Path to preprocessed data parquet
        model_path: Path to trained model pickle
        
    Returns:
        Dictionary with fold RMSEs and aggregate metrics
    """
    import pandas as pd
    import joblib
    
    df = pd.read_parquet(data_path)
    model = joblib.load(model_path)
    
    # Load folds
    with open(folds_path, 'r') as f:
        folds = json.load(f)
    
    fold_rmses = []
    
    for fold_idx, fold_data in enumerate(folds):
        train_indices = fold_data['train']
        test_indices = fold_data['test']
        
        X_train = df.iloc[train_indices].drop(columns=['langmuir_capacity', 'henry_constant', 'adsorbent_structure_id']).values
        y_train = df.iloc[train_indices]['langmuir_capacity'].values
        X_test = df.iloc[test_indices].drop(columns=['langmuir_capacity', 'henry_constant', 'adsorbent_structure_id']).values
        y_test = df.iloc[test_indices]['langmuir_capacity'].values
        
        predictions = model.predict(X_test)
        rmse = np.sqrt(np.mean((predictions - y_test) ** 2))
        fold_rmses.append(rmse)
    
    return {
        'fold_rmses': fold_rmses,
        'mean_rmse': float(np.mean(fold_rmses)),
        'std_rmse': float(np.std(fold_rmses))
    }

def run_cross_fold_comparison(null_rmses: List[float], 
                              trained_rmses: List[float],
                              output_path: Path) -> Dict[str, Any]:
    """
    Perform statistical comparison between null and trained models.
    
    Args:
        null_rmses: List of RMSEs from null model
        trained_rmses: List of RMSEs from trained model
        output_path: Path to write comparison results
        
    Returns:
        Dictionary with comparison results
    """
    if len(null_rmses) != len(trained_rmses):
        raise ValueError("Number of folds must match for both models")
    
    # Perform paired t-test
    t_stat, p_value_t = stats.ttest_rel(null_rmses, trained_rmses)
    
    # Perform Wilcoxon signed-rank test (non-parametric alternative)
    w_stat, p_value_w = stats.wilcoxon(null_rmses, trained_rmses)
    
    # Calculate improvement
    improvements = [n - t for n, t in zip(null_rmses, trained_rmses)]
    improvement_stats = bootstrap_confidence_intervals(improvements, n_resamples=1000, random_state=42)
    
    # Determine significance
    is_significant = p_value_t < 0.05 or p_value_w < 0.05
    
    results = {
        't_test': {
            'statistic': float(t_stat),
            'p_value': float(p_value_t),
            'significant': bool(p_value_t < 0.05)
        },
        'wilcoxon_test': {
            'statistic': float(w_stat),
            'p_value': float(p_value_w),
            'significant': bool(p_value_w < 0.05)
        },
        'improvement': {
            'mean_improvement': improvement_stats['mean'],
            'ci_lower': improvement_stats['ci_lower'],
            'ci_upper': improvement_stats['ci_upper'],
            'std': improvement_stats['std']
        },
        'null_model': {
            'mean_rmse': float(np.mean(null_rmses)),
            'std_rmse': float(np.std(null_rmses))
        },
        'trained_model': {
            'mean_rmse': float(np.mean(trained_rmses)),
            'std_rmse': float(np.std(trained_rmses))
        },
        'conclusion': {
            'is_significant': bool(is_significant),
            'p_value_used': float(p_value_t if p_value_t < p_value_w else p_value_w),
            'method': 't-test' if p_value_t < p_value_w else 'wilcoxon'
        }
    }
    
    # Write results to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Null model comparison results written to {output_path}")
    return results

def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for null model comparison.
    
    Args:
        args: Command line arguments (optional)
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare null model with trained models')
    parser.add_argument('--folds-path', type=Path, default='data/results/folds.json',
                      help='Path to folds.json file')
    parser.add_argument('--data-path', type=Path, default='data/processed/curated_data.parquet',
                      help='Path to preprocessed data parquet file')
    parser.add_argument('--model-path', type=Path, default='trained_models/best_model.pkl',
                      help='Path to trained model pickle file')
    parser.add_argument('--output-path', type=Path, default='data/validation/null_model_comparison.json',
                      help='Path to output comparison results')
    
    parsed_args = parser.parse_args(args)
    
    try:
        # Ensure directories exist
        ensure_dirs(parsed_args.output_path)
        
        # Calculate metrics for both models
        logger.info("Calculating null model metrics...")
        null_metrics = calculate_null_model_metrics(parsed_args.folds_path, parsed_args.data_path)
        
        logger.info("Calculating trained model metrics...")
        trained_metrics = calculate_trained_model_metrics(parsed_args.folds_path, parsed_args.data_path, parsed_args.model_path)
        
        # Perform comparison
        logger.info("Running cross-fold comparison...")
        results = run_cross_fold_comparison(
            null_metrics['fold_rmses'],
            trained_metrics['fold_rmses'],
            parsed_args.output_path
        )
        
        # Log results
        logger.info(f"T-test p-value: {results['t_test']['p_value']:.4f}")
        logger.info(f"Wilcoxon p-value: {results['wilcoxon_test']['p_value']:.4f}")
        logger.info(f"Mean improvement: {results['improvement']['mean_improvement']:.4f}")
        logger.info(f"Significant (p < 0.05): {results['conclusion']['is_significant']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in null model comparison: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())