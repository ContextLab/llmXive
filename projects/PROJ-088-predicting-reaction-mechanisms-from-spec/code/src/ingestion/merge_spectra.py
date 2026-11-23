"""
Merge IR (NIST) and NMR (PubChem) datasets into unified fingerprints.

This module implements the core merging logic for User Story 1.
It applies linear interpolation using the bin mapping defined in T013c
to create fixed-dimensional vectors from raw spectral data.

Output: data/processed/fingerprints.parquet
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.interpolate import interp1d

# Project imports matching the API surface
from src.utils.io import read_json_file, ensure_directory_exists, write_json_file
from src.utils.logging import log_info, log_warning, log_error, flag_edge_case
from src.utils.seed import set_seed

# Constants
DEFAULT_SEED = 42
OUTPUT_PATH = "data/processed/fingerprints.parquet"
BIN_MAPPING_PATH = "data/reference/bin_mapping.json"
NIST_DATA_PATH = "data/processed/nist_ir_data.parquet"
PUBCHEM_DATA_PATH = "data/processed/pubchem_nmr_data.parquet"

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Set random seed for reproducibility."""
    set_seed(seed)
    log_info(f"Random seed set to {seed}")

def bin_spectrum_ir(
    spectrum_data: Dict[str, Any], 
    bin_mapping: Dict[str, Any]
) -> Optional[np.ndarray]:
    """
    Bin an IR spectrum into fixed dimensions using linear interpolation.
    
    Args:
        spectrum_data: Dictionary containing 'frequencies' (cm-1) and 'intensities'
        bin_mapping: Dictionary defining the target bins and interpolation method
        
    Returns:
        numpy array of binned intensities, or None if invalid
    """
    try:
        if 'frequencies' not in spectrum_data or 'intensities' not in spectrum_data:
            log_warning("Missing frequencies or intensities in IR spectrum data")
            return None
        
        freqs = np.array(spectrum_data['frequencies'])
        intensities = np.array(spectrum_data['intensities'])
        
        if len(freqs) == 0 or len(intensities) == 0:
            log_warning("Empty frequency or intensity arrays in IR spectrum")
            return None
        
        # Get bin definition from mapping
        ir_bins_config = bin_mapping.get('bins', {}).get('IR', {})
        if not ir_bins_config:
            log_error("IR bin configuration not found in bin_mapping.json")
            return None
        
        # Extract bin edges and count
        bin_edges = np.array(ir_bins_config.get('edges', []))
        bin_count = ir_bins_config.get('count', len(bin_edges) - 1)
        
        if len(bin_edges) < 2:
            log_error("Invalid bin edges configuration for IR")
            return None
        
        # Create interpolation function
        # Sort by frequency to ensure monotonicity for interpolation
        sort_idx = np.argsort(freqs)
        freqs_sorted = freqs[sort_idx]
        intensities_sorted = intensities[sort_idx]
        
        # Create interpolation function (linear)
        interp_func = interp1d(
            freqs_sorted, 
            intensities_sorted, 
            kind='linear',
            bounds_error=False,
            fill_value=0.0  # Extrapolate to 0 outside range
        )
        
        # Calculate bin centers for sampling
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        
        # Interpolate at bin centers
        binned_values = interp_func(bin_centers)
        
        # Handle any NaNs that might result from interpolation
        binned_values = np.nan_to_num(binned_values, nan=0.0, posinf=0.0, neginf=0.0)
        
        return binned_values
        
    except Exception as e:
        log_error(f"Error binning IR spectrum: {str(e)}")
        return None

def bin_spectrum_nmr(
    spectrum_data: Dict[str, Any], 
    bin_mapping: Dict[str, Any]
) -> Optional[np.ndarray]:
    """
    Bin an NMR spectrum into fixed dimensions using linear interpolation.
    
    Args:
        spectrum_data: Dictionary containing 'chemical_shifts' (ppm) and 'intensities'
        bin_mapping: Dictionary defining the target bins and interpolation method
        
    Returns:
        numpy array of binned intensities, or None if invalid
    """
    try:
        if 'chemical_shifts' not in spectrum_data or 'intensities' not in spectrum_data:
            log_warning("Missing chemical_shifts or intensities in NMR spectrum data")
            return None
        
        shifts = np.array(spectrum_data['chemical_shifts'])
        intensities = np.array(spectrum_data['intensities'])
        
        if len(shifts) == 0 or len(intensities) == 0:
            log_warning("Empty shift or intensity arrays in NMR spectrum")
            return None
        
        # Get bin definition from mapping
        nmr_bins_config = bin_mapping.get('bins', {}).get('NMR', {})
        if not nmr_bins_config:
            log_error("NMR bin configuration not found in bin_mapping.json")
            return None
        
        # Extract bin edges and count
        bin_edges = np.array(nmr_bins_config.get('edges', []))
        bin_count = nmr_bins_config.get('count', len(bin_edges) - 1)
        
        if len(bin_edges) < 2:
            log_error("Invalid bin edges configuration for NMR")
            return None
        
        # Create interpolation function
        # Sort by chemical shift to ensure monotonicity
        sort_idx = np.argsort(shifts)
        shifts_sorted = shifts[sort_idx]
        intensities_sorted = intensities[sort_idx]
        
        # Create interpolation function (linear)
        interp_func = interp1d(
            shifts_sorted, 
            intensities_sorted, 
            kind='linear',
            bounds_error=False,
            fill_value=0.0  # Extrapolate to 0 outside range
        )
        
        # Calculate bin centers for sampling
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        
        # Interpolate at bin centers
        binned_values = interp_func(bin_centers)
        
        # Handle any NaNs
        binned_values = np.nan_to_num(binned_values, nan=0.0, posinf=0.0, neginf=0.0)
        
        return binned_values
        
    except Exception as e:
        log_error(f"Error binning NMR spectrum: {str(e)}")
        return None

