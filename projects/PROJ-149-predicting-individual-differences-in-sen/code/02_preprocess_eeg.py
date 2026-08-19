"""
T010: Full Preprocessing Pipeline for EEG Data
Implements: Band-pass (1-40Hz), Notch (50/60Hz), Bad Channel Rejection, ICA Application.
Outputs: Preprocessed .fif files and exclusion logs.
"""
import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import mne

# Project imports
from config import (
    load_config, get_filter_params, get_ica_params, get_exclusion_params,
    get_path, ensure_dirs, set_global_seed
)
from utils.eeg_helpers import (
    bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica
)
from utils.memory_monitor import MemoryMonitor, run_with_memory_monitor

def get_subject_id_from_path(file_path: str) -> str:
    """Extract subject ID from file path (e.g., 'sub-01' from 'sub-01_task-rest...')."""
    path_obj = Path(file_path)
    # Expect format like sub-XX_task-XXX...
    stem = path_obj.stem
    if stem.startswith('sub-'):
        return stem.split('_')[0]
    return stem

def load_physionet_eeg_data(raw_data_dir: str, target_task: str = "Simple RT") -> List[Path]:
    """
    Load raw EEG data files from the downloaded PhysioNet directory.
    Filters for the specific task if necessary.
    """
    # Look for .fif files in the raw directory
    # PhysioNet data structure: sub-XX/sub-XX_task-XXX...
    raw_files = []
    for root, dirs, files in os.walk(raw_data_dir):
        for file in files:
            if file.endswith('.fif') or file.endswith('.edf'):
                f_path = Path(root) / file
                # Basic heuristic: check if task name is in filename
                # Note: PhysioNet Motor Movement/Imagery has tasks like 'open', 'close', etc.
                # We rely on the feasibility check to ensure we are looking at the right data.
                # For now, we accept all .fif/.edf files found in the raw dir.
                raw_files.append(f_path)
    
    if not raw_files:
        raise FileNotFoundError(f"No raw EEG files found in {raw_data_dir}")
    
    return raw_files

