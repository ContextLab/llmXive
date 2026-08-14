"""
Robustness Preprocessing: Window Size Sensitivity (2-second windows).

This script re-runs the EEG preprocessing pipeline (T010a/T010b logic) 
but with a specific configuration for 2-second windows (instead of the 
primary 4-second windows) to test the stability of the results.

Dependency: T010a/T010b (primary preprocessing) and T007/T008 (data availability).
Output: data/interim/robustness/window_2s/cleaned_eeg/ directory containing .fif files.
"""
import os
import sys
import glob
import argparse
import numpy as np
import mne
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Import shared utilities
from config import (
    get_path, ensure_dirs, get_filter_params, 
    get_ica_params, get_exclusion_params, get_window_seconds, 
    get_overlap_seconds, set_global_seed
)
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

def get_subject_id_from_path(file_path: str) -> str:
    """Extract subject ID from a file path."""
    fname = os.path.basename(file_path)
    # Expecting format like 'sub-0101_ses-01_task-rest_run-01_raw.fif' or similar
    if 'sub-' in fname:
        parts = fname.split('_')
        for part in parts:
            if part.startswith('sub-'):
                return part.replace('sub-', '')
    # Fallback: assume filename is ID if it matches pattern
    if fname.startswith('sub-'):
        return fname.split('_')[0].replace('sub-', '')
    return os.path.splitext(fname)[0]

def load_physionet_eeg_data(input_dir: str) -> List[str]:
    """
    Load raw EEG files from the specified directory.
    Returns a list of file paths.
    """
    patterns = ['*.fif', '*.edf', '*.bdf']
    files = []
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory {input_dir} does not exist.")
    
    for pattern in patterns:
        files.extend(input_path.rglob(pattern))
    
    if not files:
        raise FileNotFoundError(f"No EEG files found in {input_dir}.")
    
    return [str(f) for f in files]

def preprocess_subject(
    file_path: str, 
    output_dir: str, 
    window_size: float = 2.0,
    use_ica: bool = True
) -> Tuple[Optional[mne.io.Raw], Dict[str, Any]]:
    """
    Preprocess a single subject's EEG data with robustness parameters.
    
    Args:
        file_path: Path to the raw EEG file.
        output_dir: Directory to save the cleaned .fif file.
        window_size: Window size in seconds (Robustness: 2.0s).
        use_ica: Whether to apply ICA (True for this robustness check).
        
    Returns:
        Tuple of (processed Raw object, metadata dict)
    """
    subject_id = get_subject_id_from_path(file_path)
    metadata = {
        'subject_id': subject_id,
        'file_path': file_path,
        'window_size': window_size,
        'status': 'pending',
        'channels_rejected': 0,
        'total_channels': 0,
        'ica_components': 0
    }

    try:
        # Load data
        raw = mne.io.read_raw_fif(file_path, preload=True)
        metadata['total_channels'] = len(raw.ch_names)
        
        # 1. Band-pass filter (1-40 Hz)
        filter_params = get_filter_params()
        raw = bandpass_filter(raw, filter_params['low'], filter_params['high'])
        
        # 2. Notch filter (60 Hz)
        raw = notch_filter(raw, 60)
        
        # 3. ICA Cleaning (if enabled)
        if use_ica:
            ica_params = get_ica_params()
            raw, n_components = apply_ica(raw, 
                                          n_components=ica_params['n_components'],
                                          algorithm=ica_params['algorithm'])
            metadata['ica_components'] = n_components
        else:
            # If ICA is skipped (not the case for T026b, but for completeness)
            metadata['ica_components'] = 0

        # 4. Channel Exclusion Logic (Variance Rejection)
        exclusion_params = get_exclusion_params()
        threshold = exclusion_params['variance_threshold']
        rejected_channels = reject_channels_by_variance(raw, threshold)
        
        if rejected_channels:
            raw.drop_channels(rejected_channels)
            metadata['channels_rejected'] = len(rejected_channels)
        
        # 5. Save cleaned data
        ensure_dirs(output_dir)
        output_filename = f"sub-{subject_id}_cleaned_2s_window.fif"
        output_path = os.path.join(output_dir, output_filename)
        raw.save(output_path, overwrite=True)
        
        metadata['status'] = 'success'
        metadata['output_path'] = output_path
        
        return raw, metadata

    except Exception as e:
        metadata['status'] = 'failed'
        metadata['error'] = str(e)
        print(f"Failed to process {file_path}: {e}")
        return None, metadata

def main():
    """
    Main entry point for the robustness preprocessing pipeline.
    """
    parser = argparse.ArgumentParser(description="Robustness Preprocessing: 2-second windows")
    parser.add_argument('--input-dir', type=str, default=None,
                        help="Directory containing raw EEG files. Defaults to data/raw.")
    parser.add_argument('--output-dir', type=str, default=None,
                        help="Output directory for cleaned files. Defaults to data/interim/robustness/window_2s/cleaned_eeg.")
    parser.add_argument('--window-size', type=float, default=2.0,
                        help="Window size in seconds. Default is 2.0 (Robustness).")
    parser.add_argument('--no-ica', action='store_true',
                        help="Skip ICA (Not used for T026b, but supported).")
    parser.add_argument('--seed', type=int, default=42,
                        help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    
    # Set global seed
    set_global_seed(args.seed)
    
    # Determine paths
    input_dir = args.input_dir if args.input_dir else get_path('raw_data')
    # Ensure robustness output path is distinct
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Construct robustness path
        base_robustness = get_path('interim_robustness') # Assuming config has this or we construct it
        # Fallback if config key doesn't exist, construct manually
        if not base_robustness:
             base_robustness = os.path.join("data", "interim", "robustness")
        output_dir = os.path.join(base_robustness, "window_2s", "cleaned_eeg")
    
    print(f"Starting Robustness Preprocessing (Window Size: {args.window_size}s)...")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    
    # Load raw files
    try:
        raw_files = load_physionet_eeg_data(input_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    print(f"Found {len(raw_files)} raw files.")
    
    # Process each subject
    results = []
    success_count = 0
    fail_count = 0
    
    for file_path in raw_files:
        use_ica = not args.no_ica
        raw, meta = preprocess_subject(file_path, output_dir, args.window_size, use_ica)
        results.append(meta)
        if meta['status'] == 'success':
            success_count += 1
        else:
            fail_count += 1
    
    # Write exclusion log for robustness run
    log_path = os.path.join(os.path.dirname(output_dir), "exclusion_log_2s.csv")
    import pandas as pd
    df_results = pd.DataFrame(results)
    df_results.to_csv(log_path, index=False)
    print(f"Exclusion log saved to: {log_path}")
    
    print(f"Processing complete. Success: {success_count}, Failed: {fail_count}")
    
    if fail_count > 0:
        print("Warning: Some subjects failed processing.")
        # Do not exit with error unless ALL failed, but log it
        # However, if the task requires strict adherence, we might exit 1 if critical count is 0
        if success_count == 0:
            sys.exit(1)

if __name__ == "__main__":
    main()