def merge_and_bin_spectra(
    nist_df: pd.DataFrame, 
    pubchem_df: pd.DataFrame, 
    bin_mapping: Dict[str, Any]
) -> pd.DataFrame:
    """
    Merge filtered IR and NMR datasets and create unified fingerprints.
    
    Args:
        nist_df: DataFrame of filtered NIST IR data
        pubchem_df: DataFrame of filtered PubChem NMR data
        bin_mapping: Bin mapping configuration from T013c
        
    Returns:
        DataFrame with merged fingerprints and mechanism labels
    """
    log_info(f"Starting merge of {len(nist_df)} IR records and {len(pubchem_df)} NMR records")
    
    # Identify common samples (by compound ID or other key)
    # Assuming 'compound_id' is the key for matching
    common_key = 'compound_id'
    
    if common_key not in nist_df.columns:
        log_error(f"NIST data missing expected key column: {common_key}")
        return pd.DataFrame()
        
    if common_key not in pubchem_df.columns:
        log_error(f"PubChem data missing expected key column: {common_key}")
        return pd.DataFrame()
    
    # Merge on compound_id
    merged_df = pd.merge(
        nist_df, 
        pubchem_df, 
        on=common_key, 
        how='inner',
        suffixes=('_ir', '_nmr')
    )
    
    log_info(f"After merging on {common_key}: {len(merged_df)} records")
    
    if len(merged_df) == 0:
        log_warning("No matching records found between IR and NMR datasets")
        return pd.DataFrame()
    
    # Prepare columns for fingerprints
    ir_bins_config = bin_mapping.get('bins', {}).get('IR', {})
    nmr_bins_config = bin_mapping.get('bins', {}).get('NMR', {})
    
    ir_bin_count = ir_bins_config.get('count', 0)
    nmr_bin_count = nmr_bins_config.get('count', 0)
    
    if ir_bin_count == 0 or nmr_bin_count == 0:
        log_error("Invalid bin counts in bin_mapping")
        return pd.DataFrame()
    
    fingerprint_columns = []
    fingerprints = []
    
    # Process each row
    valid_count = 0
    for idx, row in merged_df.iterrows():
        # Extract IR data
        ir_data = {
            'frequencies': row['frequencies_ir'] if isinstance(row['frequencies_ir'], list) else json.loads(row['frequencies_ir']),
            'intensities': row['intensities_ir'] if isinstance(row['intensities_ir'], list) else json.loads(row['intensities_ir'])
        }
        
        # Extract NMR data
        nmr_data = {
            'chemical_shifts': row['chemical_shifts_nmr'] if isinstance(row['chemical_shifts_nmr'], list) else json.loads(row['chemical_shifts_nmr']),
            'intensities': row['intensities_nmr'] if isinstance(row['intensities_nmr'], list) else json.loads(row['intensities_nmr'])
        }
        
        # Bin spectra
        ir_binned = bin_spectrum_ir(ir_data, bin_mapping)
        nmr_binned = bin_spectrum_nmr(nmr_data, bin_mapping)
        
        if ir_binned is None or nmr_binned is None:
            flag_edge_case(f"Skipping row {idx} due to invalid spectral data")
            continue
        
        # Combine fingerprints: [IR_bins..., NMR_bins...]
        full_fingerprint = np.concatenate([ir_binned, nmr_binned])
        fingerprints.append(full_fingerprint)
        valid_count += 1
    
    log_info(f"Successfully created {valid_count} valid fingerprints")
    
    if valid_count == 0:
        log_error("No valid fingerprints generated")
        return pd.DataFrame()
    
    # Create result DataFrame
    result_df = merged_df.iloc[:valid_count].reset_index(drop=True)
    
    # Add fingerprint as a single column (array)
    result_df['fingerprint'] = fingerprints
    
    # Ensure mechanism label exists
    if 'mechanism_label' not in result_df.columns:
        log_error("Missing mechanism_label in merged data")
        return pd.DataFrame()
    
    # Validate class balance
    validate_class_balance(result_df)
    
    return result_df

