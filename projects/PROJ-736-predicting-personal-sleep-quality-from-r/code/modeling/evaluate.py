"""
Evaluation module for model performance assessment.
Handles permutation tests, bootstrap resampling, and sensitivity analysis.
"""
import os
import sys
import json
import signal
import time
import numpy as np
from pathlib import Path
import logging
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, get_hyperparameter, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error
from utils.metrics import calculate_metrics

def load_predictions():
    """
    Load predictions from disk.
    
    Returns:
        Tuple of (y_true, y_pred) arrays.
    """
    paths = get_paths()
    predictions_path = paths['processed_dir'] / "predictions.npy"
    behavioral_path = paths['processed_dir'] / "filtered_behavioral.csv"
    
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions not found: {predictions_path}")
    
    if not behavioral_path.exists():
        raise FileNotFoundError(f"Behavioral data not found: {behavioral_path}")
    
    # Load predictions (array of shape [n_subjects, 1] or [n_subjects])
    y_pred = np.load(predictions_path)
    if y_pred.ndim > 1:
        y_pred = y_pred.flatten()
    
    # Load true values
    df = pd.read_csv(behavioral_path)
    if 'SleepScore' not in df.columns:
        raise ValueError("SleepScore column not found in behavioral data")
    
    y_true = df['SleepScore'].values
    
    # Ensure alignment (assuming same order as processed)
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")
    
    return y_true, y_pred

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared metric.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        R-squared value
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

def bootstrap_resample_r2(y_true: np.ndarray, y_pred: np.ndarray, n_bootstrap: int = 1000) -> Dict[str, float]:
    """
    Perform bootstrap resampling to get confidence intervals for R².
    
    Args:
        y_true: True values
        y_pred: Predicted values
        n_bootstrap: Number of bootstrap samples
        
    Returns:
        Dictionary with R² and confidence intervals
    """
    n_samples = len(y_true)
    bootstrap_r2 = []
    
    # Set seed for reproducibility
    np.random.seed(get_hyperparameter('random_seed'))
    
    for i in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]
        
        # Calculate R²
        r2 = calculate_r2(y_true_boot, y_pred_boot)
        bootstrap_r2.append(r2)
        
        # Progress logging every 100 iterations
        if (i + 1) % 100 == 0:
            logging.info(f"Bootstrap progress: {i + 1}/{n_bootstrap}")
    
    bootstrap_r2 = np.array(bootstrap_r2)
    
    # Calculate confidence intervals
    ci_lower = np.percentile(bootstrap_r2, 2.5)
    ci_upper = np.percentile(bootstrap_r2, 97.5)
    r2_mean = np.mean(bootstrap_r2)
    
    return {
        'r2_mean': float(r2_mean),
        'r2_ci_lower': float(ci_lower),
        'r2_ci_upper': float(ci_upper),
        'n_bootstrap': n_bootstrap,
        'bootstrap_std': float(np.std(bootstrap_r2))
    }

def save_bootstrap_results(results: Dict[str, float]):
    """
    Save bootstrap results to disk.
    
    Args:
        results: Bootstrap results dictionary
    """
    paths = get_paths()
    output_path = paths['results_dir'] / "bootstrap_results.json"
    ensure_dirs()
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Saved bootstrap results to {output_path}")

def main():
    """
    Main function to run evaluation.
    """
    logger = logging.getLogger(__name__)
    log_stage_start(logger, "Evaluation")
    
    try:
        # Load predictions and true values
        log_stage_start(logger, "Loading Data")
        y_true, y_pred = load_predictions()
        log_stage_complete(logger, "Loading Data")
        
        # Calculate initial metrics
        metrics = calculate_metrics(y_true, y_pred)
        logger.info(f"Initial R²: {metrics['r_squared']:.4f}, r: {metrics['pearson_r']:.4f}")
        
        # Bootstrap resampling
        log_stage_start(logger, "Bootstrap Resampling (1000 iterations)")
        n_bootstrap = get_hyperparameter('n_bootstrap', 1000)
        bootstrap_results = bootstrap_resample_r2(y_true, y_pred, n_bootstrap=n_bootstrap)
        save_bootstrap_results(bootstrap_results)
        log_stage_complete(logger, "Bootstrap Resampling")
        
        # Log summary
        logger.info(f"Bootstrap R² mean: {bootstrap_results['r2_mean']:.4f}")
        logger.info(f"95% CI: [{bootstrap_results['r2_ci_lower']:.4f}, {bootstrap_results['r2_ci_upper']:.4f}]")
        
        log_stage_complete(logger, "Evaluation")
        
    except Exception as e:
        log_stage_error(logger, "Evaluation", str(e))
        raise

if __name__ == "__main__":
    main()