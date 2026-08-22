"""
T010 [US1] Implement code/02_preprocess_eeg.py:
Full Preprocessing Pipeline:
1. Apply 1–40 Hz band-pass filter, 50/60 Hz notch.
2. Reject channels with variance > 3 SD from mean variance (Spec FR-002).
3. Apply ICA (0.99 variance retention) to remove ocular/muscle artifacts.
4. Exclude participants if ratio of rejected channels > 0.30.

Output:
- data/interim/preprocessed_eeg/ (.fif)
- data/interim/ica_cleaned_eeg/ (.fif)
- data/interim/exclusion_log.csv (schema: participant_id, reason, channels_rejected_ratio)
"""
import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
import mne
from config import get_path, ensure_dirs, get_filter_params, get_ica_params, get_exclusion_params
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

def get_subject_id_from_path(filepath: str) -> str:
    """Extract subject ID from file path."""
    return Path(filepath).stem.split('_')[0] if '_' in Path(filepath).stem else Path(filepath).stem

def load_physionet_eeg_data(data_dir: str) -> List[str]:
    """Load list of EEG file paths."""
    return glob.glob(os.path.join(data_dir, "**/*.dat"), recursive=True)

def preprocess_subject(raw: mne.io.Raw, params: Dict[str, Any]) -> Tuple[Optional[mne.io.Raw], Dict[str, Any]]:
    """
    Preprocess a single subject:
    1. Band-pass filter
    2. Notch filter
    3. Bad channel rejection
    4. ICA
    Returns cleaned raw and stats dict.
    """
    # Filter
    raw = bandpass_filter(raw, params['lowcut'], params['highcut'])
    raw = notch_filter(raw, params['notch'])

    # Bad channel rejection
    rejected, ratio = reject_channels_by_variance(raw, params['bad_channel_threshold_std'])
    raw.info['bads'] = rejected

    # ICA
    raw, ica_info = apply_ica(raw, params['n_components'])

    return raw, {
        'rejected_channels': rejected,
        'rejection_ratio': ratio,
        'ica_components': ica_info.get('n_components', 0)
    }

def main():
    print("Starting EEG Preprocessing (T010)...")

    data_dir = get_path("raw_data")
    if not os.path.exists(data_dir):
        data_dir = get_path("data_raw")

    filter_params = get_filter_params()
    ica_params = get_ica_params()
    exclusion_params = get_exclusion_params()

    # Merge params
    preprocess_params = {**filter_params, **ica_params, **exclusion_params}

    # Load files
    eeg_files = load_physionet_eeg_data(data_dir)

    if not eeg_files:
        print(f"Warning: No EEG files found in {data_dir}")
        # Still create exclusion log with empty data
        exclusion_log_path = get_path("interim", "exclusion_log.csv")
        ensure_dirs(exclusion_log_path)
        pd.DataFrame(columns=['participant_id', 'reason', 'channels_rejected_ratio']).to_csv(exclusion_log_path, index=False)
        return

    # Directories
    preprocessed_dir = get_path("interim", "preprocessed_eeg")
    ica_cleaned_dir = get_path("interim", "ica_cleaned_eeg")
    final_cleaned_dir = get_path("interim", "cleaned_eeg_final")
    exclusion_log_path = get_path("interim", "exclusion_log.csv")

    ensure_dirs(preprocessed_dir)
    ensure_dirs(ica_cleaned_dir)
    ensure_dirs(final_cleaned_dir)
    ensure_dirs(exclusion_log_path)

    exclusion_log = []
    processed_count = 0

    for fpath in eeg_files:
        subj_id = get_subject_id_from_path(fpath)
        try:
            # Load raw data
            raw = mne.io.read_raw_edf(fpath, preload=True)
            
            # Preprocess
            raw_clean, stats = preprocess_subject(raw, preprocess_params)

            # Check exclusion ratio
            if stats['rejection_ratio'] > preprocess_params['max_bad_channel_ratio']:
                exclusion_log.append({
                    'participant_id': subj_id,
                    'reason': 'excessive_bad_channels',
                    'channels_rejected_ratio': stats['rejection_ratio']
                })
                print(f"Excluded {subj_id}: excessive bad channels ({stats['rejection_ratio']:.2%})")
                continue

            # Save preprocessed (after filtering, before ICA)
            preprocessed_out = os.path.join(preprocessed_dir, f"{subj_id}_preprocessed.fif")
            raw_clean.save(preprocessed_out, overwrite=True)

            # Save ICA cleaned
            ica_out = os.path.join(ica_cleaned_dir, f"{subj_id}_ica_cleaned.fif")
            raw_clean.save(ica_out, overwrite=True)

            # Save final cleaned
            final_out = os.path.join(final_cleaned_dir, f"{subj_id}_cleaned.fif")
            raw_clean.save(final_out, overwrite=True)
            
            processed_count += 1

        except Exception as e:
            print(f"Error processing {subj_id}: {e}")
            exclusion_log.append({
                'participant_id': subj_id, 
                'reason': 'processing_error', 
                'channels_rejected_ratio': 1.0
            })

    # Save exclusion log
    pd.DataFrame(exclusion_log).to_csv(exclusion_log_path, index=False)
    print(f"Preprocessing completed. Processed {processed_count}, Excluded {len(exclusion_log)} subjects.")
    print(f"Exclusion log saved to: {exclusion_log_path}")

if __name__ == "__main__":
    main()