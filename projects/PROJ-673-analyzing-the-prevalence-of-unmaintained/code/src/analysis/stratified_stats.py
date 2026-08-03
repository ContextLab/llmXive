"""
Stratified statistical analysis for unmaintained dependencies.

This module computes Spearman correlation coefficients for dependency age vs.
vulnerability count, stratified by package category. It excludes groups with
fewer than 30 samples to ensure statistical validity.
"""

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_dependencies_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed dependencies data from CSV.

    Args:
        filepath: Path to the CSV file. Defaults to data/processed/dependencies_raw.csv.

    Returns:
        DataFrame containing dependency data.
    """
    if filepath is None:
        filepath = Path("data/processed/dependencies_raw.csv")

    if not filepath.exists():
        raise FileNotFoundError(f"Dependencies data file not found: {filepath}")

    logger.info(f"Loading dependencies data from {filepath}")
    df = pd.read_csv(filepath)

    # Ensure numeric columns are properly typed
    numeric_cols = ['age_in_days', 'vulnerability_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def filter_valid_samples(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out samples with missing age_in_days or vulnerability_count.

    Args:
        df: Input DataFrame.

    Returns:
        Filtered DataFrame with valid samples only.
    """
    logger.info(f"Filtering valid samples. Original count: {len(df)}")

    # Filter out rows where age_in_days or vulnerability_count is NaN
    valid_df = df.dropna(subset=['age_in_days', 'vulnerability_count'])

    logger.info(f"Valid samples count: {len(valid_df)}")
    return valid_df


def compute_stratified_correlations(
    df: pd.DataFrame,
    category_col: str = 'category',
    age_col: str = 'age_in_days',
    vuln_col: str = 'vulnerability_count',
    min_samples: int = 30
) -> Dict[str, Dict[str, Any]]:
    """
    Compute Spearman correlation coefficients stratified by category.

    Groups with fewer than min_samples are excluded.

    Args:
        df: DataFrame with dependency data.
        category_col: Column name for package category.
        age_col: Column name for dependency age.
        vuln_col: Column name for vulnerability count.
        min_samples: Minimum number of samples required for a group.

    Returns:
        Dictionary mapping category names to correlation results.
    """
    if category_col not in df.columns:
        raise ValueError(f"Category column '{category_col}' not found in DataFrame")

    logger.info(f"Computing stratified correlations with min_samples={min_samples}")

    results = {}
    category_counts = df[category_col].value_counts()

    logger.info(f"Category distribution:\n{category_counts}")

    for category, count in category_counts.items():
        if count < min_samples:
            logger.info(f"Excluding category '{category}' (N={count} < {min_samples})")
            continue

        category_df = df[df[category_col] == category]

        # Calculate Spearman correlation
        try:
            rho, p_value = spearmanr(
                category_df[age_col],
                category_df[vuln_col]
            )

            # Handle case where correlation is NaN (e.g., constant values)
            if np.isnan(rho):
                rho = 0.0
                p_value = 1.0

            results[category] = {
                'n_samples': int(count),
                'spearman_rho': float(rho),
                'p_value': float(p_value),
                'is_significant': p_value < 0.05
            }

            logger.info(
                f"Category '{category}': N={count}, rho={rho:.4f}, "
                f"p={p_value:.4f}, significant={p_value < 0.05}"
            )

        except Exception as e:
            logger.error(f"Error computing correlation for category '{category}': {e}")
            results[category] = {
                'n_samples': int(count),
                'error': str(e),
                'spearman_rho': None,
                'p_value': None,
                'is_significant': None
            }

    return results


def run_stratified_analysis(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    category_col: str = 'category',
    min_samples: int = 30
) -> Dict[str, Any]:
    """
    Run the full stratified analysis pipeline.

    Args:
        input_path: Path to input CSV file.
        output_path: Path to output JSON file.
        category_col: Column name for package category.
        min_samples: Minimum samples per group.

    Returns:
        Dictionary containing analysis results.
    """
    if output_path is None:
        output_path = Path("data/processed/results_stratified.json")

    # Load and filter data
    df = load_dependencies_data(input_path)
    valid_df = filter_valid_samples(df)

    # Compute stratified correlations
    correlations = compute_stratified_correlations(
        valid_df,
        category_col=category_col,
        min_samples=min_samples
    )

    # Prepare results
    results = {
        'total_samples': len(df),
        'valid_samples': len(valid_df),
        'min_samples_threshold': min_samples,
        'categories_included': len(correlations),
        'categories_excluded': sum(1 for c, n in valid_df[category_col].value_counts().items() if n < min_samples),
        'stratified_correlations': correlations
    }

    # Write results to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Stratified analysis results written to {output_path}")

    return results


def main():
    """Main entry point for the stratified analysis script."""
    logger.info("Starting stratified correlation analysis")

    results = run_stratified_analysis()

    logger.info(f"Analysis complete. Included {results['categories_included']} categories "
               f"with N >= {results['min_samples_threshold']}")

    # Print summary
    print("\n=== Stratified Correlation Analysis Summary ===")
    print(f"Total samples: {results['total_samples']}")
    print(f"Valid samples: {results['valid_samples']}")
    print(f"Categories included: {results['categories_included']}")
    print(f"Categories excluded (N < {results['min_samples_threshold']}): {results['categories_excluded']}")
    print("\nCorrelations by category:")

    for category, stats in results['stratified_correlations'].items():
        if 'error' in stats:
            print(f"  {category}: ERROR - {stats['error']}")
        else:
            sig_marker = "*" if stats['is_significant'] else ""
            print(
                f"  {category}: N={stats['n_samples']}, "
                f"rho={stats['spearman_rho']:.4f}, "
                f"p={stats['p_value']:.4f}{sig_marker}"
            )

    print("\n* indicates p < 0.05 (statistically significant)")
    print(f"Results saved to: data/processed/results_stratified.json")


if __name__ == "__main__":
    main()