"""
Bootstrap correction and multiple-comparison adjustment for correlation analysis.

Implements:
1. Bootstrap resampling (1000 iterations, seed=42) for 95% confidence intervals.
2. Bonferroni correction for multiple-comparison p-values.
3. SC-002 p < 0.05 threshold enforcement for significance testing only.
4. Correlation Result output with region_type field (target/control).
"""

import os
import sys
import logging
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_SEED = 42
CONFIDENCE_LEVEL = 0.95
SIGNIFICANCE_THRESHOLD = 0.05  # SC-002 threshold

def load_merged_data(input_path: str) -> pd.DataFrame:
    """Load the merged monthly dataset."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def compute_pearson_correlation(x: np.ndarray, y: np.ndarray) -> tuple:
    """Compute Pearson correlation coefficient and p-value."""
    if len(x) == 0 or len(y) == 0:
        return np.nan, np.nan
    
    # Handle constant arrays
    if np.std(x) == 0 or np.std(y) == 0:
        return np.nan, np.nan
    
    try:
        r, p_value = stats.pearsonr(x, y)
        return r, p_value
    except Exception as e:
        logger.warning(f"Correlation computation failed: {e}")
        return np.nan, np.nan

def bootstrap_confidence_interval(
    x: np.ndarray, 
    y: np.ndarray, 
    n_iterations: int = BOOTSTRAP_ITERATIONS, 
    seed: int = BOOTSTRAP_SEED,
    confidence_level: float = CONFIDENCE_LEVEL
) -> tuple:
    """
    Compute bootstrap confidence intervals for Pearson correlation.
    
    Returns:
        tuple: (correlation_coefficient, ci_lower, ci_upper)
    """
    np.random.seed(seed)
    n = len(x)
    if n == 0:
        return np.nan, np.nan, np.nan
    
    bootstrap_r_values = []
    
    for _ in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_resampled = x[indices]
        y_resampled = y[indices]
        
        r, _ = compute_pearson_correlation(x_resampled, y_resampled)
        if not np.isnan(r):
            bootstrap_r_values.append(r)
    
    if len(bootstrap_r_values) == 0:
        return np.nan, np.nan, np.nan
    
    bootstrap_r_values = np.array(bootstrap_r_values)
    r_original, _ = compute_pearson_correlation(x, y)
    
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_r_values, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_r_values, 100 * (1 - alpha / 2))
    
    return r_original, ci_lower, ci_upper

def bonferroni_correction(p_values: np.ndarray, alpha: float = SIGNIFICANCE_THRESHOLD) -> np.ndarray:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: Array of raw p-values
        alpha: Significance threshold (default 0.05)
    
    Returns:
        Array of corrected p-values
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return np.array([])
    
    corrected_p = p_values * n_tests
    # Cap at 1.0
    corrected_p = np.clip(corrected_p, 0.0, 1.0)
    return corrected_p

def analyze_correlation_with_bootstrap(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    region_type: str = "target"
) -> dict:
    """
    Perform correlation analysis with bootstrap confidence intervals.
    
    Args:
        df: DataFrame with data
        x_column: Name of the independent variable column
        y_column: Name of the dependent variable column
        region_type: 'target' or 'control'
    
    Returns:
        Dictionary with correlation results
    """
    x = df[x_column].dropna().values
    y = df[y_column].dropna().values
    
    if len(x) == 0 or len(y) == 0:
        logger.warning(f"No valid data for {x_column} and {y_column}")
        return {
            "region_type": region_type,
            "correlation_coefficient": np.nan,
            "p_value_raw": np.nan,
            "p_value_corrected": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "significant": False,
            "n_samples": 0
        }
    
    # Compute original correlation
    r, p_raw = compute_pearson_correlation(x, y)
    
    # Compute bootstrap confidence intervals
    r_boot, ci_lower, ci_upper = bootstrap_confidence_interval(x, y)
    
    # Apply Bonferroni correction (assuming 1 test per region for now)
    # If multiple lags are analyzed, this would need adjustment
    p_corrected = bonferroni_correction(np.array([p_raw]))[0] if not np.isnan(p_raw) else np.nan
    
    # Determine significance based on SC-002 threshold
    significant = (p_corrected < SIGNIFICANCE_THRESHOLD) if not np.isnan(p_corrected) else False
    
    return {
        "region_type": region_type,
        "correlation_coefficient": float(r) if not np.isnan(r) else None,
        "p_value_raw": float(p_raw) if not np.isnan(p_raw) else None,
        "p_value_corrected": float(p_corrected) if not np.isnan(p_corrected) else None,
        "ci_lower": float(ci_lower) if not np.isnan(ci_lower) else None,
        "ci_upper": float(ci_upper) if not np.isnan(ci_upper) else None,
        "significant": significant,
        "n_samples": len(x)
    }

def main():
    """Main entry point for bootstrap correction script."""
    # Define paths
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "merged_monthly.csv"
    output_path = project_root / "data" / "processed" / "correlation_results.json"
    
    logger.info(f"Input path: {input_path}")
    logger.info(f"Output path: {output_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T017 (merge_output.py) has been run first.")
        sys.exit(1)
    
    # Load data
    try:
        df = load_merged_data(str(input_path))
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Define columns for analysis
    # These should match the schema from T017
    ar_intensity_col = "ar_iwt_mean"  # Integrated Water Vapor Transport mean
    gravity_anomaly_col = "grace_anomaly_mean"  # Gravity anomaly mean
    
    # Check if columns exist
    if ar_intensity_col not in df.columns or gravity_anomaly_col not in df.columns:
        logger.error(f"Required columns not found. Available: {list(df.columns)}")
        sys.exit(1)
    
    # Analyze target region (assuming merged data is already filtered to target)
    logger.info("Analyzing target region correlation...")
    target_result = analyze_correlation_with_bootstrap(
        df, 
        ar_intensity_col, 
        gravity_anomaly_col, 
        region_type="target"
    )
    
    # Prepare output
    results = {
        "analysis_metadata": {
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "confidence_level": CONFIDENCE_LEVEL,
            "significance_threshold": SIGNIFICANCE_THRESHOLD,
            "correction_method": "Bonferroni"
        },
        "results": [target_result]
    }
    
    # Add control region analysis if control data exists
    # For now, we assume the merged file contains only target data
    # Control region analysis would be done in T022
    
    # Save results
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        sys.exit(1)
    
    # Print summary
    logger.info("\n--- Correlation Analysis Summary ---")
    for res in results["results"]:
        logger.info(f"Region: {res['region_type']}")
        logger.info(f"  Correlation: {res['correlation_coefficient']:.4f}")
        logger.info(f"  95% CI: [{res['ci_lower']:.4f}, {res['ci_upper']:.4f}]")
        logger.info(f"  Raw p-value: {res['p_value_raw']:.4f}")
        logger.info(f"  Corrected p-value: {res['p_value_corrected']:.4f}")
        logger.info(f"  Significant (p < {SIGNIFICANCE_THRESHOLD}): {res['significant']}")
        logger.info(f"  Samples: {res['n_samples']}")
    
    logger.info("-----------------------------------")

if __name__ == "__main__":
    main()