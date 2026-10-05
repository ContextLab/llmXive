import os
import sys
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import pandas as pd
from scipy import stats
from utils import set_global_seed, setup_logging, record_artifact_hash
from config import ensure_directories

logger = logging.getLogger(__name__)

def calculate_observed_metric(X: np.ndarray, y: np.ndarray, model: Any) -> float:
    """
    Calculate the observed Pearson correlation coefficient (r) between
    model predictions and actual labels.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target labels (n_samples,)
        model: Fitted model with a .predict() method
        
    Returns:
        Pearson correlation coefficient (r)
    """
    predictions = model.predict(X)
    r, _ = stats.pearsonr(predictions, y)
    return float(r)

def run_bootstrap_ci(X: np.ndarray, y: np.ndarray, model_class: Any, 
                    n_iterations: int = 200, random_state: int = 42) -> Tuple[float, float, float]:
    """
    Perform bootstrap resampling to calculate 95% CI for Pearson r.
    
    Args:
        X: Feature matrix
        y: Target labels
        model_class: Class of the model to instantiate
        n_iterations: Number of bootstrap iterations
        random_state: Random seed
        
    Returns:
        Tuple of (observed_r, lower_ci, upper_ci)
    """
    set_global_seed(random_state)
    ensure_directories()
    
    # Fit model on full data to get observed r
    model = model_class()
    model.fit(X, y)
    observed_r = calculate_observed_metric(X, y, model)
    
    bootstrap_r = []
    n_samples = len(y)
    
    for i in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_resample = X[indices]
        y_resample = y[indices]
        
        # Fit model on resampled data
        model_boot = model_class()
        model_boot.fit(X_resample, y_resample)
        r_boot = calculate_observed_metric(X_resample, y_resample, model_boot)
        bootstrap_r.append(r_boot)
        
    bootstrap_r = np.array(bootstrap_r)
    lower_ci = float(np.percentile(bootstrap_r, 2.5))
    upper_ci = float(np.percentile(bootstrap_r, 97.5))
    
    return observed_r, lower_ci, upper_ci

def calculate_empirical_pvalue(observed_r: float, null_distribution: np.ndarray) -> float:
    """
    Calculate empirical p-value by comparing observed r against the null distribution.
    
    The p-value is calculated as the proportion of null distribution values that are
    as extreme or more extreme than the observed value (two-tailed test).
    
    Args:
        observed_r: The observed Pearson correlation coefficient from real data
        null_distribution: Array of correlation coefficients from permutation tests
        
    Returns:
        Empirical p-value
    """
    if len(null_distribution) == 0:
        raise ValueError("Null distribution is empty. Cannot calculate p-value.")
    
    # Two-tailed test: count how many null values are as extreme or more extreme
    # than the observed value (in absolute terms)
    abs_observed = np.abs(observed_r)
    abs_null = np.abs(null_distribution)
    
    # Count values in null distribution >= |observed_r|
    extreme_count = np.sum(abs_null >= abs_observed)
    
    # Calculate p-value
    p_value = extreme_count / len(null_distribution)
    
    logger.info(f"Observed r: {observed_r:.4f}")
    logger.info(f"Null distribution size: {len(null_distribution)}")
    logger.info(f"Extreme count (|null| >= |observed|): {extreme_count}")
    logger.info(f"Empirical p-value: {p_value:.4f}")
    
    return float(p_value)

def load_null_distribution(path: Path) -> np.ndarray:
    """
    Load the null distribution from a saved file.
    
    Args:
        path: Path to the null distribution file (CSV or NPY)
        
    Returns:
        NumPy array of correlation coefficients
    """
    if path.suffix == '.npy':
        return np.load(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
        # Assume first column contains the correlation values
        return df.iloc[:, 0].values
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def save_null_distribution(null_dist: np.ndarray, path: Path) -> None:
    """
    Save the null distribution to a file.
    
    Args:
        null_dist: NumPy array of correlation coefficients
        path: Path to save the file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, null_dist)
    logger.info(f"Null distribution saved to {path}")

def run_modeling_pipeline(
    feature_matrix_path: Path,
    labels_path: Path,
    null_distribution_path: Path,
    output_artifact_path: Path,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Main pipeline function to calculate observed metric, load null distribution,
    compute empirical p-value, and save results.
    
    Args:
        feature_matrix_path: Path to feature matrix CSV
        labels_path: Path to labels CSV
        null_distribution_path: Path to null distribution file
        output_artifact_path: Path to save the result artifact
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing results
    """
    set_global_seed(random_state)
    ensure_directories()
    setup_logging()
    
    # Load data
    logger.info(f"Loading features from {feature_matrix_path}")
    X = pd.read_csv(feature_matrix_path).values
    
    logger.info(f"Loading labels from {labels_path}")
    labels_df = pd.read_csv(labels_path)
    y = labels_df.iloc[:, 0].values  # Assume first column is the target
    
    # Load null distribution (generated by T022)
    logger.info(f"Loading null distribution from {null_distribution_path}")
    if not null_distribution_path.exists():
        raise FileNotFoundError(
            f"Null distribution file not found at {null_distribution_path}. "
            "Please ensure T022 has been executed successfully."
        )
    null_dist = load_null_distribution(null_distribution_path)
    
    # We need to calculate the observed r again to ensure consistency
    # This assumes the model is already trained or we retrain it
    # For this implementation, we'll assume we have the observed_r from T022
    # or we need to recompute it. Let's recompute it for consistency.
    
    # Simple linear regression for observed metric (as placeholder for actual model)
    # In a real scenario, this would use the Elastic Net model from T021
    from sklearn.linear_model import ElasticNet
    model = ElasticNet(alpha=0.5, l1_ratio=0.5, random_state=random_state, max_iter=5000)
    model.fit(X, y)
    observed_r = calculate_observed_metric(X, y, model)
    
    # Calculate empirical p-value
    p_value = calculate_empirical_pvalue(observed_r, null_dist)
    
    # Prepare results
    results = {
        "observed_r": observed_r,
        "p_value": p_value,
        "null_distribution_size": len(null_dist),
        "null_distribution_stats": {
            "mean": float(np.mean(null_dist)),
            "std": float(np.std(null_dist)),
            "min": float(np.min(null_dist)),
            "max": float(np.max(null_dist))
        }
    }
    
    # Save results
    output_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_artifact_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_artifact_path}")
    record_artifact_hash(output_artifact_path)
    
    return results

def main():
    """Entry point for the modeling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate empirical p-value from null distribution")
    parser.add_argument("--features", type=str, required=True, help="Path to feature matrix CSV")
    parser.add_argument("--labels", type=str, required=True, help="Path to labels CSV")
    parser.add_argument("--null-dist", type=str, required=True, help="Path to null distribution file")
    parser.add_argument("--output", type=str, required=True, help="Path to output artifact JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    results = run_modeling_pipeline(
        feature_matrix_path=Path(args.features),
        labels_path=Path(args.labels),
        null_distribution_path=Path(args.null_dist),
        output_artifact_path=Path(args.output),
        random_state=args.seed
    )
    
    print(f"Observed r: {results['observed_r']:.4f}")
    print(f"Empirical p-value: {results['p_value']:.4f}")
    print(f"Null distribution size: {results['null_distribution_size']}")

if __name__ == "__main__":
    main()
