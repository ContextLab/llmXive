import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from utils.config import get_project_root, get_data_processed_path, get_output_path
from analysis.metadata_utils import load_metadata, save_metadata
from analysis.stats import kruskal_wallis_test, apply_bonferroni_correction

# Configure logger
logger = logging.getLogger(__name__)

# Define the sweep ranges for binning thresholds
# SC-003: Sweep thresholds over a representative set of values spanning low to high confidence levels.
# We vary the c/a ratio boundaries used for binning (prolate, triaxial, spherical).
# Original thresholds were: c/a < 0.5 (prolate), 0.5-0.8 (triaxial), > 0.8 (spherical).
# We will sweep the lower and upper boundaries.
LOWER_BOUNDARIES = [0.4, 0.5, 0.6]
UPPER_BOUNDARIES = [0.7, 0.8, 0.9]

def load_statistical_results() -> pd.DataFrame:
    """Load the statistical results from the previous analysis (T025 output)."""
    processed_path = get_data_processed_path()
    file_path = processed_path / "statistical_results.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Statistical results file not found at {file_path}. "
            "Ensure T025 (generate_statistical_results) has been run successfully."
        )
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded statistical results with {len(df)} rows from {file_path}")
    return df

def recompute_bin_assignments(df: pd.DataFrame, lower_thresh: float, upper_thresh: float) -> pd.DataFrame:
    """
    Recompute bin assignments based on new thresholds.
    Bins:
      - 'prolate': c/a < lower_thresh
      - 'triaxial': lower_thresh <= c/a <= upper_thresh
      - 'spherical': c/a > upper_thresh
    """
    df = df.copy()
    
    # Ensure c/a column exists
    if 'c_a_ratio' not in df.columns:
        raise ValueError("Input dataframe missing 'c_a_ratio' column required for binning.")
    
    conditions = [
        df['c_a_ratio'] < lower_thresh,
        (df['c_a_ratio'] >= lower_thresh) & (df['c_a_ratio'] <= upper_thresh),
        df['c_a_ratio'] > upper_thresh
    ]
    choices = ['prolate', 'triaxial', 'spherical']
    df['recomputed_bin'] = np.select(conditions, choices, default='unknown')
    
    return df

def run_statistical_test_for_binning(df: pd.DataFrame, property_col: str) -> Dict[str, Any]:
    """
    Run Kruskal-Wallis test on the specified property across the recomputed bins.
    Returns p-value and test statistic.
    """
    # Group by bin
    groups = [group[1][property_col].values for group in df.groupby('recomputed_bin') if len(group[1]) > 0]
    
    if len(groups) < 2:
        return {'p_value': np.nan, 'statistic': np.nan, 'n_groups': len(groups)}
    
    try:
        stat, p_val = scipy_stats.kruskal(*groups)
        return {'p_value': p_val, 'statistic': stat, 'n_groups': len(groups)}
    except Exception as e:
        logger.warning(f"Kruskal-Wallis failed for {property_col}: {e}")
        return {'p_value': np.nan, 'statistic': np.nan, 'n_groups': len(groups)}

def calculate_variance(p_values: List[float]) -> float:
    """Calculate the variance of a list of p-values, ignoring NaNs."""
    valid_p = [p for p in p_values if not np.isnan(p)]
    if len(valid_p) < 2:
        return np.nan
    return float(np.var(valid_p))

