"""
Vectorized implementation of GMM fitting for performance optimization.
Uses numpy vectorized operations and optimized scipy routines.
"""
import os
import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.mixture import GaussianMixture
from typing import Tuple, Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fit_gmm_vectorized(
    radii: np.ndarray,
    n_components: int = 2,
    max_iter: int = 100,
    n_init: int = 5
) -> Tuple[GaussianMixture, float]:
    """
    Fit a Gaussian Mixture Model using vectorized sklearn operations.
    
    Args:
        radii: Array of planet radii
        n_components: Number of Gaussian components
        max_iter: Maximum iterations
        n_init: Number of initializations
        
    Returns:
        Tuple of (fitted GMM, BIC score)
    """
    if len(radii) < n_components:
        raise ValueError(f"Not enough data points ({len(radii)}) for {n_components} components")
    
    # Reshape for sklearn
    X = radii.reshape(-1, 1)
    
    # Fit GMM with K-Means++ initialization
    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type='full',
        init_params='k-means++',
        max_iter=max_iter,
        n_init=n_init,
        random_state=42,
        verbose=0
    )
    
    gmm.fit(X)
    bic = gmm.bic(X)
    
    return gmm, bic

def calculate_gap_location_vectorized(
    gmm: GaussianMixture
) -> Tuple[float, float, float]:
    """
    Calculate the gap location (valley between two Gaussians).
    
    Args:
        gmm: Fitted GaussianMixture model
        
    Returns:
        Tuple of (gap_location, lower_bound, upper_bound)
    """
    means = gmm.means_.flatten()
    covars = gmm.covariances_.flatten()
    weights = gmm.weights_
    
    # Sort by mean
    sorted_idx = np.argsort(means)
    means = means[sorted_idx]
    covars = covars[sorted_idx]
    weights = weights[sorted_idx]
    
    stds = np.sqrt(covars)
    
    # Find the point where the two PDFs intersect
    # Solve: w1 * N(x|mu1,s1) = w2 * N(x|mu2,s2)
    # This is a quadratic equation in log space
    
    mu1, mu2 = means[0], means[1]
    s1, s2 = stds[0], stds[1]
    w1, w2 = weights[0], weights[1]
    
    # Coefficients for the quadratic equation in x
    # From: log(w1) - log(s1) - (x-mu1)^2/(2s1^2) = log(w2) - log(s2) - (x-mu2)^2/(2s2^2)
    a = 1/(2*s2**2) - 1/(2*s1**2)
    b = mu1/s1**2 - mu2/s2**2
    c = (mu2**2)/(2*s2**2) - (mu1**2)/(2*s1**2) + np.log(w2/s2) - np.log(w1/s1)
    
    if abs(a) < 1e-10:
        # Linear case
        gap = -c / b if abs(b) > 1e-10 else (mu1 + mu2) / 2
    else:
        discriminant = b**2 - 4*a*c
        if discriminant < 0:
            # No real intersection, use midpoint
            gap = (mu1 + mu2) / 2
        else:
            root1 = (-b + np.sqrt(discriminant)) / (2*a)
            root2 = (-b - np.sqrt(discriminant)) / (2*a)
            # Choose the root between the two means
            if mu1 < root1 < mu2:
                gap = root1
            elif mu1 < root2 < mu2:
                gap = root2
            else:
                gap = (mu1 + mu2) / 2
    
    # Estimate uncertainty based on the width of the valley
    # Approximate using the combined standard deviation
    combined_std = np.sqrt((s1**2 + s2**2) / 2)
    uncertainty = combined_std / np.sqrt(len(radii)) if len(radii) > 0 else combined_std
    
    return gap, gap - 2*uncertainty, gap + 2*uncertainty

def bootstrap_gap_vectorized(
    radii: np.ndarray,
    n_bootstrap: int = 100,
    random_state: int = 42
) -> Tuple[float, float, float]:
    """
    Perform bootstrap resampling to estimate gap location uncertainty.
    Uses vectorized operations where possible.
    
    Args:
        radii: Array of planet radii
        n_bootstrap: Number of bootstrap iterations
        random_state: Random seed
        
    Returns:
        Tuple of (mean_gap, std_gap, confidence_interval_95)
    """
    logger.info(f"Starting bootstrap with {n_bootstrap} iterations")
    
    rng = np.random.RandomState(random_state)
    n = len(radii)
    gaps = np.zeros(n_bootstrap)
    
    for i in range(n_bootstrap):
        # Resample with replacement (vectorized)
        indices = rng.randint(0, n, size=n)
        sample = radii[indices]
        
        if len(sample) < 4:
            gaps[i] = np.nan
            continue
        
        try:
            gmm, _ = fit_gmm_vectorized(sample, n_components=2, n_init=3)
            gap, _, _ = calculate_gap_location_vectorized(gmm)
            gaps[i] = gap
        except Exception as e:
            gaps[i] = np.nan
    
    # Filter valid gaps
    valid_gaps = gaps[~np.isnan(gaps)]
    
    if len(valid_gaps) == 0:
        logger.warning("No valid gap estimates from bootstrap")
        return np.nan, np.nan, (np.nan, np.nan)
    
    mean_gap = np.mean(valid_gaps)
    std_gap = np.std(valid_gaps)
    ci_lower = np.percentile(valid_gaps, 2.5)
    ci_upper = np.percentile(valid_gaps, 97.5)
    
    logger.info(f"Bootstrap results: mean={mean_gap:.3f}, std={std_gap:.3f}, 95% CI=[{ci_lower:.3f}, {ci_upper:.3f}]")
    
    return mean_gap, std_gap, (ci_lower, ci_upper)

