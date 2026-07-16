"""
KDE Validator for Gap Location Verification.

This module implements a non-parametric validation of the gap location
identified by the Gaussian Mixture Model (GMM). It uses Kernel Density
Estimation (KDE) to identify the gap location independently and verifies
that it falls within the confidence interval derived from the GMM bootstrap.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

# Project root adjustment for execution context
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger

# Configuration
KDE_BANDWIDTH_METHOD = 'scott'  # Options: 'scott', 'silverman'
MIN_DENSITY_THRESHOLD = 0.05  # Minimum density relative to max to consider a point valid
GAP_WINDOW_SIZE = 0.1  # Width of window around GMM gap to search for KDE minimum

logger = get_logger(__name__)


def load_gap_locations(input_path: str) -> pd.DataFrame:
    """
    Load gap locations from the GMM output.

    Args:
        input_path: Path to the gap_locations.csv file.

    Returns:
        DataFrame containing gap locations and uncertainties.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Gap locations file not found: {input_path}")

    df = pd.read_csv(path)
    required_cols = ['bin_index', 'gap_location', 'gap_uncertainty', 'ci_lower', 'ci_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Gap locations file missing required columns: {missing_cols}")

    return df


def estimate_kde_gap(radius_data: np.ndarray) -> Optional[float]:
    """
    Estimate the gap location using Kernel Density Estimation.

    The gap is identified as the local minimum in the density distribution
    between the two peaks (super-Earths and sub-Neptunes).

    Args:
        radius_data: Array of planet radii for a specific period bin.

    Returns:
        Estimated gap location (radius) or None if no gap is found.
    """
    if len(radius_data) < 10:
        logger.warning("Insufficient data points for KDE estimation")
        return None

    # Create KDE object
    try:
        kde = gaussian_kde(radius_data, bw_method=KDE_BANDWIDTH_METHOD)
    except Exception as e:
        logger.error(f"KDE fitting failed: {e}")
        return None

    # Define evaluation range
    x_min, x_max = radius_data.min(), radius_data.max()
    x_range = np.linspace(x_min, x_max, 1000)

    # Evaluate density
    density = kde(x_range)

    # Normalize density
    density_norm = density / density.max()

    # Find peaks (local maxima)
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(density_norm, height=MIN_DENSITY_THRESHOLD)

    if len(peaks) < 2:
        logger.info(f"Only {len(peaks)} peak(s) found in KDE, cannot identify gap")
        return None

    # Find the minimum between the first two significant peaks
    # Sort peaks by position
    peaks = np.sort(peaks)
    min_idx = None
    min_density = np.inf

    # Look for the minimum between consecutive peaks
    for i in range(len(peaks) - 1):
        start_idx = peaks[i]
        end_idx = peaks[i + 1]

        # Find minimum in this range
        range_density = density_norm[start_idx:end_idx]
        if len(range_density) > 0:
            local_min_idx = np.argmin(range_density)
            if density_norm[start_idx + local_min_idx] < min_density:
                min_density = density_norm[start_idx + local_min_idx]
                min_idx = start_idx + local_min_idx

    if min_idx is not None:
        return x_range[min_idx]

    return None


def validate_gap_location(gap_df: pd.DataFrame, data_dir: Path) -> Dict[str, Any]:
    """
    Validate GMM gap locations against KDE estimates.

    For each period bin, this function:
    1. Loads the planet radii for that bin
    2. Estimates the gap location using KDE
    3. Checks if the KDE estimate falls within the GMM confidence interval
    4. Records the validation result

    Args:
        gap_df: DataFrame with GMM gap locations and uncertainties.
        data_dir: Directory containing processed planet data.

    Returns:
        Dictionary with validation results.
    """
    results = []
    all_passed = True

    # Load the deduplicated planets data
    planets_path = data_dir / "processed" / "deduped_planets.csv"
    if not planets_path.exists():
        raise FileNotFoundError(f"Planet data not found: {planets_path}")

    planets_df = pd.read_csv(planets_path)

    # Ensure we have the necessary columns
    required_planet_cols = ['koi_planet_number', 'planet_radius', 'orbital_period']
    missing = [col for col in required_planet_cols if col not in planets_df.columns]
    if missing:
        raise ValueError(f"Planet data missing columns: {missing}")

    for _, row in gap_df.iterrows():
        bin_idx = int(row['bin_index'])
        gmm_gap = float(row['gap_location'])
        ci_lower = float(row['ci_lower'])
        ci_upper = float(row['ci_upper'])

        # Filter planets for this bin (assuming bin_index is stored or can be derived)
        # Since binning might not store bin_index in the original data, we need to
        # reconstruct the bin assignment or use the binned_planets.csv
        binned_path = data_dir / "processed" / "binned_planets.csv"
        if binned_path.exists():
            binned_df = pd.read_csv(binned_path)
            bin_data = binned_df[binned_df['bin_index'] == bin_idx]
        else:
            # Fallback: try to derive from period if bin_index is not in original data
            # This is a simplified approach; in practice, we'd need the actual binning logic
            logger.warning(f"Binned data not found, attempting fallback for bin {bin_idx}")
            bin_data = planets_df[planets_df['orbital_period'] > 0]  # Placeholder

        if bin_data.empty:
            logger.warning(f"No data for bin {bin_idx}, skipping validation")
            results.append({
                'bin_index': bin_idx,
                'gmm_gap': gmm_gap,
                'kde_gap': None,
                'validation_passed': False,
                'reason': 'no_data'
            })
            all_passed = False
            continue

        radius_data = bin_data['planet_radius'].dropna().values

        if len(radius_data) < 10:
            logger.warning(f"Insufficient data for bin {bin_idx}, skipping KDE")
            results.append({
                'bin_index': bin_idx,
                'gmm_gap': gmm_gap,
                'kde_gap': None,
                'validation_passed': False,
                'reason': 'insufficient_data'
            })
            all_passed = False
            continue

        kde_gap = estimate_kde_gap(radius_data)

        if kde_gap is None:
            logger.warning(f"KDE gap estimation failed for bin {bin_idx}")
            results.append({
                'bin_index': bin_idx,
                'gmm_gap': gmm_gap,
                'kde_gap': None,
                'validation_passed': False,
                'reason': 'kde_failed'
            })
            all_passed = False
            continue

        # Check if KDE gap is within GMM confidence interval
        # Allow a small tolerance for numerical differences
        tolerance = 0.05  # 5% tolerance
        lower_bound = ci_lower - tolerance
        upper_bound = ci_upper + tolerance

        passed = lower_bound <= kde_gap <= upper_bound

        results.append({
            'bin_index': bin_idx,
            'gmm_gap': gmm_gap,
            'kde_gap': kde_gap,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'validation_passed': passed,
            'reason': 'ok' if passed else 'outside_ci'
        })

        if not passed:
            all_passed = False
            logger.info(f"Bin {bin_idx}: KDE gap {kde_gap:.3f} outside GMM CI [{ci_lower:.3f}, {ci_upper:.3f}]")

    return {
        'validation_passed': all_passed,
        'bin_results': results,
        'summary': {
            'total_bins': len(results),
            'passed_bins': sum(1 for r in results if r['validation_passed']),
            'failed_bins': sum(1 for r in results if not r['validation_passed'])
        }
    }


def save_validation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save validation results to a JSON file.

    Args:
        results: Validation results dictionary.
        output_path: Path for the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation results saved to {output_path}")


def main() -> None:
    """Main entry point for KDE validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    data_dir = PROJECT_ROOT / "data"
    gap_locations_path = data_dir / "processed" / "gap_locations.csv"
    output_path = data_dir / "processed" / "kde_validation.json"

    try:
        logger.info("Loading GMM gap locations...")
        gap_df = load_gap_locations(str(gap_locations_path))
        logger.info(f"Loaded {len(gap_df)} gap locations")

        logger.info("Performing KDE validation...")
        results = validate_gap_location(gap_df, data_dir)

        logger.info(f"Validation summary: {results['summary']}")
        save_validation_results(results, str(output_path))

        if results['validation_passed']:
            logger.info("KDE validation PASSED: All gap locations within confidence intervals")
        else:
            logger.warning("KDE validation FAILED: Some gap locations outside confidence intervals")

    except Exception as e:
        logger.error(f"KDE validation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
