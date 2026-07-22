"""
Sensitivity Analysis Module for PROJ-071.

This module implements sensitivity analysis using bootstrap resampling on correlation
coefficients to assess the stability of the relationship between molecular complexity
and degradation rates.

Note: While LASSO with K-fold CV (T024) addresses model stability, this module
provides a complementary non-parametric sensitivity check on the correlation metrics
themselves.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats

from config import get_config
from logging_config import get_logger

# Ensure project root is in path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

def get_data_path() -> Path:
    """Return the path to the processed standard subset."""
    config = get_config()
    return Path(config["data_dir"]) / "processed" / "standard_subset.csv"

def load_processed_data() -> Optional[pd.DataFrame]:
    """Load the standard subset data required for sensitivity analysis."""
    data_path = get_data_path()
    if not data_path.exists():
        logger.error(f"Standard subset not found at {data_path}. "
                     "Please ensure T021 (standardize.py) has run successfully.")
        return None
    
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} records from {data_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return None

def bootstrap_correlation(
    x: np.ndarray, 
    y: np.ndarray, 
    n_bootstrap: int = 1000, 
    random_seed: int = 42
) -> Dict[str, float]:
    """
    Perform bootstrap resampling to estimate the stability of Pearson correlation.

    Args:
        x: First variable array (e.g., TPSA)
        y: Second variable array (e.g., half_life)
        n_bootstrap: Number of bootstrap samples
        random_seed: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - original_r: Original Pearson correlation
            - original_p: Original p-value
            - bootstrap_mean: Mean correlation from bootstrap
            - bootstrap_std: Standard deviation of bootstrap correlations
            - bootstrap_ci_lower: Lower bound of 95% CI
            - bootstrap_ci_upper: Upper bound of 95% CI
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Input arrays must have same length >= 2")
    
    rng = np.random.default_rng(random_seed)
    n = len(x)
    bootstrap_r = []

    # Calculate original correlation
    orig_r, orig_p = stats.pearsonr(x, y)

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = rng.choice(n, size=n, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]

        # Handle constant resampled data
        if np.std(x_boot) == 0 or np.std(y_boot) == 0:
            continue

        r_boot, _ = stats.pearsonr(x_boot, y_boot)
        bootstrap_r.append(r_boot)

    if not bootstrap_r:
        logger.warning("All bootstrap samples resulted in constant data. "
                       "Returning original stats only.")
        return {
            "original_r": float(orig_r),
            "original_p": float(orig_p),
            "bootstrap_mean": float(orig_r),
            "bootstrap_std": 0.0,
            "bootstrap_ci_lower": float(orig_r),
            "bootstrap_ci_upper": float(orig_r)
        }

    bootstrap_r = np.array(bootstrap_r)
    ci_lower = np.percentile(bootstrap_r, 2.5)
    ci_upper = np.percentile(bootstrap_r, 97.5)

    return {
        "original_r": float(orig_r),
        "original_p": float(orig_p),
        "bootstrap_mean": float(np.mean(bootstrap_r)),
        "bootstrap_std": float(np.std(bootstrap_r)),
        "bootstrap_ci_lower": float(ci_lower),
        "bootstrap_ci_upper": float(ci_upper)
    }

def run_sensitivity_analysis(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    n_bootstrap: int = 1000,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run full sensitivity analysis on specified features against target.

    Args:
        df: DataFrame containing the data
        features: List of feature column names
        target: Target column name
        n_bootstrap: Number of bootstrap iterations
        output_dir: Directory to save results (defaults to data/output)

    Returns:
        Dictionary containing analysis results for all features
    """
    if output_dir is None:
        config = get_config()
        output_dir = Path(config["data_dir"]) / "output"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "sensitivity_analysis_results.json"

    results = {
        "metadata": {
            "n_samples": len(df),
            "n_bootstrap": n_bootstrap,
            "target_variable": target,
            "features_analyzed": features
        },
        "feature_stability": {}
    }

    logger.info(f"Starting sensitivity analysis for {len(features)} features...")

    for feature in features:
        if feature not in df.columns or target not in df.columns:
            logger.warning(f"Skipping {feature}: column not found.")
            continue

        x = df[feature].dropna().values
        y = df[target].dropna().values

        # Align indices after dropna
        valid_mask = ~df[feature].isna() & ~df[target].isna()
        x = df.loc[valid_mask, feature].values
        y = df.loc[valid_mask, target].values

        if len(x) < 10:
            logger.warning(f"Skipping {feature}: insufficient valid pairs ({len(x)})")
            continue

        try:
            stability_metrics = bootstrap_correlation(x, y, n_bootstrap)
            results["feature_stability"][feature] = stability_metrics
            logger.info(f"Completed analysis for {feature}: "
                        f"mean={stability_metrics['bootstrap_mean']:.3f}, "
                        f"std={stability_metrics['bootstrap_std']:.3f}")
        except Exception as e:
            logger.error(f"Failed to compute bootstrap for {feature}: {e}")
            results["feature_stability"][feature] = {"error": str(e)}

    # Save results
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis results saved to {results_file}")
    return results

def main():
    """Entry point for running sensitivity analysis."""
    logger.info("Starting Sensitivity Analysis (T022a)...")
    
    # Load data
    df = load_processed_data()
    if df is None:
        logger.error("Data loading failed. Aborting sensitivity analysis.")
        sys.exit(1)

    # Define features based on T014 descriptors
    # We assume the standard_subset.csv contains these columns
    potential_features = [
        'tpsa', 'rotatable_bonds', 'molecular_weight', 
        'aromatic_rings', 'wiener_index', 'zagreb_index'
    ]
    
    # Filter to only available columns
    available_features = [f for f in potential_features if f in df.columns]
    
    if not available_features:
        logger.error("No descriptor features found in standard_subset.csv.")
        logger.info(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    target = 'half_life_hours'
    if target not in df.columns:
        # Fallback check for common naming
        if 'half_life' in df.columns:
            target = 'half_life'
        else:
            logger.error(f"Target variable '{target}' not found in columns.")
            sys.exit(1)

    # Run analysis
    results = run_sensitivity_analysis(
        df, 
        available_features, 
        target, 
        n_bootstrap=1000
    )

    # Summary logging
    logger.info("Sensitivity Analysis Summary:")
    for feature, metrics in results.get("feature_stability", {}).items():
        if "error" in metrics:
            logger.warning(f"  {feature}: ERROR - {metrics['error']}")
        else:
            logger.info(f"  {feature}: r={metrics['original_r']:.3f}, "
                        f"ci=[{metrics['bootstrap_ci_lower']:.3f}, "
                        f"{metrics['bootstrap_ci_upper']:.3f}]")

    logger.info("Sensitivity Analysis (T022a) completed successfully.")

if __name__ == "__main__":
    main()