def preprocess_subject(
    raw_file: Path,
    output_preprocessed_dir: Path,
    output_ica_dir: Path,
    output_final_dir: Path,
    config: Dict[str, Any]
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Preprocess a single subject's EEG data.
    Returns: (subject_id, exclusion_info)
    """
    try:
        # Load raw data
        # Determine file type
        if str(raw_file).endswith('.fif'):
            raw = mne.io.read_raw_fif(raw_file, preload=True)
        elif str(raw_file).endswith('.edf'):
            raw = mne.io.read_raw_edf(raw_file, preload=True)
        else:
            # Try to guess or skip
            raw = mne.io.read_raw_raw(raw_file, preload=True) # Generic fallback

        # Set montage if available (standard 10-20 for EEG)
        # PhysioNet usually has standard channels
        try:
            raw.set_montage('standard_1020', match_case=False, match_alias=True)
        except Exception:
            pass # Ignore if montage fails, proceed with data

        subject_id = get_subject_id_from_path(str(raw_file))

        # 1. Band-pass filter (1-40 Hz)
        filter_params = get_filter_params(config)
        raw = bandpass_filter(raw, l_freq=filter_params['l_freq'], h_freq=filter_params['h_freq'])

        # 2. Notch filter (50 or 60 Hz)
        notch_freq = filter_params.get('notch_freq', 50)
        raw = notch_filter(raw, freq=notch_freq)

        # 3. Bad channel rejection (Variance > 3 SD)
        exclusion_params = get_exclusion_params(config)
        threshold_sd = exclusion_params.get('variance_threshold_sd', 3.0)
        
        # Reject bad channels
        bad_channels, raw_clean = reject_channels_by_variance(raw, threshold_sd=threshold_sd)
        rejected_ratio = len(bad_channels) / len(raw_clean.ch_names) if len(raw_clean.ch_names) > 0 else 1.0

        # Check exclusion criteria BEFORE ICA
        # If >30% channels rejected, exclude immediately
        max_ratio = exclusion_params.get('max_rejected_ratio', 0.30)
        if rejected_ratio > max_ratio:
            return subject_id, {
                'participant_id': subject_id,
                'reason': f'Bad channel rejection ratio {rejected_ratio:.2f} > {max_ratio}',
                'channels_rejected_ratio': rejected_ratio
            }

        # Save intermediate preprocessed (no ICA yet)
        preprocessed_path = output_preprocessed_dir / f"{subject_id}_preprocessed.fif"
        raw_clean.save(preprocessed_path, overwrite=True)

        # 4. ICA Application
        ica_params = get_ica_params(config)
        # ICA is MANDATORY for primary pipeline per spec
        ica = apply_ica(raw_clean, variance_retention=ica_params.get('variance_retention', 0.99))
        
        # Apply ICA to remove artifacts
        # Note: apply_ica returns the cleaned raw object
        raw_ica_clean = ica.apply(raw_clean)
        
        # Save ICA cleaned
        ica_path = output_ica_dir / f"{subject_id}_ica_cleaned.fif"
        raw_ica_clean.save(ica_path, overwrite=True)

        # Final check: Re-evaluate bad channels after ICA? 
        # Spec says: "Exclude participants if the ratio of rejected channels exceeds 0.30"
        # Usually this is done before ICA, but let's ensure final quality.
        # If we assume the initial rejection was the gate, we proceed.
        # Save to final directory
        final_path = output_final_dir / f"{subject_id}_final.fif"
        raw_ica_clean.save(final_path, overwrite=True)

        return subject_id, {
            'participant_id': subject_id,
            'reason': 'OK',
            'channels_rejected_ratio': rejected_ratio
        }

    except Exception as e:
        # Log error but continue with other subjects
        print(f"Error processing {raw_file}: {e}")
        return get_subject_id_from_path(str(raw_file)), {
            'participant_id': get_subject_id_from_path(str(raw_file)),
            'reason': f'Processing error: {str(e)}',
            'channels_rejected_ratio': 1.0
        }

def main():
    """Main execution flow for T010."""
    # Load config
    config = load_config()
    set_global_seed(config)

    # Define paths
    raw_data_dir = get_path('raw_data') # Or 'data_raw' depending on config key
    # Fallback if key not found, try common names
    if not os.path.exists(raw_data_dir):
        # Try to find the path from config or default
        # Assuming config has 'raw_data' or similar
        raw_data_dir = get_path('data_raw')

    output_preprocessed_dir = Path(get_path('interim')) / 'preprocessed_eeg'
    output_ica_dir = Path(get_path('interim')) / 'ica_cleaned_eeg'
    output_final_dir = Path(get_path('interim')) / 'cleaned_eeg_final'
    exclusion_log_path = Path(get_path('interim')) / 'exclusion_log.csv'

    # Ensure directories exist
    ensure_dirs(output_preprocessed_dir)
    ensure_dirs(output_ica_dir)
    ensure_dirs(output_final_dir)

    # Load raw files
    try:
        raw_files = load_physionet_eeg_data(raw_data_dir)
    except FileNotFoundError as e:
        print(f"CRITICAL: {e}")
        # Create empty exclusion log if no data
        pd.DataFrame(columns=['participant_id', 'reason', 'channels_rejected_ratio']).to_csv(exclusion_log_path, index=False)
        sys.exit(1)

    results = []
    excluded_count = 0

    # Process each subject
    for f_path in raw_files:
        print(f"Processing: {f_path}")
        subject_id, info = preprocess_subject(
            f_path, output_preprocessed_dir, output_ica_dir, output_final_dir, config
        )
        results.append(info)
        if info['reason'] != 'OK':
            excluded_count += 1

    # Create Exclusion Log
    df_results = pd.DataFrame(results)
    # Filter to only excluded ones for the log, or all?
    # Spec: "Output: data/interim/exclusion_log.csv"
    # Usually contains all processed, but we can filter to excluded for clarity.
    # Let's save all for traceability, or just excluded if that's the standard.
    # The spec says "Exclude participants if... Output: exclusion_log.csv".
    # We will save the log of excluded participants to be concise, or all if needed.
    # Let's save all processed subjects with their status.
    df_results.to_csv(exclusion_log_path, index=False)
    print(f"Exclusion log written to {exclusion_log_path}")
    print(f"Total subjects: {len(results)}, Excluded: {excluded_count}")

    # If no valid data remains, warn
    if excluded_count == len(results):
        print("WARNING: All subjects were excluded. Check data quality.")

if __name__ == "__main__":
    main()