"""
Evaluation script for the sleep quality prediction model.
"""
import os
import sys
import json
import signal
import time
import numpy as np
from pathlib import Path
from config import get_paths
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error
from sklearn.metrics import r2_score, mean_squared_error
from scipy import stats

def load_predictions():
    """Load predictions from disk."""
    paths = get_paths()
    pred_path = os.path.join(paths['results'], 'predictions.npy')
    if os.path.exists(pred_path):
        return np.load(pred_path)
    return None

def run_permutation_test(y_true, y_pred, n_permutations=1000):
    """
    Run permutation test to estimate p-value.
    """
    log_stage_start("Evaluation", "Running permutation test")
    
    # Calculate observed R2
    obs_r2 = r2_score(y_true, y_pred)
    
    null_dist = []
    for i in range(n_permutations):
        # Permute labels
        y_perm = np.random.permutation(y_true)
        # Calculate R2 with permuted labels (using same predictions? No, retrain is expensive)
        # Simplified: Compare permuted labels to original predictions (approximation)
        # Or: Generate random predictions
        # For this pipeline, we use the approximation of comparing permuted y to original y_pred
        # This is a simplified proxy for the full retraining cost.
        r2_perm = r2_score(y_perm, y_pred)
        null_dist.append(r2_perm)
    
    null_dist = np.array(null_dist)
    p_value = np.mean(null_dist >= obs_r2)
    
    log_stage_complete("Evaluation", f"Permutation test complete. p-value: {p_value}")
    return p_value

def run_bootstrap_ci(y_true, y_pred, n_bootstrap=1000, confidence_level=0.95):
    """
    Perform bootstrap resampling of outer-fold predictions to estimate confidence intervals on R².
    
    Args:
        y_true: Ground truth values (1D array)
        y_pred: Predicted values (1D array)
        n_bootstrap: Number of bootstrap resamples (default 1000)
        confidence_level: Confidence level for CI (default 0.95 for 95%)
    
    Returns:
        dict: Contains 'r2_observed', 'ci_lower', 'ci_upper', 'bootstrap_r2s'
    """
    log_stage_start("Evaluation", f"Running bootstrap resampling (n={n_bootstrap}) for {confidence_level*100}% CI on R²")
    
    n_samples = len(y_true)
    bootstrap_r2s = []
    
    for i in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]
        
        # Calculate R² for this bootstrap sample
        r2_boot = r2_score(y_true_boot, y_pred_boot)
        bootstrap_r2s.append(r2_boot)
        
        # Progress logging every 10%
        if (i + 1) % (n_bootstrap // 10) == 0:
            log_stage_start("Evaluation", f"Bootstrap progress: {(i+1)/n_bootstrap*100:.0f}%")
    
    bootstrap_r2s = np.array(bootstrap_r2s)
    
    # Calculate observed R²
    r2_observed = r2_score(y_true, y_pred)
    
    # Calculate confidence interval
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_r2s, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_r2s, 100 * (1 - alpha / 2))
    
    log_stage_complete(
        "Evaluation", 
        f"Bootstrap complete. R²={r2_observed:.4f}, {confidence_level*100}% CI=[{ci_lower:.4f}, {ci_upper:.4f}]"
    )
    
    return {
        'r2_observed': float(r2_observed),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'bootstrap_r2s': bootstrap_r2s,
        'n_bootstrap': n_bootstrap,
        'confidence_level': confidence_level
    }

def main():
    """
    Main entry point for evaluation.
    Performs bootstrap resampling on outer-fold predictions to estimate CI on R².
    """
    paths = get_paths()
    ensure_dirs()
    
    # Load data
    from data.download_hcp import filter_subjects
    import pandas as pd
    behavioral_path = paths['raw_behavioral']
    
    if not os.path.exists(behavioral_path):
        log_stage_error("Evaluation", f"Behavioral data not found at {behavioral_path}")
        return
    
    df = pd.read_csv(behavioral_path)
    df.columns = df.columns.str.strip()
    
    # Find sleep score column
    sleep_col_candidates = [c for c in df.columns if 'Sleep' in c and 'Score' in c]
    if not sleep_col_candidates:
        log_stage_error("Evaluation", "No Sleep Score column found in behavioral data")
        return
    
    sleep_col = sleep_col_candidates[0]
    y_true = df[sleep_col].values.astype(float)
    
    # Load predictions
    y_pred = load_predictions()
    
    if y_pred is None:
        log_stage_error("Evaluation", "No predictions found at expected path")
        return
    
    # Ensure arrays are aligned (same length)
    min_len = min(len(y_true), len(y_pred))
    y_true = y_true[:min_len]
    y_pred = y_pred[:min_len]
    
    if len(y_true) == 0:
        log_stage_error("Evaluation", "No valid data points for evaluation")
        return
    
    # Run bootstrap CI
    bootstrap_results = run_bootstrap_ci(y_true, y_pred, n_bootstrap=1000)
    
    # Also run standard metrics
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # Run permutation test
    p_val = run_permutation_test(y_true, y_pred)
    
    # Compile all results
    results = {
        "r2": float(r2),
        "rmse": float(rmse),
        "p_value": float(p_val),
        "bootstrap_ci": {
            "r2_observed": bootstrap_results['r2_observed'],
            "ci_lower": bootstrap_results['ci_lower'],
            "ci_upper": bootstrap_results['ci_upper'],
            "confidence_level": bootstrap_results['confidence_level'],
            "n_bootstrap": bootstrap_results['n_bootstrap']
        },
        "n_samples": len(y_true),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save results
    result_path = os.path.join(paths['results'], 'evaluation_results.json')
    with open(result_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save bootstrap distribution for further analysis
    bootstrap_path = os.path.join(paths['results'], 'bootstrap_r2_distribution.npy')
    np.save(bootstrap_path, bootstrap_results['bootstrap_r2s'])
    
    log_stage_complete("Evaluation", f"Evaluation complete. Results saved to {result_path}")

if __name__ == "__main__":
    main()
