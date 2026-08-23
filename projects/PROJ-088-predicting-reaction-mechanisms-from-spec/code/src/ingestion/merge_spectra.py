import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from src.utils.logging import log_info, log_warning, log_error, log_data_quality_issue, flag_edge_case
from src.utils.io import ensure_directory_exists, write_json_file, read_json_file

# Constants for binning and class balance
IR_MIN_WAVENUMBER = 400
IR_MAX_WAVENUMBER = 4000
NMR_MIN_SHIFT = 0
NMR_MAX_SHIFT = 14
NUM_BINS = 512
IR_BINS = 256
NMR_BINS = 256
CLASS_LABELS = {'SN1', 'SN2', 'E1'}
MIN_SAMPLE_THRESHOLD = 50

def bin_spectrum_ir(spectrum_data: Dict[str, Any], num_bins: int = IR_BINS) -> np.ndarray:
    """
    Bins an IR spectrum into a fixed number of bins.
    
    Args:
        spectrum_data: Dictionary containing 'wavenumbers' and 'intensities' lists/arrays.
        num_bins: Number of bins to create.
        
    Returns:
        numpy array of binned intensities.
    """
    wavenumbers = np.array(spectrum_data.get('wavenumbers', []))
    intensities = np.array(spectrum_data.get('intensities', []))
    
    if len(wavenumbers) == 0 or len(intensities) == 0:
        return np.zeros(num_bins)
    
    # Ensure sorting
    sorted_indices = np.argsort(wavenumbers)
    wavenumbers = wavenumbers[sorted_indices]
    intensities = intensities[sorted_indices]
    
    # Filter to valid range
    mask = (wavenumbers >= IR_MIN_WAVENUMBER) & (wavenumbers <= IR_MAX_WAVENUMBER)
    wavenumbers = wavenumbers[mask]
    intensities = intensities[mask]
    
    if len(wavenumbers) == 0:
        return np.zeros(num_bins)
    
    # Create bin edges
    bin_edges = np.linspace(IR_MIN_WAVENUMBER, IR_MAX_WAVENUMBER, num_bins + 1)
    
    # Bin the data
    binned, _ = np.histogram(wavenumbers, bins=bin_edges, weights=intensities)
    
    # Normalize
    if np.sum(binned) > 0:
        binned = binned / np.sum(binned)
        
    return binned

def bin_spectrum_nmr(spectrum_data: Dict[str, Any], num_bins: int = NMR_BINS) -> np.ndarray:
    """
    Bins an NMR spectrum into a fixed number of bins.
    
    Args:
        spectrum_data: Dictionary containing 'shifts' and 'intensities' lists/arrays.
        num_bins: Number of bins to create.
        
    Returns:
        numpy array of binned intensities.
    """
    shifts = np.array(spectrum_data.get('shifts', []))
    intensities = np.array(spectrum_data.get('intensities', []))
    
    if len(shifts) == 0 or len(intensities) == 0:
        return np.zeros(num_bins)
    
    # Ensure sorting
    sorted_indices = np.argsort(shifts)
    shifts = shifts[sorted_indices]
    intensities = intensities[sorted_indices]
    
    # Filter to valid range
    mask = (shifts >= NMR_MIN_SHIFT) & (shifts <= NMR_MAX_SHIFT)
    shifts = shifts[mask]
    intensities = intensities[mask]
    
    if len(shifts) == 0:
        return np.zeros(num_bins)
    
    # Create bin edges
    bin_edges = np.linspace(NMR_MIN_SHIFT, NMR_MAX_SHIFT, num_bins + 1)
    
    # Bin the data
    binned, _ = np.histogram(shifts, bins=bin_edges, weights=intensities)
    
    # Normalize
    if np.sum(binned) > 0:
        binned = binned / np.sum(binned)
        
    return binned

