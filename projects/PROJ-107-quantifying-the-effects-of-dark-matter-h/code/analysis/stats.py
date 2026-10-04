"""
Statistical analysis module for User Story 2.
Implements mass-matching, non-parametric tests, regression, and binning logic.
"""
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from typing import Tuple, List, Optional, Dict, Any, Iterator
import logging
import os
import csv
from pathlib import Path
import json

from utils.config import get_project_root, get_data_processed_path
from utils.io import write_csv_with_associational_flag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MASS_TOLERANCE = 0.1  # 10% tolerance for nearest neighbor matching
MIN_PARTICLE_COUNT = 10000    # Minimum particles to include a halo


def nearest_neighbor_matching(
    source_masses: np.ndarray,
    source_ids: np.ndarray,
    target_masses: np.ndarray,
    target_ids: np.ndarray,
    tolerance: float = DEFAULT_MASS_TOLERANCE
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform Nearest-Neighbor Matching between two sets of halo masses.
    
    This function implements a memory-efficient matching algorithm that finds
    the closest mass match in the target set for each source halo, within a
    specified tolerance.
    
    Args:
        source_masses: 1D array of log10(halo mass) values from the source dataset.
        source_ids: 1D array of halo IDs corresponding to source_masses.
        target_masses: 1D array of log10(halo mass) values from the target dataset.
        target_ids: 1D array of halo IDs corresponding to target_masses.
        tolerance: Maximum allowed relative difference in mass (default 0.1 for 10%).
    
    Returns:
        Tuple of (matched_source_indices, matched_target_indices).
        Indices refer to positions in the input arrays.
        If no match is found within tolerance, the source index is -1.
    
    Raises:
        ValueError: If input arrays have mismatched dimensions or are empty.
    """
    if len(source_masses) == 0 or len(target_masses) == 0:
        raise ValueError("Input mass arrays cannot be empty.")
    
    if len(source_masses) != len(source_ids) or len(target_masses) != len(target_ids):
        raise ValueError("Mass and ID arrays must have the same length.")
    
    # Sort target masses to enable efficient nearest neighbor search
    sorted_target_indices = np.argsort(target_masses)
    sorted_target_masses = target_masses[sorted_target_indices]
    sorted_target_ids = target_ids[sorted_target_indices]
    
    matched_source_indices = np.full(len(source_masses), -1, dtype=int)
    matched_target_indices = np.full(len(source_masses), -1, dtype=int)
    
    # For each source halo, find the nearest target within tolerance
    for i, src_mass in enumerate(source_masses):
        # Binary search for insertion point
        idx = np.searchsorted(sorted_target_masses, src_mass)
        
        # Check neighbors around insertion point
        best_dist = float('inf')
        best_idx = -1
        
        # Check a window around the insertion point
        window_start = max(0, idx - 10)
        window_end = min(len(sorted_target_masses), idx + 10)
        
        for j in range(window_start, window_end):
            dist = abs(sorted_target_masses[j] - src_mass)
            if dist < best_dist:
                best_dist = dist
                best_idx = j
        
        # Check if match is within tolerance
        # Tolerance is relative: |mass1 - mass2| / mass1 < tolerance
        if best_idx != -1:
            relative_diff = abs(sorted_target_masses[best_idx] - src_mass) / src_mass
            if relative_diff <= tolerance:
                matched_source_indices[i] = i
                matched_target_indices[i] = sorted_target_indices[best_idx]
    
    return matched_source_indices, matched_target_indices


def stream_mass_matched_chunks(
    halo_shapes_path: str,
    galaxy_properties_path: str,
    output_dir: str,
    tolerance: float = DEFAULT_MASS_TOLERANCE,
    chunk_size: int = 5000
) -> Iterator[str]:
    """
    Stream mass-matched chunks from two large CSV files without loading them entirely into memory.
    
    This function reads halo shapes and galaxy properties in chunks, performs
    nearest-neighbor matching on each chunk pair, and writes matched results
    to separate CSV files in the output directory.
    
    Args:
        halo_shapes_path: Path to halo_shapes.csv (contains halo_id, mass, b_a_ratio, etc.)
        galaxy_properties_path: Path to galaxy_properties.csv (contains galaxy_id, halo_id, mass, etc.)
        output_dir: Directory to write matched chunk files.
        tolerance: Mass matching tolerance (default 0.1).
        chunk_size: Number of rows to process at a time.
    
    Yields:
        Path to each generated matched chunk file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Read halo shapes in chunks
    halo_chunks = pd.read_csv(halo_shapes_path, chunksize=chunk_size)
    galaxy_chunks = pd.read_csv(galaxy_properties_path, chunksize=chunk_size)
    
    chunk_count = 0
    
    try:
        for halo_chunk in halo_chunks:
            galaxy_chunk = next(galaxy_chunks)
            
            # Filter for valid particle counts (already done in T017, but ensure here)
            halo_chunk = halo_chunk[halo_chunk['particle_count'] >= MIN_PARTICLE_COUNT]
            galaxy_chunk = galaxy_chunk[galaxy_chunk['particle_count'] >= MIN_PARTICLE_COUNT]
            
            if len(halo_chunk) == 0 or len(galaxy_chunk) == 0:
                continue
            
            # Extract mass arrays for matching
            # Note: mass is typically stored as log10(M) in TNG data
            halo_masses = halo_chunk['mass'].values.astype(float)
            halo_ids = halo_chunk['halo_id'].values
            
            galaxy_masses = galaxy_chunk['stellar_mass'].values.astype(float)
            galaxy_ids = galaxy_chunk['galaxy_id'].values
            
            # Perform matching
            matched_source_idx, matched_target_idx = nearest_neighbor_matching(
                halo_masses, halo_ids, galaxy_masses, galaxy_ids, tolerance
            )
            
            # Create matched dataset
            matched_halo = []
            matched_galaxy = []
            
            for i, (src_idx, tgt_idx) in enumerate(zip(matched_source_idx, matched_target_idx)):
                if src_idx != -1 and tgt_idx != -1:
                    matched_halo.append(halo_chunk.iloc[src_idx].to_dict())
                    matched_galaxy.append(galaxy_chunk.iloc[tgt_idx].to_dict())
            
            if len(matched_halo) > 0:
                chunk_count += 1
                output_file = os.path.join(output_dir, f"match_{chunk_count:03d}.csv")
                
                # Combine matched data
                matched_df = pd.DataFrame(matched_halo)
                matched_df['matched_galaxy_id'] = [m['galaxy_id'] for m in matched_galaxy]
                matched_df['matched_galaxy_sfr'] = [m['sfr'] for m in matched_galaxy]
                matched_df['matched_galaxy_radius'] = [m['effective_radius'] for m in matched_galaxy]
                matched_df['matched_galaxy_mass'] = [m['stellar_mass'] for m in matched_galaxy]
                
                # Write with associational flag
                write_csv_with_associational_flag(matched_df, output_file)
                logger.info(f"Written matched chunk: {output_file} ({len(matched_df)} rows)")
                yield output_file
    
    except StopIteration:
        # Handle case where galaxy chunks run out before halo chunks
        logger.warning("Galaxy chunks exhausted before halo chunks. Stopping matching.")
    
    logger.info(f"Mass-matching complete. Generated {chunk_count} chunk files.")


def kruskal_wallis_test(
    groups: List[np.ndarray],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Kruskal-Wallis H-test for independent samples.
    
    Args:
        groups: List of 1D arrays, each representing a group of samples.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing:
            - statistic: H statistic
            - p_value: p-value of the test
            - rejected: True if null hypothesis is rejected (p < alpha)
    """
    if len(groups) < 2:
        raise ValueError("At least two groups are required for Kruskal-Wallis test.")
    
    h_stat, p_val = scipy_stats.kruskal(*groups)
    
    return {
        'statistic': float(h_stat),
        'p_value': float(p_val),
        'rejected': bool(p_val < alpha),
        'method': 'kruskal_wallis'
    }


def mann_whitney_u_test(
    group_a: np.ndarray,
    group_b: np.ndarray,
    alternative: str = 'two-sided',
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Mann-Whitney U test for two independent samples.
    
    Args:
        group_a: 1D array of samples from group A.
        group_b: 1D array of samples from group B.
        alternative: 'two-sided', 'less', or 'greater'.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing:
            - statistic: U statistic
            - p_value: p-value of the test
            - rejected: True if null hypothesis is rejected
    """
    u_stat, p_val = scipy_stats.mannwhitneyu(group_a, group_b, alternative=alternative)
    
    return {
        'statistic': float(u_stat),
        'p_value': float(p_val),
        'rejected': bool(p_val < alpha),
        'method': 'mann_whitney_u',
        'alternative': alternative
    }


def ks_test(
    group_a: np.ndarray,
    group_b: np.ndarray,
    alternative: str = 'two-sided',
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov two-sample test.
    
    Args:
        group_a: 1D array of samples from distribution A.
        group_b: 1D array of samples from distribution B.
        alternative: 'two-sided', 'less', or 'greater'.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing:
            - statistic: D statistic
            - p_value: p-value of the test
            - rejected: True if null hypothesis is rejected
    """
    ks_stat, p_val = scipy_stats.ks_2samp(group_a, group_b)
    
    return {
        'statistic': float(ks_stat),
        'p_value': float(p_val),
        'rejected': bool(p_val < alpha),
        'method': 'ks_test',
        'alternative': alternative
    }


def linear_regression_with_mass_control(
    y: np.ndarray,
    x_shape: np.ndarray,
    x_mass: np.ndarray,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform linear regression of y ~ x_shape + x_mass.
    
    This implements a mass-controlled regression to isolate the effect of
    shape parameters on galaxy properties.
    
    Args:
        y: Dependent variable (e.g., SFR).
        x_shape: Independent variable (shape parameter, e.g., triaxiality).
        x_mass: Control variable (halo mass).
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing regression results:
            - coefficients: dict of coefficient names to values
            - p_values: dict of p-values for each coefficient
            - r_squared: R-squared of the model
            - rejected: True if shape coefficient is significant
    """
    import statsmodels.api as sm
    
    # Prepare design matrix
    X = np.column_stack([x_shape, x_mass])
    X = sm.add_constant(X)
    y = np.asarray(y)
    
    # Fit model
    model = sm.OLS(y, X).fit()
    
    # Extract results
    coeffs = model.params
    p_vals = model.pvalues
    r_sq = model.rsquared
    
    # Check significance of shape parameter (index 1)
    shape_p_val = p_vals[1]
    
    return {
        'intercept': float(coeffs[0]),
        'shape_coefficient': float(coeffs[1]),
        'mass_coefficient': float(coeffs[2]),
        'shape_p_value': float(shape_p_val),
        'mass_p_value': float(p_vals[2]),
        'r_squared': float(r_sq),
        'rejected': bool(shape_p_val < alpha),
        'method': 'linear_regression'
    }


def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).
    
    Returns:
        Tuple of (adjusted_p_values, rejected_flags).
        adjusted_p_values: List of Bonferroni-corrected p-values.
        rejected_flags: List of booleans indicating if null is rejected.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], []
    
    adjusted_p_vals = [min(p * n_tests, 1.0) for p in p_values]
    rejected = [p < alpha for p in adjusted_p_vals]
    
    return adjusted_p_vals, rejected


def run_statistical_tests(
    halo_shapes_path: str,
    galaxy_properties_path: str,
    output_dir: str,
    binning_thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Run full statistical analysis pipeline on matched data.
    
    This function orchestrates mass-matching, binning, and statistical tests.
    
    Args:
        halo_shapes_path: Path to halo_shapes.csv.
        galaxy_properties_path: Path to galaxy_properties.csv.
        output_dir: Directory for output files.
        binning_thresholds: Dict with 'prolate', 'triaxial', 'spherical' thresholds.
    
    Returns:
        Dictionary containing all test results.
    """
    if binning_thresholds is None:
        binning_thresholds = {
            'prolate': 0.5,
            'triaxial_upper': 0.8,
            'spherical': 0.8
        }
    
    logger.info("Starting statistical analysis pipeline...")
    
    # Step 1: Perform mass-matching
    matched_chunks_dir = os.path.join(output_dir, "matched_chunks")
    matched_files = list(stream_mass_matched_chunks(
        halo_shapes_path, galaxy_properties_path, matched_chunks_dir
    ))
    
    if not matched_files:
        logger.error("No matched chunks generated. Cannot proceed with analysis.")
        return {'error': 'No matched data found'}
    
    # Step 2: Aggregate matched data
    all_matched_data = []
    for f in matched_files:
        df = pd.read_csv(f)
        all_matched_data.append(df)
    
    combined_df = pd.concat(all_matched_data, ignore_index=True)
    logger.info(f"Combined {len(combined_df)} matched halo-galaxy pairs.")
    
    # Step 3: Bin by shape
    def assign_shape_bin(c_a_ratio):
        if c_a_ratio < binning_thresholds['prolate']:
            return 'prolate'
        elif c_a_ratio <= binning_thresholds['triaxial_upper']:
            return 'triaxial'
        else:
            return 'spherical'
    
    combined_df['shape_bin'] = combined_df['c_a_ratio'].apply(assign_shape_bin)
    
    # Step 4: Run non-parametric tests for each shape bin
    results = {
        'binning_tests': [],
        'regression_results': [],
        'sample_sizes': {}
    }
    
    # Group by shape bin
    shape_groups = combined_df.groupby('shape_bin')
    groups_list = [group['sfr'].values for name, group in shape_groups]
    
    if len(groups_list) >= 2:
        # Kruskal-Wallis test
        kw_result = kruskal_wallis_test(groups_list)
        results['binning_tests'].append(kw_result)
        logger.info(f"Kruskal-Wallis test: H={kw_result['statistic']:.4f}, p={kw_result['p_value']:.6f}")
    
    # Step 5: Linear regression with mass control
    if len(combined_df) > 10:
        # Use triaxiality as shape parameter
        y = combined_df['sfr'].values
        x_shape = combined_df['triaxiality'].values
        x_mass = combined_df['mass'].values  # Halo mass as control
        
        # Remove NaNs
        valid_mask = ~(np.isnan(y) | np.isnan(x_shape) | np.isnan(x_mass))
        if np.sum(valid_mask) > 10:
            reg_result = linear_regression_with_mass_control(
                y[valid_mask], x_shape[valid_mask], x_mass[valid_mask]
            )
            results['regression_results'].append(reg_result)
            logger.info(f"Regression: shape_coeff={reg_result['shape_coefficient']:.6f}, p={reg_result['shape_p_value']:.6f}")
    
    # Step 6: Apply Bonferroni correction if multiple tests
    if results['binning_tests']:
        p_vals = [t['p_value'] for t in results['binning_tests']]
        adj_p, rejected = apply_bonferroni_correction(p_vals)
        for i, test in enumerate(results['binning_tests']):
            test['bonferroni_adjusted_p'] = adj_p[i]
            test['bonferroni_rejected'] = rejected[i]
    
    # Step 7: Save results
    results_path = os.path.join(output_dir, "statistical_results.csv")
    
    # Flatten results for CSV
    rows = []
    for test in results['binning_tests']:
        rows.append({
            'test_type': 'binning_kruskal_wallis',
            'statistic': test['statistic'],
            'p_value': test['p_value'],
            'bonferroni_adjusted_p': test.get('bonferroni_adjusted_p', test['p_value']),
            'rejected': test['rejected'],
            'bonferroni_rejected': test.get('bonferroni_rejected', test['rejected'])
        })
    
    for reg in results['regression_results']:
        rows.append({
            'test_type': 'linear_regression',
            'predictor': 'triaxiality',
            'coefficient': reg['shape_coefficient'],
            'p_value': reg['shape_p_value'],
            'r_squared': reg['r_squared'],
            'rejected': reg['rejected']
        })
    
    if rows:
        df_results = pd.DataFrame(rows)
        write_csv_with_associational_flag(df_results, results_path)
        logger.info(f"Saved statistical results to {results_path}")
    
    return results


def save_statistical_results(results: Dict[str, Any], output_path: str):
    """
    Save statistical analysis results to CSV.
    
    Args:
        results: Dictionary containing test results.
        output_path: Path to output CSV file.
    """
    df = pd.DataFrame(results)
    write_csv_with_associational_flag(df, output_path)
    logger.info(f"Saved statistical results to {output_path}")


def main():
    """Main entry point for statistical analysis."""
    root = get_project_root()
    halo_shapes_path = os.path.join(root, "data", "processed", "halo_shapes.csv")
    galaxy_properties_path = os.path.join(root, "data", "processed", "galaxy_properties.csv")
    output_dir = os.path.join(root, "data", "processed")
    
    if not os.path.exists(halo_shapes_path):
        logger.error(f"Halo shapes file not found: {halo_shapes_path}")
        return
    
    if not os.path.exists(galaxy_properties_path):
        logger.error(f"Galaxy properties file not found: {galaxy_properties_path}")
        return
    
    results = run_statistical_tests(halo_shapes_path, galaxy_properties_path, output_dir)
    logger.info("Statistical analysis complete.")


if __name__ == "__main__":
    main()