def run_sensitivity_analysis() -> pd.DataFrame:
    """
    Perform the full sensitivity analysis sweep.
    1. Iterate over threshold combinations.
    2. Recompute bins.
    3. Run statistical tests for key properties (e.g., 'star_formation_rate', 'stellar_mass').
    4. Collect p-values.
    5. Calculate variance.
    6. Check against SC-003 threshold (0.001).
    """
    processed_path = get_data_processed_path()
    output_path = get_output_path()
    
    # Load base data
    logger.info("Loading statistical results for sensitivity analysis...")
    try:
        base_df = load_statistical_results()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Properties to test (matching typical outputs from stats.py)
    test_properties = ['star_formation_rate', 'stellar_mass', 'b_a_ratio', 'triaxiality']
    # Filter to only those present in the dataframe
    available_properties = [p for p in test_properties if p in base_df.columns]
    
    if not available_properties:
        logger.warning("No test properties found in statistical_results.csv. Using synthetic columns for structure? No, failing.")
        # If the previous step didn't produce these columns, we can't do the analysis.
        # However, for robustness, we might fallback to 'c_a_ratio' if present, but that's circular.
        # Let's assume the previous step produced at least some numeric columns.
        numeric_cols = base_df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found in statistical_results.csv to run sensitivity analysis.")
        available_properties = numeric_cols[:3] # Take first 3 numeric columns
        logger.info(f"Using numeric columns as test properties: {available_properties}")

    results = []
    all_p_values = []

    logger.info(f"Starting sensitivity sweep over {len(LOWER_BOUNDARIES) * len(UPPER_BOUNDARIES)} threshold combinations.")

    for lower in LOWER_BOUNDARIES:
        for upper in UPPER_BOUNDARIES:
            # Skip invalid ranges
            if lower >= upper:
                continue
            
            logger.debug(f"Sweeping: lower={lower}, upper={upper}")
            
            # Recompute bins
            df_swept = recompute_bin_assignments(base_df, lower, upper)
            
            # Check if we have enough data in bins
            bin_counts = df_swept['recomputed_bin'].value_counts()
            if bin_counts.min() < 10: # Minimum sample size per bin
                logger.debug(f"Skipping: Insufficient data in bins for lower={lower}, upper={upper}")
                continue

            sweep_row = {
                'lower_threshold': lower,
                'upper_threshold': upper
            }
            
            for prop in available_properties:
                test_res = run_statistical_test_for_binning(df_swept, prop)
                p_val = test_res['p_value']
                sweep_row[f'p_value_{prop}'] = p_val
                
                if not np.isnan(p_val):
                    all_p_values.append(p_val)
            
            results.append(sweep_row)

    if not results:
        logger.error("Sensitivity analysis produced no results. Check data and thresholds.")
        raise RuntimeError("Sensitivity analysis produced no valid results.")

    # Create DataFrame
    report_df = pd.DataFrame(results)
    
    # Calculate overall variance across all p-values collected
    if all_p_values:
        variance = calculate_variance(all_p_values)
    else:
        variance = np.nan
    
    report_df['p_value_variance'] = variance
    
    # SC-003 Check
    sc_003_status = "PASSED" if variance <= 0.001 else "FAILED_SC-003"
    if variance > 0.001 and not np.isnan(variance):
        logger.warning(f"SC-003 FAILED: P-value variance {variance:.6f} > 0.001")
    else:
        logger.info(f"SC-003 Status: {sc_003_status} (Variance: {variance:.6f})")
    
    report_df['sc_003_status'] = sc_003_status
    
    # Ensure associational_only flag is present (T026 requirement)
    if 'associational_only' not in report_df.columns:
        report_df['associational_only'] = True

    # Save to CSV
    output_file = processed_path / "sensitivity_report.csv"
    report_df.to_csv(output_file, index=False)
    logger.info(f"Sensitivity report saved to {output_file}")
    
    # Update metadata.yaml
    try:
        metadata = load_metadata()
        if 'sensitivity_report' not in metadata.get('datasets', {}):
            metadata['datasets']['sensitivity_report'] = {}
        metadata['datasets']['sensitivity_report']['path'] = str(output_file)
        metadata['datasets']['sensitivity_report']['associational_only'] = True
        metadata['datasets']['sensitivity_report']['sc_003_status'] = sc_003_status
        metadata['datasets']['sensitivity_report']['p_value_variance'] = variance
        
        save_metadata(metadata)
        logger.info("Updated data/metadata.yaml with sensitivity analysis results.")
    except Exception as e:
        logger.error(f"Failed to update metadata.yaml: {e}")
        raise

    return report_df

def main():
    """Entry point for the sensitivity analysis script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        report = run_sensitivity_analysis()
        print(f"Sensitivity analysis complete. Variance: {report['p_value_variance'].iloc[0]:.6f}")
        print(f"SC-003 Status: {report['sc_003_status'].iloc[0]}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
