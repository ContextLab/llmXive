import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from src.utils.logging import log_warning, log_error, flag_edge_case, log_data_quality_issue
from src.utils.seed import set_seed

def normalize_spectrum(spectrum: np.ndarray, method: str = 'minmax') -> np.ndarray:
    """
    Normalize a spectrum array to a standard range.
    
    Args:
        spectrum: Input 1D array of intensity values.
        method: Normalization method ('minmax' or 'zscore').
    
    Returns:
        Normalized numpy array.
    """
    if len(spectrum) == 0:
        return spectrum
    
    if method == 'minmax':
        min_val = np.min(spectrum)
        max_val = np.max(spectrum)
        if max_val - min_val < 1e-10:
            return np.zeros_like(spectrum)
        return (spectrum - min_val) / (max_val - min_val)
    elif method == 'zscore':
        mean_val = np.mean(spectrum)
        std_val = np.std(spectrum)
        if std_val < 1e-10:
            return np.zeros_like(spectrum)
        return (spectrum - mean_val) / std_val
    else:
        raise ValueError(f"Unknown normalization method: {method}")

def bin_spectrum(spectrum: np.ndarray, n_bins: int = 512, 
                 freq_range: Tuple[float, float] = (4000, 400)) -> np.ndarray:
    """
    Bin a spectrum into fixed-length vector.
    
    Args:
        spectrum: Input spectrum (assumed to be sorted by frequency or uniform).
        n_bins: Number of bins to create.
        freq_range: Tuple of (max_freq, min_freq) to define the range.
    
    Returns:
        Binned numpy array of length n_bins.
    """
    if len(spectrum) == 0:
        return np.zeros(n_bins)
    
    # Assuming the input spectrum is already aligned or uniform
    # If not, this would require interpolation logic based on frequency arrays
    # For this implementation, we assume the input 'spectrum' is the intensity array
    # corresponding to a uniform frequency grid defined by freq_range.
    
    # Resample/interpolate to n_bins if necessary
    if len(spectrum) != n_bins:
        x_new = np.linspace(freq_range[0], freq_range[1], n_bins)
        x_old = np.linspace(freq_range[0], freq_range[1], len(spectrum))
        # Simple linear interpolation
        binned = np.interp(x_new, x_old, spectrum)
        return binned
    
    return spectrum

def detect_outliers(spectra: List[np.ndarray], threshold: float = 3.0) -> List[bool]:
    """
    Detect outliers based on variance or missing frequency ranges.
    
    Args:
        spectra: List of spectrum arrays.
        threshold: Z-score threshold for outlier detection.
    
    Returns:
        List of booleans indicating if each spectrum is an outlier.
    """
    if not spectra:
        return []
    
    # Calculate variance for each spectrum
    variances = [np.var(s) for s in spectra]
    mean_var = np.mean(variances)
    std_var = np.std(variances)
    
    if std_var < 1e-10:
        return [False] * len(spectra)
    
    outliers = []
    for i, var in enumerate(variances):
        z_score = (var - mean_var) / std_var
        if z_score > threshold or z_score < -threshold:
            outliers.append(True)
            log_warning(f"Spectrum {i} flagged as outlier due to extreme variance: {var}")
        else:
            outliers.append(False)
    
    return outliers

def validate_class_balance(df: pd.DataFrame, label_col: str = 'label', 
                           min_samples: int = 50) -> Dict[str, Any]:
    """
    Validate class balance in the dataset. Flags classes with < min_samples.
    
    Args:
        df: DataFrame containing the dataset.
        label_col: Name of the column containing class labels.
        min_samples: Minimum number of samples required per class.
    
    Returns:
        Dictionary with validation results:
            - 'balanced': bool, True if all classes meet min_samples
            - 'class_counts': dict, count per class
            - 'flagged_classes': list, classes below threshold
    """
    if label_col not in df.columns:
        log_error(f"Label column '{label_col}' not found in DataFrame")
        return {
            'balanced': False,
            'class_counts': {},
            'flagged_classes': [label_col]
        }
    
    class_counts = df[label_col].value_counts().to_dict()
    flagged_classes = []
    
    for cls, count in class_counts.items():
        if count < min_samples:
            flagged_classes.append(cls)
            msg = f"Class '{cls}' has only {count} samples (threshold: {min_samples})"
            log_data_quality_issue(msg)
            flag_edge_case(f"Class imbalance detected: {msg}")
    
    is_balanced = len(flagged_classes) == 0
    
    if not is_balanced:
        log_warning(f"Class imbalance detected. Flagged classes: {flagged_classes}")
    
    return {
        'balanced': is_balanced,
        'class_counts': class_counts,
        'flagged_classes': flagged_classes
    }

