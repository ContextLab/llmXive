"""
Sensitivity Analysis Script for Halo Shape Thresholds (Task T030)

This script performs a sensitivity sweep over shape binning thresholds to verify
the robustness of statistical results (specifically p-values) against threshold choices.

It reads the primary statistical results from data/processed/statistical_results.csv,
recomputes statistics using varied thresholds, and outputs a sensitivity report.

It validates Success Criterion SC-003: P-value variance <= 0.001.
"""
import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

# Project imports based on API surface
from utils.config import get_project_root, get_data_processed_path, get_output_path
from analysis.metadata_utils import load_metadata, save_metadata

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants for SC-003
SC_003_VARIANCE_THRESHOLD = 0.001

# Threshold sweep parameters
# We vary the boundaries for the three bins:
# Bin 1 (Prolate): c/a < threshold_low
# Bin 2 (Triaxial): threshold_low <= c/a < threshold_high
# Bin 3 (Spherical): c/a >= threshold_high
# Base thresholds from T020: 0.5 and 0.8
THRESHOLD_SWEEP_LOW = [0.4, 0.45, 0.5, 0.55, 0.6]
THRESHOLD_SWEEP_HIGH = [0.7, 0.75, 0.8, 0.85, 0.9]

def load_statistical_results() -> pd.DataFrame:
    """Load the primary statistical results file."""
    input_path = get_data_processed_path() / "statistical_results.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                "Ensure T025 (generate_statistical_results) has been run.")
    return pd.read_csv(input_path)

def recompute_bin_assignments(df: pd.DataFrame, low_thresh: float, high_thresh: float) -> pd.Series:
    """
    Reassign bins based on new thresholds.
    Assumes the input df has a 'c_a_ratio' column (or similar) and a 'shape_bin' column.
    We will re-derive the bin based on 'c_a_ratio' if available, otherwise we assume
    the input df contains the raw shape metrics needed to re-bin.
    
    If 'c_a_ratio' is not present, we attempt to infer it or raise an error.
    """
    if 'c_a_ratio' not in df.columns:
        # Fallback: try to find a column that looks like c/a
        candidates = [c for c in df.columns if 'c_a' in c.lower() or 'c/a' in c]
        if candidates:
            col = candidates[0]
            logger.warning(f"Column 'c_a_ratio' not found. Using '{col}' as proxy for c/a ratio.")
            c_a_col = col
        else:
            raise ValueError("Could not find 'c_a_ratio' or similar column to re-bin data.")
    else:
        c_a_col = 'c_a_ratio'

    def assign_bin(c_a):
        if pd.isna(c_a):
            return np.nan
        if c_a < low_thresh:
            return 'prolate'
        elif c_a < high_thresh:
            return 'triaxial'
        else:
            return 'spherical'

    return df[c_a_col].apply(assign_bin)

def run_statistical_test_for_binning(df: pd.DataFrame, low_thresh: float, high_thresh: float) -> Dict[str, float]:
    """
    Run a simplified statistical test (e.g., Kruskal-Wallis on SFR vs Shape Bin)
    for the given thresholds.
    
    We assume the statistical_results.csv contains the raw data or summary stats needed.
    However, typically statistical_results.csv contains the *results* (p-values), not the raw data.
    If the input file only contains results, we cannot re-run the test without the raw data.
    
    Strategy:
    1. Check if the input file has raw data columns (e.g., 'SFR', 'c_a_ratio', 'shape_bin').
    2. If yes, re-bin and re-run Kruskal-Wallis.
    3. If no, we must load the raw halo_shapes.csv (from T017) and merge with galaxy properties.
    
    For robustness, we will attempt to load the raw data if the results file is just summaries.
    """
    # Check if we have raw data columns
    has_raw_sfr = 'SFR' in df.columns
    has_raw_shape = 'c_a_ratio' in df.columns or 'shape_bin' in df.columns

    if has_raw_sfr and has_raw_shape:
        # Re-bin
        new_bins = recompute_bin_assignments(df, low_thresh, high_thresh)
        df_temp = df.copy()
        df_temp['shape_bin'] = new_bins
        
        # Drop NaN bins
        valid_mask = df_temp['shape_bin'].notna()
        if valid_mask.sum() < 3:
            return {'p_value': np.nan, 'status': 'insufficient_data'}
        
        df_valid = df_temp[valid_mask]
        
        # Perform Kruskal-Wallis test: SFR ~ shape_bin
        # We need to group by bin
        groups = [group['SFR'].values for name, group in df_valid.groupby('shape_bin') if len(group) > 0]
        
        if len(groups) < 2:
            return {'p_value': np.nan, 'status': 'not_enough_groups'}
        
        try:
            stat, p_val = scipy_stats.kruskal(*groups)
            return {'p_value': float(p_val), 'status': 'success'}
        except Exception as e:
            logger.warning(f"Kruskal-Wallis failed for thresholds ({low_thresh}, {high_thresh}): {e}")
            return {'p_value': np.nan, 'status': 'test_failed'}
    else:
        # We need to load raw data from halo_shapes.csv and merge
        # This implies we need the galaxy properties too. 
        # To keep this script self-contained and robust, we assume the input statistical_results.csv
        # might be a summary. If it's a summary, we can't re-run without raw data.
        # Let's assume the project provides a merged raw file or we need to load halo_shapes.csv.
        # Given the constraints, we will try to load halo_shapes.csv which should have c_a_ratio.
        # We need SFR. If SFR is not in halo_shapes, we might need to load galaxy properties.
        
        # Attempt to load halo_shapes.csv
        halo_path = get_data_processed_path() / "halo_shapes.csv"
        if not halo_path.exists():
            raise FileNotFoundError(f"Cannot re-run test: {halo_path} not found. "
                                    "The statistical_results.csv appears to be summary-only. "
                                    "Raw data (halo_shapes.csv) is required for sensitivity analysis.")
        
        raw_df = pd.read_csv(halo_path)
        
        # Check for SFR
        if 'SFR' not in raw_df.columns:
            # Try to load galaxy properties if available
            gal_path = get_data_processed_path() / "galaxy_properties.csv"
            if gal_path.exists():
                gal_df = pd.read_csv(gal_path)
                # Assume a merge key exists, e.g., 'halo_id' or 'group_id'
                merge_key = None
                for key in ['halo_id', 'group_id', 'id']:
                    if key in raw_df.columns and key in gal_df.columns:
                        merge_key = key
                        break
                
                if merge_key:
                    merged = pd.merge(raw_df, gal_df, on=merge_key, how='inner')
                    if 'SFR' in merged.columns:
                        raw_df = merged
                    else:
                        raise ValueError("SFR not found in merged data.")
                else:
                    raise ValueError("Cannot merge halo_shapes and galaxy_properties: no common key found.")
            else:
                raise ValueError("SFR not found in halo_shapes.csv and galaxy_properties.csv not found.")

        # Now run the test on raw_df
        new_bins = recompute_bin_assignments(raw_df, low_thresh, high_thresh)
        raw_df['shape_bin'] = new_bins
        
        valid_mask = raw_df['shape_bin'].notna()
        if valid_mask.sum() < 3:
            return {'p_value': np.nan, 'status': 'insufficient_data'}
        
        df_valid = raw_df[valid_mask]
        groups = [group['SFR'].values for name, group in df_valid.groupby('shape_bin') if len(group) > 0]
        
        if len(groups) < 2:
            return {'p_value': np.nan, 'status': 'not_enough_groups'}
        
        try:
            stat, p_val = scipy_stats.kruskal(*groups)
            return {'p_value': float(p_val), 'status': 'success'}
        except Exception as e:
            logger.warning(f"Kruskal-Wallis failed for thresholds ({low_thresh}, {high_thresh}): {e}")
            return {'p_value': np.nan, 'status': 'test_failed'}

