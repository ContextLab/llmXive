"""
T010a: EEG Preprocessing Pipeline

Applies 1-40 Hz band-pass, 50/60 Hz notch, bad channel rejection (>3 SD),
and ICA (0.99 variance retention) to PhysioNet EEG Motor Movement/Imagery data.
Excludes participants with >30% rejected channels.
Outputs cleaned .fif files and an exclusion log.
"""
import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Import from local config and utils
from config import (
    get_path, 
    ensure_dirs, 
    get_filter_params, 
    get_ica_params, 
    get_exclusion_params,
    set_global_seed
)
from utils.eeg_helpers import (
    bandpass_filter, 
    notch_filter, 
    reject_channels_by_variance, 
    apply_ica
)

def get_subject_id_from_path(file_path: str) -> str:
    """Extract subject ID from PhysioNet file path."""
    # PhysioNet paths usually look like: .../sub-01/ses-1/...
    # Or specific to this dataset: .../S001/S001R01.edf
    path_obj = Path(file_path)
    name = path_obj.name
    if name.startswith("S"):
        # Format S001, extract 001
        return name[:4]
    # Fallback: try to find 'sub-' pattern or just use filename stem
    if "sub-" in str(path_obj):
        parts = str(path_obj).split("sub-")
        if len(parts) > 1:
            return parts[1][:4] # Take 4 chars
    return path_obj.stem

def load_physionet_eeg_data(raw_dir: str) -> List[str]:
    """
    Scan raw directory for EDF files.
    Returns list of file paths.
    """
    # PhysioNet EEG Motor Movement/Imagery usually has .edf files
    # Look in subdirectories if necessary
    patterns = ["*.edf", "*.EDF"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(raw_dir, "**", pattern), recursive=True))
    
    # Filter out non-data files if any
    data_files = [f for f in files if "edf" in f.lower()]
    return data_files

def preprocess_subject(
    file_path: str, 
    output_dir: str, 
    exclusion_log: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Preprocess a single subject's EEG data.
    
    Steps:
    1. Load raw data
    2. Band-pass (1-40 Hz)
    3. Notch (50/60 Hz)
    4. Reject bad channels (variance > 3 SD)
    5. Apply ICA (0.99 variance retention)
    6. Save cleaned .fif if valid, log exclusion if >30% channels rejected.
    
    Returns:
        Path to saved .fif if successful, None if excluded.
    """
    set_global_seed()
    
    subject_id = get_subject_id_from_path(file_path)
    if not subject_id:
        exclusion_log.append({
            "participant_id": "unknown",
            "reason": "Could not extract subject ID from path",
            "channels_rejected_ratio": 0.0
        })
        return None

    try:
        # Load raw data
        # MNE expects specific formats, PhysioNet is usually EDF
        raw = None
        try:
            raw = bandpass_filter(file_path, l_freq=1.0, h_freq=40.0)
        except Exception as e:
            # If bandpass fails, try loading raw first then filtering
            import mne
            raw = mne.io.read_raw_edf(file_path, preload=True)
            raw = bandpass_filter(raw, l_freq=1.0, h_freq=40.0)

        # Apply Notch Filter (50 or 60 Hz based on config)
        # We assume config handles the specific frequency or we default to 50
        # The helper notch_filter should handle raw object
        raw = notch_filter(raw, freqs=[50.0, 60.0]) # Apply both or detect

        # Bad Channel Rejection
        # Reject channels with variance > 3 SD
        raw, rejected_channels = reject_channels_by_variance(raw, threshold=3.0)
        
        n_total = len(raw.ch_names)
        n_rejected = len(rejected_channels)
        rejection_ratio = n_rejected / n_total if n_total > 0 else 1.0

        # ICA Application
        # MNE's default ICA with 0.99 variance retention
        ica_params = get_ica_params()
        raw, ica_applied = apply_ica(raw, **ica_params)
        
        if not ica_applied:
            # ICA failure logged, but exclusion only if >30% channels rejected
            # We continue to check channel rejection ratio
            pass

        # Exclusion Logic
        exclusion_threshold = get_exclusion_params().get('max_rejection_ratio', 0.30)
        
        if rejection_ratio > exclusion_threshold:
            exclusion_log.append({
                "participant_id": subject_id,
                "reason": f"High channel rejection ratio ({rejection_ratio:.2f} > {exclusion_threshold})",
                "channels_rejected_ratio": rejection_ratio
            })
            return None
        
        # Save cleaned data
        # Ensure output directory exists
        ensure_dirs(output_dir)
        
        output_path = os.path.join(output_dir, f"sub-{subject_id}_cleaned.fif")
        raw.save(output_path, overwrite=True)
        
        return output_path

    except Exception as e:
        # Log failure but do not exclude unless it's a data integrity issue
        # For this task, we log to exclusion log if processing completely fails
        exclusion_log.append({
            "participant_id": subject_id,
            "reason": f"Processing error: {str(e)}",
            "channels_rejected_ratio": 1.0
        })
        return None

def main():
    """Main entry point for T010a preprocessing."""
    parser = argparse.ArgumentParser(description="Preprocess EEG data (T010a)")
    parser.add_argument("--input-dir", type=str, default=None, help="Override input raw directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output cleaned directory")
    args = parser.parse_args()

    # Paths
    raw_dir = args.input_dir if args.input_dir else get_path("raw_data")
    output_dir = args.output_dir if args.output_dir else os.path.join(
        get_path("interim"), "cleaned_eeg_final"
    )
    
    # Ensure output directory exists
    ensure_dirs(output_dir)
    
    # Exclusion log path
    exclusion_log_path = os.path.join(get_path("interim"), "exclusion_log.csv")
    
    # Load files
    print(f"Scanning for data in: {raw_dir}")
    file_list = load_physionet_eeg_data(raw_dir)
    
    if not file_list:
        print("No EEG data files found. Creating empty exclusion log.")
        pd.DataFrame(columns=["participant_id", "reason", "channels_rejected_ratio"]).to_csv(
            exclusion_log_path, index=False
        )
        return

    print(f"Found {len(file_list)} files.")
    
    exclusion_log: List[Dict[str, Any]] = []
    processed_count = 0
    excluded_count = 0

    for f_path in file_list:
        print(f"Processing: {f_path}")
        result = preprocess_subject(f_path, output_dir, exclusion_log)
        if result:
            processed_count += 1
        else:
            excluded_count += 1

    # Save Exclusion Log
    if exclusion_log:
        df_exclusion = pd.DataFrame(exclusion_log)
        df_exclusion.to_csv(exclusion_log_path, index=False)
        print(f"Exclusion log saved to: {exclusion_log_path}")
    else:
        # Create empty file if no exclusions
        pd.DataFrame(columns=["participant_id", "reason", "channels_rejected_ratio"]).to_csv(
            exclusion_log_path, index=False
        )
        
    print(f"Processing complete. Processed: {processed_count}, Excluded: {excluded_count}")

if __name__ == "__main__":
    main()
