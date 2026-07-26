"""
Sensitivity Analysis Module (T022a)

This module implements a Bootstrap-based sensitivity analysis to verify the
stability of the correlation coefficients derived in T022/T026.
While T024 (LASSO) handles model stability via regularization, T022a provides
a non-parametric check on the correlation significance itself.

Outputs:
  - data/processed/sensitivity_analysis_results.json: Bootstrap statistics
    (mean, std, CI, stability_score) for top correlations.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import from local project modules (API surface compliance)
from analysis import get_data_path, load_standard_subset
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def bootstrap_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    n_bootstraps: int = 1000,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Perform bootstrap resampling to estimate the stability of Pearson correlation.

    Args:
        df: DataFrame containing the data.
        x_col: Name of the independent variable column.
        y_col: Name of the dependent variable column (e.g., half_life).
        n_bootstraps: Number of bootstrap samples.
        random_state: Seed for reproducibility.

    Returns:
        Dict with mean_r, std_r, ci_lower, ci_upper, stability_score.
    """
    rng = np.random.default_rng(random_state)
    n_samples = len(df)
    if n_samples < 2:
        raise ValueError("Bootstrap requires at least 2 samples.")

    correlations = []

    for _ in range(n_bootstraps):
        # Resample with replacement
        indices = rng.choice(n_samples, size=n_samples, replace=True)
        sample = df.iloc[indices]

        # Calculate Pearson correlation
        # Drop pairs where either is NaN to ensure valid calculation
        valid_pairs = sample[[x_col, y_col]].dropna()
        if len(valid_pairs) < 2:
            continue

        r, _ = np.corrcoef(valid_pairs[x_col], valid_pairs[y_col])
        correlations.append(r)

    if not correlations:
        return {
            "mean_r": np.nan,
            "std_r": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "stability_score": 0.0,
            "note": "Insufficient valid pairs for bootstrap"
        }

    mean_r = np.mean(correlations)
    std_r = np.std(correlations)
    ci_lower = np.percentile(correlations, 2.5)
    ci_upper = np.percentile(correlations, 97.5)

    # Stability score: Inverse of relative standard deviation (higher is better)
    # If mean is near zero, stability is undefined/low
    if abs(mean_r) > 1e-9:
        stability_score = 1.0 / (1.0 + (std_r / abs(mean_r)))
    else:
        stability_score = 0.0

    return {
        "mean_r": float(mean_r),
        "std_r": float(std_r),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "stability_score": float(stability_score)
    }

def run_sensitivity_analysis(
    data_path: Optional[Path] = None,
    n_bootstraps: int = 1000,
    target_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main entry point for sensitivity analysis.
    Reads standard_subset, identifies top correlated features from analysis_results,
    and runs bootstrap on them.

    Args:
        data_path: Path to standard_subset.csv. If None, uses default config.
        n_bootstraps: Number of bootstrap iterations.
        target_cols: List of columns to test against 'half_life'. If None,
                     uses top 5 from analysis_results.json.

    Returns:
        Dict containing results for each tested correlation.
    """
    if data_path is None:
        data_path = get_data_path("standard_subset.csv")

    logger.info(f"Loading standard subset from {data_path}")
    df = load_standard_subset(data_path)

    if df.empty:
        logger.warning("Standard subset is empty. Skipping sensitivity analysis.")
        return {"status": "skipped", "reason": "Empty dataset"}

    # Determine target columns to analyze
    # Priority 1: Use provided list
    # Priority 2: Read from analysis_results.json if available
    # Priority 3: Fallback to all numeric descriptors (excluding half_life)

    analysis_path = get_data_path("analysis_results.json")
    if target_cols is None and analysis_path.exists():
        try:
            with open(analysis_path, 'r') as f:
                results = json.load(f)
            # Extract top correlations if available
            significant = results.get("significant_correlations", [])
            if significant:
                target_cols = [item["feature"] for item in significant[:5]]
                logger.info(f"Using top {len(target_cols)} features from analysis_results")
        except Exception as e:
            logger.warning(f"Could not read analysis_results for targets: {e}")

    if target_cols is None:
        # Fallback: Select numeric columns that are not 'half_life'
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        exclude = ['half_life', 'id', 'row_idx']
        target_cols = [c for c in numeric_cols if c not in exclude]
        logger.info(f"Using fallback target columns: {target_cols}")

    results = {}
    target_var = 'half_life'

    if target_var not in df.columns:
        logger.error(f"Target variable '{target_var}' not found in dataset.")
        return {"status": "failed", "reason": f"Missing target column: {target_var}"}

    for col in target_cols:
        if col not in df.columns:
            logger.warning(f"Target column '{col}' not found in dataset. Skipping.")
            continue

        logger.info(f"Running bootstrap for {col} vs {target_var}")
        try:
            stats = bootstrap_correlation(df, col, target_var, n_bootstraps)
            results[col] = stats
        except Exception as e:
            logger.error(f"Failed to compute bootstrap for {col}: {e}")
            results[col] = {"error": str(e)}

    return {
        "status": "completed",
        "n_bootstraps": n_bootstraps,
        "target_variable": target_var,
        "results": results
    }

def save_sensitivity_results(
    results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save sensitivity analysis results to JSON.

    Args:
        results: The dictionary returned by run_sensitivity_analysis.
        output_path: Path to save the JSON file.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_data_path("sensitivity_analysis_results.json")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis results saved to {output_path}")
    return output_path

def main():
    """
    CLI entry point for T022a.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Sensitivity Analysis (T022a)...")

    try:
        results = run_sensitivity_analysis()
        output_file = save_sensitivity_results(results)
        logger.info(f"Task completed successfully. Output: {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
