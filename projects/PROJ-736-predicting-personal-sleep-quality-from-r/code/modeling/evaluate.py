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
from typing import List, Tuple, Optional, Dict, Any
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, log_event
from config import get_paths

# Constants for bootstrap
BOOTSTRAP_N_RESAMPLES = 1000
BOOTSTRAP_CONFIDENCE_LEVEL = 0.95
BOOTSTRAP_RANDOM_SEED = 42

def load_predictions(predictions_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load the outer-fold predictions, true labels, and subject IDs from the training pipeline.
    
    Args:
        predictions_path: Path to the predictions.npy file.
        
    Returns:
        Tuple of (predictions, true_labels, subject_ids)
    """
    log_stage_start("Loading predictions for bootstrap analysis")
    
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    try:
        data = np.load(predictions_path, allow_pickle=True).item()
        predictions = data.get('predictions')
        true_labels = data.get('true_labels')
        subject_ids = data.get('subject_ids')
        
        if predictions is None or true_labels is None:
            raise ValueError("Predictions file is missing required keys: 'predictions' or 'true_labels'")
        
        log_stage_complete("Loaded predictions successfully", {
            "n_samples": len(predictions),
            "predictions_shape": predictions.shape,
            "labels_shape": true_labels.shape
        })
        
        return predictions, true_labels, subject_ids
    except Exception as e:
        log_stage_error("Failed to load predictions", str(e))
        raise

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared (coefficient of determination).
    
    Args:
        y_true: True values.
        y_pred: Predicted values.
        
    Returns:
        R-squared value.
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
        
    return 1.0 - (ss_res / ss_tot)

def bootstrap_resample_r2(
    predictions: np.ndarray,
    true_labels: np.ndarray,
    n_resamples: int = BOOTSTRAP_N_RESAMPLES,
    confidence_level: float = BOOTSTRAP_CONFIDENCE_LEVEL,
    random_seed: int = BOOTSTRAP_RANDOM_SEED
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling on outer-fold predictions to estimate confidence intervals for R².
    
    This function resamples the (prediction, true_label) pairs with replacement,
    calculates R² for each resample, and computes the confidence interval.
    
    Args:
        predictions: Array of predicted values from the model.
        true_labels: Array of true values.
        n_resamples: Number of bootstrap resamples to generate.
        confidence_level: Confidence level for the interval (e.g., 0.95 for 95% CI).
        random_seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing:
            - r2_original: Original R² on the full dataset
            - r2_bootstrap_mean: Mean R² across bootstrap resamples
            - r2_bootstrap_std: Standard deviation of R² across bootstrap resamples
            - ci_lower: Lower bound of the confidence interval
            - ci_upper: Upper bound of the confidence interval
            - r2_distribution: Array of all bootstrap R² values (for plotting/debugging)
    """
    log_stage_start(
        "Bootstrap resampling for R² confidence interval",
        {
            "n_resamples": n_resamples,
            "confidence_level": confidence_level,
            "n_samples": len(predictions)
        }
    )
    
    np.random.seed(random_seed)
    n_samples = len(predictions)
    
    # Calculate original R²
    r2_original = calculate_r2(true_labels, predictions)
    
    # Bootstrap resampling
    bootstrap_r2_values = []
    start_time = time.time()
    
    for i in range(n_resamples):
        # Resample indices with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_true_resampled = true_labels[indices]
        y_pred_resampled = predictions[indices]
        
        # Calculate R² for this resample
        r2_boot = calculate_r2(y_true_resampled, y_pred_resampled)
        bootstrap_r2_values.append(r2_boot)
        
        # Progress logging every 10%
        if (i + 1) % (n_resamples // 10) == 0:
            elapsed = time.time() - start_time
            log_event("Bootstrap progress", {
                "completed": i + 1,
                "total": n_resamples,
                "percent": round((i + 1) / n_resamples * 100, 1),
                "elapsed_seconds": round(elapsed, 2)
            })
    
    bootstrap_r2_values = np.array(bootstrap_r2_values)
    
    # Calculate statistics
    r2_mean = np.mean(bootstrap_r2_values)
    r2_std = np.std(bootstrap_r2_values)
    
    # Calculate confidence interval (percentile method)
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_r2_values, (alpha / 2) * 100)
    ci_upper = np.percentile(bootstrap_r2_values, (1 - alpha / 2) * 100)
    
    elapsed = time.time() - start_time
    
    result = {
        "r2_original": float(r2_original),
        "r2_bootstrap_mean": float(r2_mean),
        "r2_bootstrap_std": float(r2_std),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "confidence_level": confidence_level,
        "n_resamples": n_resamples,
        "n_samples": n_samples,
        "r2_distribution": bootstrap_r2_values.tolist(),
        "elapsed_seconds": round(elapsed, 2)
    }
    
    log_stage_complete(
        "Bootstrap resampling completed",
        {
            "r2_original": result["r2_original"],
            "ci_95": [result["ci_lower"], result["ci_upper"]],
            "elapsed_seconds": result["elapsed_seconds"]
        }
    )
    
    return result

def save_bootstrap_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save bootstrap resampling results to a JSON file.
    
    Args:
        results: Dictionary containing bootstrap results.
        output_path: Path to save the results JSON.
    """
    # Create a copy to avoid saving large arrays in the main report if not needed
    save_results = results.copy()
    # We keep the distribution for debugging but note it's large
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(save_results, f, indent=2)
    
    log_event("Bootstrap results saved", {"path": output_path, "file_size_bytes": os.path.getsize(output_path)})

def bootstrap_resample_r2(y_true: np.ndarray, y_pred: np.ndarray, n_bootstrap: int = 1000) -> List[float]:
    """
    Main entry point for the bootstrap resampling analysis.
    
    This function:
    1. Loads outer-fold predictions from data/processed/predictions.npy
    2. Performs 1,000 bootstrap resamples to estimate R² confidence intervals
    3. Saves the results to data/results/bootstrap_r2_ci.json
    """
    log_stage_start("T023: Bootstrap Resampling for R² Confidence Interval")
    
    try:
        paths = get_paths()
        predictions_path = paths["predictions"]
        output_path = paths["bootstrap_ci"]
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Load predictions
        predictions, true_labels, subject_ids = load_predictions(predictions_path)
        
        # Perform bootstrap resampling
        bootstrap_results = bootstrap_resample_r2(
            predictions=predictions,
            true_labels=true_labels,
            n_resamples=BOOTSTRAP_N_RESAMPLES,
            confidence_level=BOOTSTRAP_CONFIDENCE_LEVEL,
            random_seed=BOOTSTRAP_RANDOM_SEED
        )
        
        # Save results
        save_bootstrap_results(bootstrap_results, output_path)
        
        log_stage_complete(
            "T023: Bootstrap Resampling Completed Successfully",
            {
                "output_file": output_path,
                "r2_original": bootstrap_results["r2_original"],
                "ci_95": [bootstrap_results["ci_lower"], bootstrap_results["ci_upper"]]
            }
        )
        
        # Print summary to stdout for quick verification
        print(f"\nBootstrap Resampling Results:")
        print(f"  Original R²: {bootstrap_results['r2_original']:.4f}")
        print(f"  95% CI: [{bootstrap_results['ci_lower']:.4f}, {bootstrap_results['ci_upper']:.4f}]")
        print(f"  Bootstrap Mean R²: {bootstrap_results['r2_bootstrap_mean']:.4f}")
        print(f"  Bootstrap Std R²: {bootstrap_results['r2_bootstrap_std']:.4f}")
        print(f"  Results saved to: {output_path}")
        
    except Exception as e:
        log_stage_error("T023: Bootstrap Resampling Failed", str(e))
        print(f"Error during bootstrap resampling: {e}")
        raise

if __name__ == "__main__":
    main()