def merge_and_bin_spectra(ir_data: List[Dict[str, Any]], nmr_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Merges IR and NMR data, bins them, and creates a unified fingerprint.
    
    Args:
        ir_data: List of IR spectrum dictionaries.
        nmr_data: List of NMR spectrum dictionaries.
        
    Returns:
        DataFrame with binned fingerprints and labels.
    """
    # Create IR fingerprints
    ir_fingerprints = []
    ir_ids = []
    for item in ir_data:
        fingerprint = bin_spectrum_ir(item)
        ir_fingerprints.append(fingerprint)
        ir_ids.append(item.get('id', 'unknown'))
    
    # Create NMR fingerprints
    nmr_fingerprints = []
    nmr_ids = []
    for item in nmr_data:
        fingerprint = bin_spectrum_nmr(item)
        nmr_fingerprints.append(fingerprint)
        nmr_ids.append(item.get('id', 'unknown'))
    
    # Merge by ID (assuming IDs match between IR and NMR for this example)
    # In a real scenario, we would join on a common key
    merged_data = []
    ir_dict = {item['id']: item for item in ir_data}
    nmr_dict = {item['id']: item for item in nmr_data}
    
    all_ids = set(ir_dict.keys()) & set(nmr_dict.keys())
    
    for sample_id in all_ids:
        ir_fp = bin_spectrum_ir(ir_dict[sample_id])
        nmr_fp = bin_spectrum_nmr(nmr_dict[sample_id])
        
        # Combine fingerprints
        combined_fp = np.concatenate([ir_fp, nmr_fp])
        
        # Get label
        label = ir_dict[sample_id].get('label', 'unknown')
        
        merged_data.append({
            'sample_id': sample_id,
            'fingerprint': combined_fp,
            'label': label,
            'ir_source': 'nist',
            'nmr_source': 'pubchem'
        })
    
    return pd.DataFrame(merged_data)

def validate_fingerprints(df: pd.DataFrame) -> bool:
    """
    Validates that fingerprints are correctly formed.
    
    Args:
        df: DataFrame with fingerprint column.
        
    Returns:
        True if valid, False otherwise.
    """
    if 'fingerprint' not in df.columns:
        log_error("DataFrame missing 'fingerprint' column")
        return False
    
    if 'label' not in df.columns:
        log_error("DataFrame missing 'label' column")
        return False
    
    # Check for NaN in fingerprints
    for idx, row in df.iterrows():
        fp = row['fingerprint']
        if np.any(np.isnan(fp)):
            log_warning(f"NaN found in fingerprint for sample {row.get('sample_id', idx)}")
            return False
    
    return True

def validate_class_balance(df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Validates class balance and generates a report.
    
    Args:
        df: DataFrame with 'label' column.
        output_path: Path to write the JSON report.
        
    Returns:
        Dictionary containing the class balance report.
    """
    if 'label' not in df.columns:
        log_error("DataFrame missing 'label' column for class balance validation")
        return {"error": "missing_label_column"}
    
    labels = df['label'].dropna()
    label_counts = labels.value_counts().to_dict()
    
    # Ensure all expected classes are present
    for cls in CLASS_LABELS:
        if cls not in label_counts:
            label_counts[cls] = 0
    
    total_samples = len(labels)
    min_count = min(label_counts.values()) if label_counts else 0
    max_count = max(label_counts.values()) if label_counts else 0
    
    # Calculate ratio
    ratio = max_count / min_count if min_count > 0 else float('inf')
    
    # Flag under-sampled classes
    under_sampled = [cls for cls, count in label_counts.items() if count < MIN_SAMPLE_THRESHOLD]
    
    report = {
        "total_samples": total_samples,
        "class_counts": label_counts,
        "max_min_ratio": ratio,
        "under_sampled_classes": under_sampled,
        "is_balanced": len(under_sampled) == 0,
        "threshold": MIN_SAMPLE_THRESHOLD
    }
    
    # Log issues
    if min_count == 0:
        log_critical(f"Class imbalance detected: one or more classes have zero samples. Ratios: {label_counts}")
        flag_edge_case("class_imbalance", "Zero samples in one or more classes")
    elif ratio > 10:
        log_warning(f"High class imbalance detected (ratio={ratio:.2f})")
        flag_edge_case("class_imbalance", f"Max/Min ratio {ratio:.2f} exceeds threshold 10")
    
    if under_sampled:
        log_data_quality_issue(f"Under-sampled classes detected: {under_sampled}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        ensure_directory_exists(output_dir)
    
    # Write report
    write_json_file(output_path, report)
    log_info(f"Class balance report written to {output_path}")
    
    return report

def main():
    """
    Main entry point for the merge_spectra script.
    This function demonstrates the class balance validation by loading
    sample data (in a real scenario, this would load from data/processed/fingerprints.parquet)
    and running the validation.
    """
    # For demonstration, we create a small synthetic dataset that mimics the expected structure
    # In a real pipeline, this would load from the merged parquet file produced by previous steps
    # NOTE: This is ONLY for local testing of the validation logic. The actual pipeline 
    # should use real data from data/processed/fingerprints.parquet
    
    log_info("Starting merge_spectra validation script")
    
    # Create sample data for testing class balance validation
    sample_data = {
        'sample_id': [f'sample_{i}' for i in range(100)],
        'fingerprint': [np.random.rand(NUM_BINS) for _ in range(100)],
        'label': np.random.choice(list(CLASS_LABELS), 100, p=[0.6, 0.3, 0.1]) # Intentionally imbalanced
    }
    
    df = pd.DataFrame(sample_data)
    
    # Run class balance validation
    output_path = "data/results/class_balance_report.json"
    report = validate_class_balance(df, output_path)
    
    # Print summary
    print(f"\nClass Balance Report Summary:")
    print(f"Total samples: {report['total_samples']}")
    print(f"Class counts: {report['class_counts']}")
    print(f"Max/Min ratio: {report['max_min_ratio']:.2f}")
    print(f"Under-sampled classes: {report['under_sampled_classes']}")
    print(f"Report saved to: {output_path}")
    
    return report

if __name__ == "__main__":
    main()
