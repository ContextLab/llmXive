"""
Correlation Analysis Module for Musical Training Study.

Computes Pearson/Spearman correlation between years of training and connectivity strength
for musicians only. Calculates effect sizes, confidence intervals, and stability flags.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from scipy import stats

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
OUTPUT_DIR = Path("data/processed")
CONNECTIVITY_INPUT = OUTPUT_DIR / "connectivity_matrices.npy"
SUBJECTS_INPUT = OUTPUT_DIR / "subjects_cleaned.csv"
OUTPUT_FILE = OUTPUT_DIR / "correlation_results.csv"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_musicians_connectivity_data(
    connectivity_path: Path,
    subjects_path: Path
) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Load connectivity matrices and filter for musicians only.

    Args:
        connectivity_path: Path to connectivity_matrices.npy
        subjects_path: Path to subjects_cleaned.csv

    Returns:
        Tuple of (connectivity_matrices, musicians_df)
    """
    logger.info(f"Loading connectivity matrices from {connectivity_path}")
    if not connectivity_path.exists():
        raise FileNotFoundError(f"Connectivity matrices not found: {connectivity_path}")

    matrices = np.load(connectivity_path)
    logger.info(f"Loaded connectivity matrices with shape: {matrices.shape}")

    logger.info(f"Loading subject data from {subjects_path}")
    if not subjects_path.exists():
        raise FileNotFoundError(f"Subject data not found: {subjects_path}")

    subjects_df = pd.read_csv(subjects_path)

    # Filter for musicians only (years_of_training >= 1)
    musicians_df = subjects_df[subjects_df['years_of_training'] >= 1].copy()
    logger.info(f"Found {len(musicians_df)} musicians out of {len(subjects_df)} total subjects")

    if len(musicians_df) == 0:
        raise ValueError("No musicians found in the dataset. Cannot perform correlation analysis.")

    # Ensure connectivity matrices match the number of musicians
    if matrices.shape[0] != len(subjects_df):
        # If matrices are for all subjects, we need to index only musicians
        # This assumes the order in subjects_df matches the matrix order
        musician_indices = subjects_df[subjects_df['years_of_training'] >= 1].index.tolist()
        if len(musician_indices) != len(musicians_df):
            raise ValueError("Index mismatch between subjects and connectivity matrices")
        matrices = matrices[musician_indices]

    return matrices, musicians_df


def compute_connectivity_strength(matrices: np.ndarray) -> np.ndarray:
    """
    Compute connectivity strength for each subject's matrix.

    Connectivity strength is defined as the mean of the upper triangle
    (excluding diagonal) of the connectivity matrix.

    Args:
        matrices: Array of shape (N_subjects, N_ROIs, N_ROIs)

    Returns:
        Array of shape (N_subjects,) containing connectivity strength values
    """
    n_subjects = matrices.shape[0]
    strengths = np.zeros(n_subjects)

    for i in range(n_subjects):
        mat = matrices[i]
        # Get upper triangle excluding diagonal
        upper_tri = mat[np.triu_indices_from(mat, k=1)]
        strengths[i] = np.mean(upper_tri)

    return strengths


