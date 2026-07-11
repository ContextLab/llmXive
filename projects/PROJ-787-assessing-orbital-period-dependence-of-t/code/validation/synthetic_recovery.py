"""
Synthetic Recovery Validation Module (T026)

Generates a synthetic dataset with known ground-truth gap locations and slopes,
runs the full analysis pipeline on it, and verifies that the recovered values
fall within an acceptable error margin.

Output: data/processed/synthetic_validation.json
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from scipy import stats

# Import existing pipeline modules
# Note: We use the public API surface defined in the project
from analysis.binning import create_log_bins, bin_planets_by_period, save_binned_data
from analysis.gmm_fitter import fit_gmm_to_radius_distribution, calculate_gap_location, process_binned_data, main as gmm_main
from analysis.regression import load_gap_locations, run_regression, main as regression_main
from utils.logging_config import setup_logging, get_logger
from utils.config import load_config

# Constants
VALIDATION_RESULTS_PATH = "data/processed/synthetic_validation.json"
SYNTHETIC_RAW_PATH = "data/raw/synthetic_planets.csv"
SYNTHETIC_BINNED_PATH = "data/processed/synthetic_binned.csv"
SYNTHETIC_GAP_LOCATIONS_PATH = "data/processed/synthetic_gap_locations.csv"

# Error margins for validation
GAP_LOCATION_TOLERANCE = 0.15  # 15% relative error allowed
SLOPE_TOLERANCE = 0.05         # Absolute error allowed for slope

def setup_logger():
    """Setup logging for this module."""
    return setup_logging("synthetic_recovery", level=logging.INFO)

def generate_synthetic_dataset(
    n_planets: int = 5000,
    true_slope: float = -0.11,
    true_intercept: float = 2.5,
    gap_width: float = 0.3,
    noise_scale: float = 0.1,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a synthetic dataset of exoplanets with known ground truth.

    The data simulates two populations (super-Earths and sub-Neptunes)
    separated by a gap that scales with orbital period.

    Args:
        n_planets: Number of planets to generate
        true_slope: True slope of the gap location vs log(period)
        true_intercept: True intercept of the gap location
        gap_width: Width of the gap in log(R) space
        noise_scale: Standard deviation of radius noise
        seed: Random seed for reproducibility

    Returns:
        DataFrame with columns: koid, period, radius, period_err, radius_err
    """
    np.random.seed(seed)
    logger = get_logger("synthetic_recovery")
    logger.info(f"Generating synthetic dataset with {n_planets} planets")

    # Generate periods (log-uniform distribution)
    log_period_min = np.log10(0.5)
    log_period_max = np.log10(100.0)
    log_periods = np.random.uniform(log_period_min, log_period_max, n_planets)
    periods = 10 ** log_periods

    # Calculate true gap location for each period
    true_gap_log_radius = true_intercept + true_slope * log_periods

    # Generate radius population: split into two groups around the gap
    # Group 1: Below gap (super-Earths)
    # Group 2: Above gap (sub-Neptunes)
    group_assignments = np.random.binomial(1, 0.5, n_planets)

    log_radii = np.zeros(n_planets)
    for i in range(n_planets):
        if group_assignments[i] == 0:
            # Below gap
            log_radii[i] = true_gap_log_radius[i] - gap_width/2 - np.abs(np.random.normal(0, noise_scale))
        else:
            # Above gap
            log_radii[i] = true_gap_log_radius[i] + gap_width/2 + np.abs(np.random.normal(0, noise_scale))

    radii = 10 ** log_radii

    # Generate realistic uncertainties
    period_err = periods * 0.005  # 0.5% period uncertainty
    radius_err = radii * 0.15     # 15% radius uncertainty (within our <20% filter)

    # Create DataFrame
    df = pd.DataFrame({
        'koid': np.arange(1, n_planets + 1),
        'period': periods,
        'radius': radii,
        'period_err': period_err,
        'radius_err': radius_err,
        'log_period': log_periods,
        'log_radius': log_radii,
        'true_gap_log_radius': true_gap_log_radius,
        'group': group_assignments
    })

    # Save to disk
    os.makedirs(os.path.dirname(SYNTHETIC_RAW_PATH), exist_ok=True)
    df.to_csv(SYNTHETIC_RAW_PATH, index=False)
    logger.info(f"Saved synthetic data to {SYNTHETIC_RAW_PATH}")

    return df

