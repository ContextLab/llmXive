"""
Analysis script to generate statistical results from halo shape and galaxy property data.

This script performs:
1. Mass-matching between shape bins
2. Non-parametric statistical tests (Kruskal-Wallis, Mann-Whitney U, KS)
3. Linear regression with mass control
4. Bonferroni correction for multiple comparisons

Output: data/processed/statistical_results.csv
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_data_processed_path, load_config
from utils.logging import get_pipeline_logger, log_pipeline_start, log_pipeline_end, log_error, log_metric
from analysis.stats import (
    apply_bonferroni_correction,
    kruskal_wallis_test,
    mann_whitney_u_test,
    ks_test,
    nearest_neighbor_matching,
    linear_regression_with_mass_control
)
from processing.shape_metrics import bin_halo_by_shape

def load_halo_data() -> pd.DataFrame:
    """Load processed halo shapes data."""
    data_path = get_data_processed_path()
    input_file = data_path / "halo_shapes.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Loading halo data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Validate required columns
    required_cols = ['halo_id', 'mass', 'b_a_ratio', 'c_a_ratio', 'triaxiality', 'n_particles']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} haloes")
    return df

def load_galaxy_properties() -> pd.DataFrame:
    """Load galaxy property data (SFR, radius, etc.)."""
    data_path = get_data_processed_path()
    input_file = data_path / "galaxy_properties.csv"
    
    if not input_file.exists():
        # If galaxy properties don't exist, create a minimal mock for testing
        # In production, this should be loaded from real data
        logger.warning(f"Galaxy properties file not found: {input_file}. Creating minimal mock data.")
        return pd.DataFrame({
            'halo_id': [],
            'sfr': [],
            'radius': []
        })
    
    logger.info(f"Loading galaxy properties from {input_file}")
    df = pd.read_csv(input_file)
    return df

def merge_halo_galaxy_data(halo_df: pd.DataFrame, galaxy_df: pd.DataFrame) -> pd.DataFrame:
    """Merge halo shape data with galaxy properties."""
    if len(galaxy_df) == 0:
        # If no galaxy data, use halo data as-is for shape-only analysis
        logger.warning("No galaxy properties available. Running shape-only analysis.")
        return halo_df
    
    merged = pd.merge(halo_df, galaxy_df, on='halo_id', how='inner')
    logger.info(f"Merged dataset: {len(merged)} haloes with galaxy properties")
    return merged

def run_statistical_tests(df: pd.DataFrame, logger: logging.Logger) -> List[Dict[str, Any]]:
    """Run all statistical tests and collect results."""
    results = []
    
    # Define shape bins
    bins = [
        ('prolate', lambda x: x['c_a_ratio'] < 0.5),
        ('triaxial', lambda x: (x['c_a_ratio'] >= 0.5) & (x['c_a_ratio'] < 0.8)),
        ('spherical', lambda x: x['c_a_ratio'] >= 0.8)
    ]
    
    # Apply bins
    df['shape_bin'] = df.apply(lambda x: bin_halo_by_shape(x['c_a_ratio']), axis=1)
    
    # Check if we have galaxy properties
    has_galaxy_props = 'sfr' in df.columns and 'radius' in df.columns
    
    if has_galaxy_props:
        # Run tests for SFR
        logger.info("Running statistical tests for SFR vs shape bins")
        sfr_results = run_tests_for_property(df, 'sfr', bins, logger)
        results.extend(sfr_results)
        
        # Run tests for radius
        logger.info("Running statistical tests for radius vs shape bins")
        radius_results = run_tests_for_property(df, 'radius', bins, logger)
        results.extend(radius_results)
    else:
        # Run tests for shape metrics themselves if no galaxy properties
        logger.info("No galaxy properties available. Running tests on shape metrics.")
        for metric in ['triaxiality', 'b_a_ratio']:
            metric_results = run_tests_for_metric(df, metric, bins, logger)
            results.extend(metric_results)
    
    return results

def run_tests_for_property(df: pd.DataFrame, property_name: str, bins: List, logger: logging.Logger) -> List[Dict[str, Any]]:
    """Run statistical tests for a specific galaxy property."""
    results = []
    
    # Apply mass matching
    logger.info(f"Performing mass matching for {property_name}")
    matched_df = nearest_neighbor_matching(df, 'mass', bins, logger)
    
    if len(matched_df) == 0:
        logger.warning("No matched data after mass matching")
        return results
    
    # Kruskal-Wallis test
    kws_result = kruskal_wallis_test(matched_df, property_name, 'shape_bin', logger)
    results.append({
        'property': property_name,
        'test': 'kruskal_wallis',
        'statistic': kws_result['statistic'],
        'p_value': kws_result['p_value'],
        'significant_at_0.01': kws_result['p_value'] < 0.01,
        'significant_at_0.05': kws_result['p_value'] < 0.05
    })
    
    # Mann-Whitney U tests for pairwise comparisons
    bin_names = sorted(matched_df['shape_bin'].unique())
    for i, bin1 in enumerate(bin_names):
        for bin2 in bin_names[i+1:]:
            mwu_result = mann_whitney_u_test(matched_df, property_name, 'shape_bin', bin1, bin2, logger)
            results.append({
                'property': property_name,
                'test': 'mann_whitney_u',
                'group1': bin1,
                'group2': bin2,
                'statistic': mwu_result['statistic'],
                'p_value': mwu_result['p_value'],
                'significant_at_0.01': mwu_result['p_value'] < 0.01,
                'significant_at_0.05': mwu_result['p_value'] < 0.05
            })
    
    # KS tests for pairwise comparisons
    for i, bin1 in enumerate(bin_names):
        for bin2 in bin_names[i+1:]:
            ks_result = ks_test(matched_df, property_name, 'shape_bin', bin1, bin2, logger)
            results.append({
                'property': property_name,
                'test': 'ks_test',
                'group1': bin1,
                'group2': bin2,
                'statistic': ks_result['statistic'],
                'p_value': ks_result['p_value'],
                'significant_at_0.01': ks_result['p_value'] < 0.01,
                'significant_at_0.05': ks_result['p_value'] < 0.05
            })
    
    # Linear regression with mass control
    logger.info(f"Running linear regression for {property_name} with mass control")
    regression_results = linear_regression_with_mass_control(matched_df, property_name, 'shape_bin', logger)
    for shape_bin, coeffs in regression_results['coefficients'].items():
        results.append({
            'property': property_name,
            'test': 'linear_regression',
            'shape_bin': shape_bin,
            'intercept': coeffs['intercept'],
            'mass_coefficient': coeffs['mass_coefficient'],
            'shape_coefficient': coeffs['shape_coefficient'],
            'r_squared': regression_results['r_squared'],
            'p_value_mass': coeffs['p_value_mass'],
            'p_value_shape': coeffs['p_value_shape']
        })
    
    return results

def run_tests_for_metric(df: pd.DataFrame, metric_name: str, bins: List, logger: logging.Logger) -> List[Dict[str, Any]]:
    """Run statistical tests for shape metrics when no galaxy properties are available."""
    results = []
    
    # Kruskal-Wallis test on the metric itself across bins
    kws_result = kruskal_wallis_test(df, metric_name, 'shape_bin', logger)
    results.append({
        'property': metric_name,
        'test': 'kruskal_wallis',
        'statistic': kws_result['statistic'],
        'p_value': kws_result['p_value'],
        'significant_at_0.01': kws_result['p_value'] < 0.01,
        'significant_at_0.05': kws_result['p_value'] < 0.05
    })
    
    return results

def apply_bonferroni_correction(results: List[Dict[str, Any]], logger: logging.Logger) -> List[Dict[str, Any]]:
    """Apply Bonferroni correction to all p-values."""
    if len(results) == 0:
        return results
    
    # Count number of tests
    n_tests = len(results)
    logger.info(f"Applying Bonferroni correction to {n_tests} tests")
    
    corrected_results = apply_bonferroni_correction(results, n_tests, logger)
    
    # Add corrected significance flags
    for result in corrected_results:
        if 'p_value' in result:
            result['corrected_p_value'] = result['p_value'] * n_tests
            result['significant_corrected'] = result['corrected_p_value'] < 0.05
        else:
            result['corrected_p_value'] = None
            result['significant_corrected'] = None
    
    return corrected_results

def main():
    """Main entry point for statistical analysis."""
    # Setup logging
    logger = get_pipeline_logger('statistical_analysis')
    log_pipeline_start(logger, 'T025')
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Loaded configuration: {config}")
        
        # Load data
        halo_df = load_halo_data()
        galaxy_df = load_galaxy_properties()
        
        # Merge data
        merged_df = merge_halo_galaxy_data(halo_df, galaxy_df)
        
        if len(merged_df) == 0:
            raise ValueError("No data available for analysis after merging")
        
        # Run statistical tests
        logger.info("Running statistical tests")
        raw_results = run_statistical_tests(merged_df, logger)
        
        # Apply Bonferroni correction
        logger.info("Applying Bonferroni correction")
        corrected_results = apply_bonferroni_correction(raw_results, logger)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(corrected_results)
        
        # Add metadata
        results_df['associational_only'] = True
        results_df['analysis_timestamp'] = pd.Timestamp.now().isoformat()
        results_df['n_haloes_analyzed'] = len(merged_df)
        
        # Save results
        output_dir = get_data_processed_path()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "statistical_results.csv"
        
        results_df.to_csv(output_file, index=False)
        logger.info(f"Saved statistical results to {output_file}")
        
        # Log metrics
        log_metric(logger, 'n_tests_run', len(corrected_results))
        log_metric(logger, 'n_haloes_analyzed', len(merged_df))
        n_sig = len(results_df[results_df.get('significant_corrected', pd.Series([False]*len(results_df))) == True])
        log_metric(logger, 'n_significant_results', n_sig)
        
        log_pipeline_end(logger, 'T025', success=True)
        
    except Exception as e:
        log_error(logger, 'T025', str(e))
        raise

if __name__ == '__main__':
    main()