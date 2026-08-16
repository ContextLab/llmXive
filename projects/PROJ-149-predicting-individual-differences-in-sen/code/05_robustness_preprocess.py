"""
T026b: Robustness Preprocessing - Window Size Variation (2s)

Re-runs the primary EEG preprocessing pipeline (T010a) with a modified
window size of 2 seconds instead of the default 4 seconds. This is a
robustness check to verify stability of results against window length.

All artifacts are written to `data/interim/robustness/window_2s/` to prevent
overwriting primary pipeline outputs.

Dependencies:
    - T010a (code/02_preprocess_eeg.py logic)
    - T007/T008 (Raw data availability)
"""

import os
import sys
import glob
import argparse
import numpy as np
import mne
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    load_config,
    get_path,
    ensure_dirs,
    get_filter_params,
    get_ica_params,
    get_exclusion_params,
    get_window_seconds,
    get_overlap_seconds,
    get_band_freqs,
    get_all_band_names
)
from utils.eeg_helpers import (
    bandpass_filter,
    notch_filter,
    reject_channels_by_variance,
    apply_ica
)


def get_subject_id_from_path(file_path: str) -> Optional[str]:
    """
    Extract subject ID from a PhysioNet file path.
    Expected format: .../sub-XXX/...
    """
    path_obj = Path(file_path)
    # Look for directory starting with 'sub-'
    for part in path_obj.parts:
        if part.startswith('sub-'):
            return part
    # Fallback: try to extract from filename if in a flat structure
    # e.g., sub-01_ses-1_task-rest_eeg.fif
    stem = path_obj.stem
    if stem.startswith('sub-'):
        return stem.split('_')[0]
    return None


def load_physionet_eeg_data(subject_id: str, raw_data_dir: str) -> Optional[mne.io.Raw]:
    """
    Load raw EEG data for a specific subject from the downloaded PhysioNet data.
    """
    # Search for files matching the subject ID in the raw data directory
    # PhysioNet structure: sub-XXX/ses-XXX/...
    search_pattern = os.path.join(raw_data_dir, f"sub-{subject_id}", "**", "*.fif")
    files = glob.glob(search_pattern, recursive=True)

    if not files:
        # Fallback search in case of flat structure
        search_pattern = os.path.join(raw_data_dir, f"*{subject_id}*", "*.fif")
        files = glob.glob(search_pattern, recursive=True)

    if not files:
        return None

    # Usually the first file found is the raw data
    # In PhysioNet Motor Imagery, raw files are often named sub-XXX_ses-XXX_task-XXX_eeg.fif
    # and may be split into multiple files if long. We assume the first one is raw.
    # For robustness, we might need to concatenate if multiple segments exist.
    raw_files = [f for f in files if 'eeg' in f and 'ave' not in f and 'proc' not in f]
    if not raw_files:
        # If no specific raw file found, take the first fif
        raw_files = files

    if not raw_files:
        return None

    # Sort to ensure consistent ordering
    raw_files.sort()

    try:
        # If multiple segments, concatenate them
        if len(raw_files) > 1:
            raw = mne.io.concatenate_raws([mne.io.read_raw_fif(f, preload=False) for f in raw_files])
        else:
            raw = mne.io.read_raw_fif(raw_files[0], preload=False)

        # Preload data for processing
        raw.load_data()
        return raw
    except Exception as e:
        print(f"Error loading raw data for {subject_id}: {e}")
        return None


def preprocess_subject(
    raw: mne.io.Raw,
    subject_id: str,
    output_dir: str,
    window_size: int,
    apply_ica_flag: bool = True
) -> Tuple[Optional[mne.io.Raw], Dict[str, Any]]:
    """
    Preprocess a single subject's EEG data with robustness-specific parameters.

    Args:
        raw: Raw MNE object
        subject_id: Subject identifier
        output_dir: Directory to save cleaned data
        window_size: Window size in seconds (2 for this robustness run)
        apply_ica_flag: Whether to apply ICA (True for this run, as we only change window size)

    Returns:
        Tuple of (cleaned_raw, exclusion_info)
    """
    exclusion_info = {
        'participant_id': subject_id,
        'reason': None,
        'channels_rejected_ratio': 0.0
    }

    try:
        # 1. Filter parameters (from config, but window size is overridden)
        filter_params = get_filter_params()
        ica_params = get_ica_params()
        exclusion_params = get_exclusion_params()

        # 2. Band-pass filter (1-40 Hz)
        raw_filtered = bandpass_filter(raw, filter_params['low_cutoff'], filter_params['high_cutoff'])

        # 3. Notch filter (50 or 60 Hz)
        raw_filtered = notch_filter(raw_filtered, filter_params['notch_freq'])

        # 4. Bad channel rejection (variance > 3 SD)
        original_chs = raw_filtered.info['ch_names']
        raw_cleaned, rejected_chs = reject_channels_by_variance(
            raw_filtered,
            std_threshold=exclusion_params['variance_std_threshold']
        )

        if len(rejected_chs) > 0:
            exclusion_info['channels_rejected_ratio'] = len(rejected_chs) / len(original_chs)

        # Check if too many channels were rejected
        if exclusion_info['channels_rejected_ratio'] > exclusion_params['max_channel_rejection_ratio']:
            exclusion_info['reason'] = f"Too many channels rejected ({exclusion_info['channels_rejected_ratio']:.2f})"
            return None, exclusion_info

        # 5. ICA for artifact removal (Mandatory for primary run, but we keep it for robustness unless --no-ica)
        # Note: T026b is specifically about window size, so ICA remains enabled.
        if apply_ica_flag:
            try:
                raw_cleaned = apply_ica(raw_cleaned, ica_params['n_components'], ica_params['method'])
            except Exception as e:
                # ICA failure is a hard exclusion per spec
                exclusion_info['reason'] = f"ICA failed: {str(e)}"
                return None, exclusion_info

        # 6. Save cleaned data
        # Ensure output directory exists
        ensure_dirs(output_dir)

        output_path = os.path.join(output_dir, f"sub-{subject_id}_cleaned.fif")
        raw_cleaned.save(output_path, overwrite=True)

        return raw_cleaned, exclusion_info

    except Exception as e:
        exclusion_info['reason'] = f"Processing error: {str(e)}"
        return None, exclusion_info