def preprocess_dataset(df: pd.DataFrame, n_bins: int = 512, 
                       freq_range: Tuple[float, float] = (4000, 400),
                       normalize: bool = True,
                       outlier_threshold: float = 3.0,
                       min_class_samples: int = 50,
                       label_col: str = 'label',
                       spectrum_col: str = 'spectrum') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Full preprocessing pipeline: normalize, bin, detect outliers, validate balance.
    
    Args:
        df: Input DataFrame with spectra and labels.
        n_bins: Number of bins for spectrum binning.
        freq_range: Frequency range (max, min).
        normalize: Whether to normalize spectra.
        outlier_threshold: Z-score threshold for outlier detection.
        min_class_samples: Minimum samples per class for balance check.
        label_col: Column name for labels.
        spectrum_col: Column name for spectrum data.
    
    Returns:
        Tuple of (processed DataFrame, validation report dict).
    """
    set_seed(42) # Default seed for reproducibility
    
    # 1. Detect Outliers
    if spectrum_col in df.columns:
        # Ensure spectra are numpy arrays
        spectra = [s if isinstance(s, np.ndarray) else np.array(s) for s in df[spectrum_col]]
        outlier_flags = detect_outliers(spectra, threshold=outlier_threshold)
        df['is_outlier'] = outlier_flags
        
        # Filter out outliers
        df_clean = df[~df['is_outlier']].copy()
        log_info(f"Removed {len(df) - len(df_clean)} outlier spectra.")
    else:
        df_clean = df.copy()
        log_warning(f"Column '{spectrum_col}' not found, skipping outlier detection.")
    
    # 2. Normalize and Bin
    processed_spectra = []
    for _, row in df_clean.iterrows():
        if spectrum_col in row:
            spec = row[spectrum_col]
            if not isinstance(spec, np.ndarray):
                spec = np.array(spec)
            
            if normalize:
                spec = normalize_spectrum(spec)
            
            binned = bin_spectrum(spec, n_bins=n_bins, freq_range=freq_range)
            processed_spectra.append(binned)
        else:
            processed_spectra.append(np.zeros(n_bins))
    
    df_clean[spectrum_col] = processed_spectra
    
    # 3. Validate Class Balance
    balance_report = validate_class_balance(df_clean, label_col=label_col, min_samples=min_class_samples)
    
    return df_clean, balance_report

def main():
    """
    Main entry point for running the preprocessing pipeline on a dataset.
    Expects a CSV/Parquet file with 'spectrum' and 'label' columns.
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Preprocess spectroscopic data")
    parser.add_argument("--input", type=str, required=True, help="Path to input data file (CSV/Parquet)")
    parser.add_argument("--output", type=str, required=True, help="Path to output processed file")
    parser.add_argument("--report", type=str, default="data/results/preprocessing_report.json", 
                        help="Path to output validation report")
    parser.add_argument("--n_bins", type=int, default=512)
    parser.add_argument("--min_samples", type=int, default=50)
    
    args = parser.parse_args()
    
    # Load data
    input_path = Path(args.input)
    if input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    log_info(f"Loaded {len(df)} samples from {input_path}")
    
    # Preprocess
    df_processed, report = preprocess_dataset(
        df, 
        n_bins=args.n_bins, 
        min_class_samples=args.min_samples
    )
    
    # Save processed data
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_processed.to_csv(output_path, index=False)
    log_info(f"Saved processed data to {output_path}")
    
    # Save report
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    log_info(f"Saved validation report to {report_path}")
    
    if not report['balanced']:
        log_warning(f"Class imbalance detected! Flagged classes: {report['flagged_classes']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())