def compute_correlation_with_training(
    strengths: np.ndarray,
    years_of_training: np.ndarray,
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    Compute correlation between connectivity strength and years of training.

    Args:
        strengths: Array of connectivity strength values
        years_of_training: Array of years of training values
        method: 'pearson' or 'spearman'

    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    if method == 'pearson':
        r, p = stats.pearsonr(strengths, years_of_training)
    elif method == 'spearman':
        r, p = stats.spearmanr(strengths, years_of_training)
    else:
        raise ValueError(f"Unknown correlation method: {method}")

    return r, p


def calculate_correlation_ci(
    r: float,
    n: int,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for correlation coefficient using Fisher z-transform.

    Args:
        r: Correlation coefficient
        n: Sample size
        alpha: Significance level (default 0.05 for 95% CI)

    Returns:
        Tuple of (ci_lower, ci_upper)
    """
    if n < 3:
        logger.warning("Sample size too small for CI calculation")
        return (0.0, 0.0)

    # Fisher z-transform
    # Avoid division by zero or log of negative number
    r_clipped = np.clip(r, -0.9999, 0.9999)
    z = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))

    # Standard error of z
    se_z = 1.0 / np.sqrt(n - 3)

    # Critical value for confidence interval
    z_crit = stats.norm.ppf(1 - alpha / 2)

    # Confidence interval in z-space
    z_lower = z - z_crit * se_z
    z_upper = z + z_crit * se_z

    # Back-transform to r-space
    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

    return ci_lower, ci_upper


def calculate_effect_size_cohen_d(
    strengths: np.ndarray,
    years_of_training: np.ndarray
) -> float:
    """
    Calculate Cohen's d effect size for the correlation.

    Note: For correlation, we use the point-biserial correlation equivalent
    or simply report the correlation coefficient as the effect size.
    Here we use a simplified approach based on the correlation magnitude.

    Args:
        strengths: Array of connectivity strength values
        years_of_training: Array of years of training values

    Returns:
        Effect size (Cohen's d approximation)
    """
    # For continuous correlation, we can use r as the effect size
    # or convert r to d: d = 2r / sqrt(1-r^2)
    r = stats.pearsonr(strengths, years_of_training)[0]
    r_clipped = np.clip(r, -0.9999, 0.9999)
    d = (2 * r_clipped) / np.sqrt(1 - r_clipped**2)
    return d


def process_correlation_analysis(
    connectivity_path: Optional[Path] = None,
    subjects_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main function to perform correlation analysis.

    Args:
        connectivity_path: Path to connectivity matrices (default: data/processed/connectivity_matrices.npy)
        subjects_path: Path to subjects data (default: data/processed/subjects_cleaned.csv)
        output_path: Path for output CSV (default: data/processed/correlation_results.csv)

    Returns:
        DataFrame with correlation results
    """
    if connectivity_path is None:
        connectivity_path = CONNECTIVITY_INPUT
    if subjects_path is None:
        subjects_path = SUBJECTS_INPUT
    if output_path is None:
        output_path = OUTPUT_FILE

    logger.info("Starting correlation analysis for musicians")

    # Load data
    matrices, musicians_df = load_musicians_connectivity_data(connectivity_path, subjects_path)

    # Compute connectivity strength
    strengths = compute_connectivity_strength(matrices)
    years_of_training = musicians_df['years_of_training'].values

    # Compute correlation
    r, p_value = compute_correlation_with_training(strengths, years_of_training, method='pearson')
    logger.info(f"Pearson correlation: r={r:.4f}, p={p_value:.4f}")

    # Compute effect size
    effect_size = calculate_effect_size_cohen_d(strengths, years_of_training)

    # Compute confidence interval
    ci_lower, ci_upper = calculate_correlation_ci(r, len(strengths))

    # Determine stability flag
    # If CI includes zero, stability is "low", otherwise "high"
    if ci_lower <= 0 <= ci_upper:
        stability_flag = "low"
    else:
        stability_flag = "high"

    # Create result DataFrame
    # Since we are correlating a global strength metric with training years,
    # we use a single connection_id representing the global connectivity strength
    result_data = {
        'connection_id': ['global_connectivity_strength'],
        'r_value': [r],
        'p_value': [p_value],
        'effect_size': [effect_size],
        'ci_95': [f"[{ci_lower:.4f}, {ci_upper:.4f}]"],
        'stability_flag': [stability_flag]
    }

    result_df = pd.DataFrame(result_data)

    # Write output
    result_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")

    return result_df


def main():
    """Entry point for correlation analysis."""
    logger.info("Running correlation analysis module")

    try:
        result_df = process_correlation_analysis()
        print(f"\nCorrelation Analysis Results:")
        print(result_df.to_string(index=False))
        print(f"\nOutput saved to: {OUTPUT_FILE}")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during correlation analysis: {e}")
        raise


if __name__ == "__main__":
    main()
