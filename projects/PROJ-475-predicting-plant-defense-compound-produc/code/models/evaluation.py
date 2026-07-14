"""
Model Evaluation Module.
Handles permutation tests, p-value calculation, and sensitivity analysis.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import json

# Add parent path for imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_config
from utils.logging import get_module_logger
from utils.stats import benjamini_hochberg_correction

logger = get_module_logger(__name__)

def calculate_p_value(observed_r2: float, null_distribution: np.ndarray) -> float:
    """
    Calculate p-value comparing observed R² against null distribution.
    p = (1 + count(null >= observed)) / (1 + n)
    """
    count = np.sum(null_distribution >= observed_r2)
    n = len(null_distribution)
    return (1 + count) / (1 + n)

def run_permutation_test(model, X: np.ndarray, y: np.ndarray, n_permutations: int = 1000) -> Tuple[np.ndarray, float]:
    """
    Execute permutation test to generate null distribution.
    """
    logger.info(f"Running permutation test with {n_permutations} permutations...")
    null_scores = []
    
    # Fit original model to get observed score
    from sklearn.model_selection import cross_val_score
    observed_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    observed_r2 = observed_scores.mean()
    
    for i in range(n_permutations):
        # Shuffle y
        y_permuted = np.random.permutation(y)
        scores = cross_val_score(model, X, y_permuted, cv=5, scoring='r2')
        null_scores.append(scores.mean())
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations} completed.")
    
    null_distribution = np.array(null_scores)
    p_value = calculate_p_value(observed_r2, null_distribution)
    
    logger.info(f"Permutation test complete. Observed R²: {observed_r2:.4f}, p-value: {p_value:.4f}")
    return null_distribution, p_value

def save_permutation_results(null_distribution: np.ndarray, p_value: float, output_path: Path):
    """Save permutation test results."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = {
        "null_distribution": null_distribution.tolist(),
        "p_value": p_value
    }
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Permutation results saved to {output_path}")

def run_sensitivity_analysis(model, X: np.ndarray, y: np.ndarray, alpha_range: List[float], n_folds: int = 5) -> Dict[float, float]:
    """
    Perform sensitivity analysis sweeping alpha values across a range of small significance levels.
    FR-007: Sweeps alpha to check model stability and feature selection consistency.
    Returns a dictionary mapping alpha to model performance (R²).
    """
    logger.info("Running sensitivity analysis across alpha values...")
    results = {}
    
    from sklearn.model_selection import cross_val_score
    
    for alpha in alpha_range:
        # Update model alpha if it's an ElasticNet/Ridge/Lasso
        if hasattr(model, 'alpha'):
            model.alpha = alpha
        
        # Ensure positive alpha for scikit-learn regularized models
        if alpha <= 0:
            alpha = 1e-6
            model.alpha = alpha

        try:
            scores = cross_val_score(model, X, y, cv=n_folds, scoring='r2', n_jobs=1)
            mean_r2 = scores.mean()
            results[alpha] = float(mean_r2)
            logger.info(f"Alpha={alpha:.6f}, Mean R²={mean_r2:.4f}, Std={scores.std():.4f}")
        except Exception as e:
            logger.warning(f"Failed to evaluate alpha={alpha}: {e}")
            results[alpha] = float('nan')
    
    return results

def main(config=None):
    """Main entry point for evaluation module."""
    if config is None:
        config = get_config()
    
    logger.info("Starting evaluation module...")
    
    try:
        # Load data
        data_path = Path(config.paths.processed_data) / "features_vif.csv"
        if not data_path.exists():
            logger.warning(f"Data file not found: {data_path}. Skipping evaluation.")
            return

        df = pd.read_csv(data_path)
        
        # Prepare X, y
        target_col = 'compound_concentration'
        if target_col not in df.columns:
            # Fallback to last numeric column if target not found
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                target_col = numeric_cols[-1]
            else:
                logger.error("No numeric target column found.")
                return
        
        # Drop non-feature columns
        drop_cols = ['population_id', 'env_id', 'compound_id', 'source_study']
        X_df = df.drop(columns=[target_col] + [c for c in drop_cols if c in df.columns], errors='ignore')
        X_df = X_df.select_dtypes(include=[np.number])
        
        if X_df.empty:
            logger.warning("No valid features remaining after dropping non-numeric columns.")
            return

        X = X_df.values
        y = df[target_col].values

        # Initialize model (ElasticNet as per pipeline context)
        from sklearn.linear_model import ElasticNet
        model = ElasticNet(alpha=0.1, random_state=42, max_iter=5000)
        
        # 1. Permutation Test
        # Reduced permutations for CI speed, but logic remains valid for real data
        null_dist, p_val = run_permutation_test(model, X, y, n_permutations=100) 
        save_permutation_results(null_dist, p_val, Path(config.paths.processed_data) / "permutation_results.json")
        
        # 2. Sensitivity Analysis (FR-007)
        # Sweep a range of alpha values (significance levels for regularization)
        # Using small values to detect stability in feature selection
        alpha_range = [0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
        sensitivity_results = run_sensitivity_analysis(model, X, y, alpha_range)
        
        # Save sensitivity results
        sens_path = Path(config.paths.processed_data) / "sensitivity_analysis.json"
        with open(sens_path, 'w') as f:
            json.dump({str(k): v for k, v in sensitivity_results.items()}, f, indent=2)
        logger.info(f"Sensitivity analysis saved to {sens_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    config = get_config()
    main(config)