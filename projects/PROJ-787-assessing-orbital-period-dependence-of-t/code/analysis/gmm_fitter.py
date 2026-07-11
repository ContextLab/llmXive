import numpy as np
import pandas as pd
import logging
import os
import sys
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from sklearn.mixture import GaussianMixture
from scipy.stats import norm

logger = logging.getLogger(__name__)

# Constants for BIC difference threshold to distinguish unimodal vs bimodal
BIC_UNIMODAL_THRESHOLD = 10.0

def fit_gmm_to_radius_distribution(
    radii: np.ndarray,
    n_components: int = 2,
    random_state: int = 42
) -> Tuple[GaussianMixture, float, float]:
    """
    Fit a Gaussian Mixture Model to the radius distribution.

    Args:
        radii: Array of planet radii.
        n_components: Number of Gaussian components (default 2).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (fitted GMM, BIC score, BIC score for 1 component).
    """
    if len(radii) < 2:
        raise ValueError("Need at least 2 data points to fit GMM.")

    X = radii.reshape(-1, 1)

    # Fit 2-component model
    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type='full',
        init_params='k-means++',
        n_init=10,
        random_state=random_state,
        max_iter=200
    )
    gmm.fit(X)
    bic_2 = gmm.bic(X)

    # Fit 1-component model for comparison
    gmm_1 = GaussianMixture(
        n_components=1,
        covariance_type='full',
        random_state=random_state
    )
    gmm_1.fit(X)
    bic_1 = gmm_1.bic(X)

    return gmm, bic_2, bic_1

def calculate_gap_location(
    gmm: GaussianMixture
) -> Tuple[float, float]:
    """
    Calculate the gap location (valley) between two Gaussian components.

    The gap is the radius value where the probability density of the two
    components is equal, found between their means.

    Args:
        gmm: Fitted 2-component GaussianMixture.

    Returns:
        Tuple of (gap_location, uncertainty_estimate).
    """
    if gmm.n_components != 2:
        raise ValueError("GMM must have exactly 2 components to calculate gap.")

    # Extract means and covariances
    means = gmm.means_.flatten()
    covs = gmm.covariances_.flatten()
    stds = np.sqrt(covs)
    weights = gmm.weights_

    # Sort by mean to ensure consistent ordering (smaller mean first)
    order = np.argsort(means)
    mu1, mu2 = means[order]
    std1, std2 = stds[order]
    w1, w2 = weights[order]

    # Find the intersection point between the two Gaussians
    # Solve: w1 * N(x|mu1, std1) = w2 * N(x|mu2, std2)
    # This leads to a quadratic equation, but we can solve numerically
    # for the root between mu1 and mu2.

    def diff_func(x):
        p1 = w1 * norm.pdf(x, mu1, std1)
        p2 = w2 * norm.pdf(x, mu2, std2)
        return p1 - p2

    # Bracket the root between the two means
    try:
        from scipy.optimize import brentq
        gap = brentq(diff_func, mu1, mu2)
    except ValueError:
        # Fallback: if brentq fails, use the midpoint
        gap = (mu1 + mu2) / 2.0

    # Uncertainty estimate: weighted average of standard deviations
    uncertainty = np.sqrt(w1 * std1**2 + w2 * std2**2)

    return gap, uncertainty

def bootstrap_gap_estimation(
    radii: np.ndarray,
    n_iterations: int = 100,
    random_state: int = 42
) -> Tuple[float, float, str]:
    """
    Estimate the gap location and confidence interval via bootstrap resampling.

    Args:
        radii: Array of planet radii.
        n_iterations: Number of bootstrap iterations.
        random_state: Random seed.

    Returns:
        Tuple of (mean_gap, std_gap, status).
        status is "resolved" if bimodal, "unresolved" if unimodal.
    """
    rng = np.random.default_rng(random_state)
    gap_estimates = []
    unresolved_count = 0

    for i in range(n_iterations):
        # Resample with replacement
        sample = rng.choice(radii, size=len(radii), replace=True)

        try:
            gmm, bic_2, bic_1 = fit_gmm_to_radius_distribution(sample)
            bic_diff = bic_1 - bic_2

            if bic_diff < BIC_UNIMODAL_THRESHOLD:
                # Unimodal case: flag as unresolved
                unresolved_count += 1
                continue

            gap, _ = calculate_gap_location(gmm)
            gap_estimates.append(gap)

        except Exception as e:
            logger.warning(f"Bootstrap iteration {i} failed: {e}")
            continue

    if len(gap_estimates) == 0:
        # All iterations were unresolved or failed
        return np.nan, np.nan, "unresolved"

    mean_gap = np.mean(gap_estimates)
    std_gap = np.std(gap_estimates)

    # Determine status based on proportion of unresolved iterations
    # If >50% are unresolved, mark the bin as unresolved
    if unresolved_count > n_iterations * 0.5:
        return mean_gap, std_gap, "unresolved"

    return mean_gap, std_gap, "resolved"

def process_binned_data(
    binned_df: pd.DataFrame,
    output_path: Path
) -> pd.DataFrame:
    """
    Process each bin to find gap locations, handling unimodal cases.

    Args:
        binned_df: DataFrame with binned planets (columns: 'bin_index', 'radius').
        output_path: Path to save the results.

    Returns:
        DataFrame with gap locations and status.
    """
    results = []

    bins = binned_df['bin_index'].unique()

    for bin_idx in sorted(bins):
        bin_data = binned_df[binned_df['bin_index'] == bin_idx]
        radii = bin_data['radius'].values

        if len(radii) < 10:
            logger.warning(f"Bin {bin_idx} has too few planets ({len(radii)}), skipping.")
            results.append({
                'bin_index': bin_idx,
                'gap_location': np.nan,
                'gap_uncertainty': np.nan,
                'status': 'unresolved',
                'n_planets': len(radii)
            })
            continue

        mean_gap, std_gap, status = bootstrap_gap_estimation(radii, n_iterations=50)

        results.append({
            'bin_index': bin_idx,
            'gap_location': mean_gap,
            'gap_uncertainty': std_gap,
            'status': status,
            'n_planets': len(radii)
        })

        if status == 'unresolved':
            logger.info(f"Bin {bin_idx} identified as unimodal (BIC diff < {BIC_UNIMODAL_THRESHOLD}). Status: unresolved.")

    result_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved gap locations to {output_path}")

    return result_df

def main():
    """
    Main entry point for GMM fitting on binned data.
    Expects binned data at data/processed/binned_planets.csv
    Outputs to data/processed/gap_locations.csv
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / 'data' / 'processed' / 'binned_planets.csv'
    output_path = base_dir / 'data' / 'processed' / 'gap_locations.csv'

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading binned data from {input_path}")
    df = pd.read_csv(input_path)

    if 'radius' not in df.columns or 'bin_index' not in df.columns:
        logger.error("Input data must contain 'radius' and 'bin_index' columns.")
        sys.exit(1)

    logger.info(f"Processing {len(df)} planets across {df['bin_index'].nunique()} bins.")
    process_binned_data(df, output_path)

    logger.info("GMM fitting complete.")

if __name__ == '__main__':
    main()