def validate_fingerprints(df: pd.DataFrame) -> bool:
    """
    Validate that fingerprints are correctly formed.
    
    Args:
        df: DataFrame with fingerprint column
        
    Returns:
        True if valid, False otherwise
    """
    if 'fingerprint' not in df.columns:
        log_error("Missing fingerprint column")
        return False
    
    if len(df) == 0:
        log_warning("Empty dataframe")
        return True  # Technically valid, just empty
    
    # Check for NaNs in fingerprints
    for idx, row in df.iterrows():
        fp = row['fingerprint']
        if fp is None:
            log_warning(f"Row {idx} has None fingerprint")
            return False
        if isinstance(fp, np.ndarray):
            if np.any(np.isnan(fp)):
                log_warning(f"Row {idx} has NaN values in fingerprint")
                return False
        else:
            log_warning(f"Row {idx} fingerprint is not a numpy array")
            return False
    
    log_info("Fingerprint validation passed")
    return True

def validate_class_balance(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate and log class balance metrics.
    
    Args:
        df: DataFrame with mechanism_label column
        
    Returns:
        Dictionary with class balance metrics
    """
    if 'mechanism_label' not in df.columns:
        log_error("Missing mechanism_label column")
        return {}
    
    label_counts = df['mechanism_label'].value_counts()
    total = len(df)
    
    metrics = {
        'total_samples': total,
        'class_counts': label_counts.to_dict(),
        'class_ratios': {}
    }
    
    if len(label_counts) > 0:
        min_count = label_counts.min()
        max_count = label_counts.max()
        metrics['min_class_count'] = min_count
        metrics['max_class_count'] = max_count
        metrics['class_balance_ratio'] = max_count / min_count if min_count > 0 else float('inf')
        
        log_info(f"Class balance: min={min_count}, max={max_count}, ratio={metrics['class_balance_ratio']:.2f}")
        
        # Log per-class distribution
        for label, count in label_counts.items():
            ratio = count / total
            metrics['class_ratios'][label] = ratio
            log_info(f"  {label}: {count} ({ratio:.2%})")
    
    return metrics

def main():
    """Main entry point for merging spectra."""
    log_info("Starting merge_spectra.py")
    
    # Set seed for reproducibility
    set_seed(DEFAULT_SEED)
    
    # Ensure output directory exists
    ensure_directory_exists(OUTPUT_PATH)
    
    # Load bin mapping (from T013c)
    if not os.path.exists(BIN_MAPPING_PATH):
        log_error(f"Bin mapping file not found: {BIN_MAPPING_PATH}")
        sys.exit(1)
    
    bin_mapping = read_json_file(BIN_MAPPING_PATH)
    log_info(f"Loaded bin mapping from {BIN_MAPPING_PATH}")
    
    # Load NIST IR data (from T011)
    if not os.path.exists(NIST_DATA_PATH):
        log_error(f"NIST data file not found: {NIST_DATA_PATH}")
        sys.exit(1)
    
    nist_df = pd.read_parquet(NIST_DATA_PATH)
    log_info(f"Loaded {len(nist_df)} IR records from {NIST_DATA_PATH}")
    
    # Load PubChem NMR data (from T012)
    if not os.path.exists(PUBCHEM_DATA_PATH):
        log_error(f"PubChem data file not found: {PUBCHEM_DATA_PATH}")
        sys.exit(1)
    
    pubchem_df = pd.read_parquet(PUBCHEM_DATA_PATH)
    log_info(f"Loaded {len(pubchem_df)} NMR records from {PUBCHEM_DATA_PATH}")
    
    # Merge and bin
    result_df = merge_and_bin_spectra(nist_df, pubchem_df, bin_mapping)
    
    if len(result_df) == 0:
        log_error("No valid data to write")
        sys.exit(1)
    
    # Validate fingerprints
    if not validate_fingerprints(result_df):
        log_error("Fingerprint validation failed")
        sys.exit(1)
    
    # Write output
    log_info(f"Writing {len(result_df)} fingerprints to {OUTPUT_PATH}")
    result_df.to_parquet(OUTPUT_PATH, index=False)
    
    # Calculate and log final metrics
    metrics = validate_class_balance(result_df)
    if metrics:
        # Save metrics to a side file
        metrics_path = OUTPUT_PATH.replace('.parquet', '_metrics.json')
        write_json_file(metrics_path, metrics)
        log_info(f"Class balance metrics saved to {metrics_path}")
    
    log_info("Merge and binning completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