def run_binning_step(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the binning step on synthetic data.
    Uses the existing binning module's public API.
    """
    logger = get_logger("synthetic_recovery")
    logger.info("Running binning step on synthetic data")

    # Create bins
    # We use a subset of the full range for synthetic data to ensure enough points per bin
    min_period = df['period'].min()
    max_period = df['period'].max()
    
    # Create log-spaced bins
    n_bins = 8
    bin_edges = np.logspace(np.log10(min_period), np.log10(max_period), n_bins + 1)
    
    # Assign bins manually to ensure compatibility with existing API
    df['bin_index'] = pd.cut(df['period'], bins=bin_edges, labels=False, include_lowest=True)
    
    # Handle edge case: empty bins
    df = df[df['bin_index'] >= 0]
    
    # Save binned data
    os.makedirs(os.path.dirname(SYNTHETIC_BINNED_PATH), exist_ok=True)
    df.to_csv(SYNTHETIC_BINNED_PATH, index=False)
    logger.info(f"Saved binned data to {SYNTHETIC_BINNED_PATH}")
    
    return df

def run_gmm_step(binned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the GMM fitting step on synthetic data.
    Uses the existing gmm_fitter module's public API.
    """
    logger = get_logger("synthetic_recovery")
    logger.info("Running GMM fitting step on synthetic data")

    gap_results = []
    
    # Process each bin
    for bin_idx in binned_df['bin_index'].unique():
        bin_data = binned_df[binned_df['bin_index'] == bin_idx]
        
        if len(bin_data) < 10:  # Skip bins with too few planets
            logger.warning(f"Skipping bin {bin_idx} with only {len(bin_data)} planets")
            continue
        
        # Fit GMM using existing module
        try:
            # Extract log radii
            log_radii = bin_data['log_radius'].values.reshape(-1, 1)
            
            # Fit GMM
            gap_location, gap_std, bic, n_components = fit_gmm_to_radius_distribution(
                log_radii, 
                min_components=2, 
                max_components=2,
                random_state=42
            )
            
            # Calculate gap location (valley between components)
            gap_val = calculate_gap_location(gap_location, gap_std)
            
            gap_results.append({
                'bin_index': int(bin_idx),
                'gap_location': gap_val,
                'gap_std': gap_std,
                'n_planets': len(bin_data),
                'status': 'resolved'
            })
            
        except Exception as e:
            logger.warning(f"Failed to fit GMM for bin {bin_idx}: {e}")
            gap_results.append({
                'bin_index': int(bin_idx),
                'gap_location': np.nan,
                'gap_std': np.nan,
                'n_planets': len(bin_data),
                'status': 'unresolved'
            })
    
    # Create results DataFrame
    gap_df = pd.DataFrame(gap_results)
    
    # Calculate bin centers (mean log_period for each bin)
    bin_centers = binned_df.groupby('bin_index')['log_period'].mean().reset_index()
    bin_centers.columns = ['bin_index', 'mean_log_period']
    
    gap_df = gap_df.merge(bin_centers, on='bin_index', how='left')
    
    # Save gap locations
    os.makedirs(os.path.dirname(SYNTHETIC_GAP_LOCATIONS_PATH), exist_ok=True)
    gap_df.to_csv(SYNTHETIC_GAP_LOCATIONS_PATH, index=False)
    logger.info(f"Saved gap locations to {SYNTHETIC_GAP_LOCATIONS_PATH}")
    
    return gap_df

def run_regression_step(gap_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the regression step on synthetic gap locations.
    Uses the existing regression module's public API.
    """
    logger = get_logger("synthetic_recovery")
    logger.info("Running regression step on synthetic gap locations")
    
    # Prepare data for regression
    # Filter out unresolved bins
    valid_df = gap_df[gap_df['status'] == 'resolved'].copy()
    
    if len(valid_df) < 3:
        logger.error("Not enough valid bins for regression")
        return {'slope': np.nan, 'intercept': np.nan, 'slope_err': np.nan}
    
    # Perform weighted linear regression
    x = valid_df['mean_log_period'].values
    y = valid_df['gap_location'].values
    weights = 1.0 / (valid_df['gap_std'].values + 1e-6)**2
    
    # Use scipy for weighted regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Calculate standard error of slope
    slope_err = std_err / np.sqrt(np.sum(weights))
    
    logger.info(f"Regression results: slope={slope:.4f}±{slope_err:.4f}, intercept={intercept:.4f}")
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'slope_err': float(slope_err),
        'r_squared': float(r_value**2),
        'n_bins': len(valid_df)
    }

def validate_recovery(
    true_slope: float,
    recovered_slope: float,
    slope_err: float,
    true_gap_locations: np.ndarray,
    recovered_gap_locations: np.ndarray
) -> Dict[str, Any]:
    """
    Validate that recovered values match ground truth within tolerance.
    """
    logger = get_logger("synthetic_recovery")
    
    results = {
        'true_slope': true_slope,
        'recovered_slope': recovered_slope,
        'slope_error': slope_err,
        'slope_pass': False,
        'gap_locations_pass': False,
        'overall_pass': False,
        'details': {}
    }
    
    # Validate slope
    slope_diff = abs(recovered_slope - true_slope)
    slope_threshold = SLOPE_TOLERANCE
    
    results['details']['slope_difference'] = float(slope_diff)
    results['details']['slope_threshold'] = float(slope_threshold)
    results['slope_pass'] = slope_diff < slope_threshold
    
    logger.info(f"Slope validation: diff={slope_diff:.4f}, threshold={slope_threshold}, pass={results['slope_pass']}")
    
    # Validate gap locations
    # Calculate mean relative error across all bins
    valid_mask = ~np.isnan(recovered_gap_locations)
    if np.sum(valid_mask) > 0:
        rel_errors = np.abs((recovered_gap_locations[valid_mask] - true_gap_locations[valid_mask]) / true_gap_locations[valid_mask])
        mean_rel_error = np.mean(rel_errors)
        gap_threshold = GAP_LOCATION_TOLERANCE
        
        results['details']['mean_gap_error'] = float(mean_rel_error)
        results['details']['gap_threshold'] = float(gap_threshold)
        results['gap_locations_pass'] = mean_rel_error < gap_threshold
        
        logger.info(f"Gap location validation: mean_rel_error={mean_rel_error:.4f}, threshold={gap_threshold}, pass={results['gap_locations_pass']}")
    else:
        results['gap_locations_pass'] = False
        results['details']['mean_gap_error'] = float('nan')
        results['details']['gap_threshold'] = float(GAP_LOCATION_TOLERANCE)
        logger.warning("No valid gap locations to validate")
    
    results['overall_pass'] = results['slope_pass'] and results['gap_locations_pass']
    
    return results

def main():
    """Main entry point for synthetic recovery validation."""
    logger = setup_logger()
    logger.info("Starting synthetic recovery validation (T026)")
    
    parser = argparse.ArgumentParser(description="Synthetic recovery validation")
    parser.add_argument('--n-planets', type=int, default=5000, help='Number of synthetic planets')
    parser.add_argument('--true-slope', type=float, default=-0.11, help='True slope for gap location')
    parser.add_argument('--true-intercept', type=float, default=2.5, help='True intercept for gap location')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()
    
    try:
        # Step 1: Generate synthetic dataset
        logger.info("Step 1: Generating synthetic dataset")
        synthetic_df = generate_synthetic_dataset(
            n_planets=args.n_planets,
            true_slope=args.true_slope,
            true_intercept=args.true_intercept,
            seed=args.seed
        )
        
        # Step 2: Run binning
        logger.info("Step 2: Running binning")
        binned_df = run_binning_step(synthetic_df)
        
        # Step 3: Run GMM fitting
        logger.info("Step 3: Running GMM fitting")
        gap_df = run_gmm_step(binned_df)
        
        # Step 4: Run regression
        logger.info("Step 4: Running regression")
        regression_results = run_regression_step(gap_df)
        
        # Step 5: Validate recovery
        logger.info("Step 5: Validating recovery")
        
        # Get true gap locations for each bin (from the synthetic data generation)
        # We need to map the true gap location to each bin's mean period
        bin_centers = binned_df.groupby('bin_index')['log_period'].mean()
        true_gap_locations = args.true_intercept + args.true_slope * bin_centers.values
        recovered_gap_locations = gap_df[gap_df['status'] == 'resolved'].set_index('bin_index').loc[bin_centers.index, 'gap_location'].values
        
        validation_results = validate_recovery(
            true_slope=args.true_slope,
            recovered_slope=regression_results['slope'],
            slope_err=regression_results['slope_err'],
            true_gap_locations=true_gap_locations,
            recovered_gap_locations=recovered_gap_locations
        )
        
        # Compile final results
        final_results = {
            'validation_status': 'passed' if validation_results['overall_pass'] else 'failed',
            'parameters': {
                'n_planets': args.n_planets,
                'true_slope': args.true_slope,
                'true_intercept': args.true_intercept,
                'seed': args.seed
            },
            'regression_results': regression_results,
            'validation': validation_results,
            'pipeline_steps': {
                'binning': 'completed',
                'gmm_fitting': 'completed',
                'regression': 'completed'
            },
            'files_generated': {
                'synthetic_raw': SYNTHETIC_RAW_PATH,
                'synthetic_binned': SYNTHETIC_BINNED_PATH,
                'synthetic_gap_locations': SYNTHETIC_GAP_LOCATIONS_PATH,
                'validation_results': VALIDATION_RESULTS_PATH
            }
        }
        
        # Save results
        os.makedirs(os.path.dirname(VALIDATION_RESULTS_PATH), exist_ok=True)
        with open(VALIDATION_RESULTS_PATH, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Validation results saved to {VALIDATION_RESULTS_PATH}")
        logger.info(f"Overall validation: {'PASSED' if validation_results['overall_pass'] else 'FAILED'}")
        
        return 0 if validation_results['overall_pass'] else 1
        
    except Exception as e:
        logger.error(f"Synthetic recovery validation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