def process_binned_data_vectorized(
    df: pd.DataFrame,
    radius_col: str = 'radius',
    bin_col: str = 'bin_index',
    min_bin_size: int = 30,
    n_bootstrap: int = 50
) -> pd.DataFrame:
    """
    Process binned data and fit GMM to each bin.
    
    Args:
        df: DataFrame with binned planet data
        radius_col: Name of radius column
        bin_col: Name of bin index column
        min_bin_size: Minimum planets per bin to fit
        n_bootstrap: Number of bootstrap iterations
        
    Returns:
        DataFrame with gap locations and uncertainties per bin
    """
    logger.info(f"Processing {df[bin_col].nunique()} bins for GMM fitting")
    
    results = []
    
    for bin_idx in sorted(df[bin_col].unique()):
        bin_data = df[df[bin_col] == bin_idx]
        
        if len(bin_data) < min_bin_size:
            results.append({
                'bin_index': bin_idx,
                'n_planets': len(bin_data),
                'gap_location': np.nan,
                'gap_std': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'status': 'insufficient_data'
            })
            continue
        
        radii = bin_data[radius_col].values
        
        # Outlier handling: remove points > 3 std from mean
        mean_r = np.mean(radii)
        std_r = np.std(radii)
        valid_mask = np.abs(radii - mean_r) <= 3 * std_r
        radii_clean = radii[valid_mask]
        
        if len(radii_clean) < 4:
            results.append({
                'bin_index': bin_idx,
                'n_planets': len(bin_data),
                'gap_location': np.nan,
                'gap_std': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'status': 'unimodal_or_outliers'
            })
            continue
        
        try:
            # Fit GMM
            gmm, bic = fit_gmm_vectorized(radii_clean, n_components=2)
            
            # Check BIC against 1-component model
            gmm_1, bic_1 = fit_gmm_vectorized(radii_clean, n_components=1)
            bic_diff = bic_1 - bic
            
            if bic_diff < 10:
                # Unimodal
                results.append({
                    'bin_index': bin_idx,
                    'n_planets': len(bin_data),
                    'gap_location': np.nan,
                    'gap_std': np.nan,
                    'ci_lower': np.nan,
                    'ci_upper': np.nan,
                    'status': 'unresolved',
                    'bic_diff': bic_diff
                })
                continue
            
            # Calculate gap location
            gap, lower, upper = calculate_gap_location_vectorized(gmm)
            
            # Bootstrap for uncertainty
            mean_gap, std_gap, ci = bootstrap_gap_vectorized(
                radii_clean, n_bootstrap=n_bootstrap
            )
            
            results.append({
                'bin_index': bin_idx,
                'n_planets': len(bin_data),
                'gap_location': mean_gap,
                'gap_std': std_gap,
                'ci_lower': ci[0],
                'ci_upper': ci[1],
                'status': 'resolved',
                'bic_diff': bic_diff
            })
            
        except Exception as e:
            logger.warning(f"Failed to fit bin {bin_idx}: {e}")
            results.append({
                'bin_index': bin_idx,
                'n_planets': len(bin_data),
                'gap_location': np.nan,
                'gap_std': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'status': 'fit_failed',
                'error': str(e)
            })
    
    return pd.DataFrame(results)

def main() -> None:
    """
    Main entry point for vectorized GMM fitting.
    Reads from data/processed/binned_planets.csv and outputs to data/processed/gap_locations.csv
    """
    logger.info("Starting vectorized GMM fitting pipeline")
    
    input_path = Path("data/processed/binned_planets.csv")
    output_path = Path("data/processed/gap_locations.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    
    if 'bin_index' not in df.columns or 'radius' not in df.columns:
        logger.error("Missing required columns in input data")
        sys.exit(1)
    
    # Process bins
    gap_results = process_binned_data_vectorized(
        df,
        radius_col='radius',
        bin_col='bin_index',
        min_bin_size=30,
        n_bootstrap=50
    )
    
    # Save results
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    gap_results.to_csv(output_path, index=False)
    
    logger.info(f"Saved gap locations for {len(gap_results)} bins to {output_path}")

if __name__ == "__main__":
    main()