def run_robustness_pipeline(
    raw_data_dir: str,
    robustness_output_dir: str,
    window_size: int = 2,
    apply_ica: bool = True
):
    """
    Run the robustness preprocessing pipeline on all available subjects.

    Args:
        raw_data_dir: Path to raw downloaded data
        robustness_output_dir: Path to write robustness outputs (e.g., data/interim/robustness/window_2s/cleaned_eeg/)
        window_size: Window size in seconds (2 for T026b)
        apply_ica: Whether to apply ICA (True for T026b)
    """
    print(f"Starting Robustness Preprocessing (Window Size: {window_size}s)...")
    print(f"Input: {raw_data_dir}")
    print(f"Output: {robustness_output_dir}")

    # Find all subject directories
    subject_dirs = []
    for item in os.listdir(raw_data_dir):
        if item.startswith('sub-'):
            full_path = os.path.join(raw_data_dir, item)
            if os.path.isdir(full_path):
                subject_dirs.append(full_path)

    if not subject_dirs:
        print(f"No subject directories found in {raw_data_dir}")
        # Create empty exclusion log even if no data
        exclusion_log_path = os.path.join(robustness_output_dir, '..', '..', 'exclusion_log.csv')
        ensure_dirs(exclusion_log_path)
        with open(exclusion_log_path, 'w') as f:
            f.write("participant_id,reason,channels_rejected_ratio\n")
        return

    print(f"Found {len(subject_dirs)} subjects to process.")

    exclusion_logs = []
    processed_count = 0
    excluded_count = 0

    for subj_dir in subject_dirs:
        subject_id = os.path.basename(subj_dir)
        print(f"Processing {subject_id}...")

        # Load raw data
        raw = load_physionet_eeg_data(subject_id, raw_data_dir)
        if raw is None:
            exclusion_logs.append({
                'participant_id': subject_id,
                'reason': 'Raw data not found',
                'channels_rejected_ratio': 0.0
            })
            excluded_count += 1
            continue

        # Preprocess with robustness parameters
        cleaned_raw, exclusion_info = preprocess_subject(
            raw,
            subject_id,
            robustness_output_dir,
            window_size,
            apply_ica
        )

        if cleaned_raw is None:
            exclusion_logs.append(exclusion_info)
            excluded_count += 1
        else:
            processed_count += 1
            # Ensure reason is None if successful
            exclusion_info['reason'] = None
            exclusion_logs.append(exclusion_info)

    # Write exclusion log
    exclusion_log_path = os.path.join(
        os.path.dirname(robustness_output_dir),
        '..',
        'exclusion_log.csv'
    )
    ensure_dirs(exclusion_log_path)

    import pandas as pd
    df_exclusion = pd.DataFrame(exclusion_logs)
    df_exclusion.to_csv(exclusion_log_path, index=False)

    print(f"Robustness preprocessing complete.")
    print(f"Processed: {processed_count}, Excluded: {excluded_count}")
    print(f"Exclusion log written to: {exclusion_log_path}")


def main():
    """Main entry point for T026b robustness preprocessing."""
    parser = argparse.ArgumentParser(description="Robustness Preprocessing - Window Size Variation")
    parser.add_argument(
        '--window-size',
        type=int,
        default=2,
        help='Window size in seconds (default: 2 for T026b)'
    )
    parser.add_argument(
        '--no-ica',
        action='store_true',
        help='Disable ICA (not used for T026b, but kept for consistency with T026a)'
    )
    parser.add_argument(
        '--raw-data-dir',
        type=str,
        default=None,
        help='Override raw data directory path'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Override output directory path'
    )

    args = parser.parse_args()

    # Load config
    config = load_config()

    # Determine paths
    if args.raw_data_dir:
        raw_data_dir = args.raw_data_dir
    else:
        raw_data_dir = get_path('raw_data')

    # For T026b, output to data/interim/robustness/window_2s/cleaned_eeg/
    if args.output_dir:
        robustness_output_dir = args.output_dir
    else:
        base_robustness_dir = get_path('interim', 'robustness')
        robustness_output_dir = os.path.join(base_robustness_dir, 'window_2s', 'cleaned_eeg')

    # Ensure base robustness directory exists
    ensure_dirs(os.path.dirname(os.path.dirname(robustness_output_dir)))

    # Run pipeline
    run_robustness_pipeline(
        raw_data_dir=raw_data_dir,
        robustness_output_dir=robustness_output_dir,
        window_size=args.window_size,
        apply_ica=not args.no_ica
    )


if __name__ == "__main__":
    main()