def calculate_variance(p_values: List[float]) -> float:
    """Calculate variance of a list of p-values, ignoring NaNs."""
    valid_p = [p for p in p_values if not np.isnan(p)]
    if len(valid_p) < 2:
        return np.nan
    return float(np.var(valid_p))

def run_sensitivity_analysis():
    """Main entry point for the sensitivity analysis."""
    logger.info("Starting Sensitivity Analysis (T030)...")
    
    # 1. Load data
    try:
        # Try to load the statistical results first to see if it has raw data
        # If not, we will rely on halo_shapes.csv logic inside the test runner
        df_results = load_statistical_results()
    except FileNotFoundError as e:
        logger.error(str(e))
        # Fallback to direct raw data loading if results file is missing but raw is there
        # But the task depends on T025, so we expect the file.
        raise

    results_rows = []
    p_values = []

    logger.info(f"Sweeping thresholds. Low: {THRESHOLD_SWEEP_LOW}, High: {THRESHOLD_SWEEP_HIGH}")

    for low_t in THRESHOLD_SWEEP_LOW:
        for high_t in THRESHOLD_SWEEP_HIGH:
            # Ensure low < high
            if low_t >= high_t:
                continue
            
            logger.info(f"Testing thresholds: low={low_t}, high={high_t}")
            res = run_statistical_test_for_binning(df_results, low_t, high_t)
            
            row = {
                'threshold_low': low_t,
                'threshold_high': high_t,
                'p_value': res['p_value'],
                'status': res['status']
            }
            results_rows.append(row)
            
            if res['p_value'] is not None and not np.isnan(res['p_value']):
                p_values.append(res['p_value'])

    # 2. Calculate Variance
    variance = calculate_variance(p_values)
    sc_003_passed = False
    sc_003_status = "Unknown"
    
    if not np.isnan(variance):
        sc_003_passed = variance <= SC_003_VARIANCE_THRESHOLD
        sc_003_status = "PASSED" if sc_003_passed else "FAILED"
        logger.info(f"P-value variance: {variance:.6f} (Threshold: {SC_003_VARIANCE_THRESHOLD}). Status: {sc_003_status}")
    else:
        logger.warning("Could not calculate variance due to insufficient valid p-values.")
        sc_003_status = "INSUFFICIENT_DATA"

    # 3. Write Output
    output_path = get_data_processed_path() / "sensitivity_report.csv"
    os.makedirs(output_path.parent, exist_ok=True)
    
    df_output = pd.DataFrame(results_rows)
    df_output.to_csv(output_path, index=False)
    logger.info(f"Sensitivity report written to {output_path}")

    # 4. Update Metadata
    try:
        metadata = load_metadata()
        metadata['success_criteria']['SC-003'] = {
            'status': sc_003_status,
            'details': f"P-value variance: {variance:.6f}. Threshold: {SC_003_VARIANCE_THRESHOLD}.",
            'variance': variance,
            'passed': sc_003_passed
        }
        save_metadata(metadata)
        logger.info("Updated data/metadata.yaml with SC-003 status.")
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")

    return df_output, variance, sc_003_passed

def main():
    try:
        run_sensitivity_analysis()
        logger.info("Sensitivity Analysis completed successfully.")
    except Exception as e:
        logger.critical(f"Sensitivity Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
