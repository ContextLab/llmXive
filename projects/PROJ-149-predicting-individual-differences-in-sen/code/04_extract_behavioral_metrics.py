"""
T013: Behavioral Parsing and Metric Extraction

Implements behavioral parsing: extract median RT, exclude outliers (<100ms, >2000ms),
exclude participants if <70% trials remain (FR-004).

Outputs:
    data/interim/behavioral_metrics.csv (columns: participant_id, median_rt, n_trials, n_trials_excluded)
    data/interim/behavioral_exclusion_log.csv (columns: participant_id, reason)
"""

import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Add project root to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_path, ensure_dirs

# Constants from FR-004
MIN_RT_MS = 100
MAX_RT_MS = 2000
MIN_TRIAL_RATIO = 0.70  # Must retain at least 70% of trials

# Expected task names in the dataset
EXPECTED_TASKS = ["Simple Reaction Time", "Simple RT"]


def load_physionet_behavioral_data(raw_data_dir: str) -> pd.DataFrame:
    """
    Load behavioral data from PhysioNet EEG Motor Movement/Imagery dataset.
    The dataset contains .mat files with reaction time data.

    Args:
        raw_data_dir: Path to the raw data directory.

    Returns:
        DataFrame with reaction time data.
    """
    # Look for .mat files containing behavioral data
    # The PhysioNet EEG Motor Movement/Imagery dataset stores data in .mat files
    # We need to extract reaction times from these files

    # First, try to find the specific task files
    # In the PhysioNet dataset, the "Simple Reaction Time" task is part of the
    # EEG Motor Movement/Imagery dataset (subject 001-009)

    # For this implementation, we'll look for the specific subject directories
    # and extract the reaction time data from the annotations or .mat files

    behavioral_data = []

    # Search for subject directories
    subject_dirs = sorted(glob.glob(os.path.join(raw_data_dir, "*", "EEG")))

    if not subject_dirs:
        # Try alternative pattern
        subject_dirs = sorted(glob.glob(os.path.join(raw_data_dir, "sub-*", "EEG")))

    for subject_dir in subject_dirs:
        subject_id = os.path.basename(os.path.dirname(subject_dir))

        # Look for EEG files
        eeg_files = glob.glob(os.path.join(subject_dir, "*.edf"))
        if not eeg_files:
            eeg_files = glob.glob(os.path.join(subject_dir, "*.EDF"))

        if not eeg_files:
            continue

        for eeg_file in eeg_files:
            # Try to load the file using mne (if available)
            try:
                import mne
                raw = mne.io.read_raw_edf(eeg_file, preload=False)
                annotations = raw.annotations

                # Extract reaction times from annotations
                # Look for annotations that contain "RT" or "reaction"
                rt_events = []
                for onset, duration, description in zip(
                    raw.annotations.onset, raw.annotations.duration, raw.annotations.description
                ):
                    # Check if this is a reaction time event
                    desc_lower = description.lower()
                    if any(term in desc_lower for term in ["rt", "reaction", "button"]):
                        # Extract RT from the description or duration
                        # In some datasets, RT is stored in the description
                        try:
                            # Try to parse RT from description
                            parts = description.split("_")
                            for part in parts:
                                if part.isdigit() or (part.replace(".", "").isdigit()):
                                    rt_ms = float(part)
                                    rt_events.append({
                                        "participant_id": subject_id,
                                        "rt_ms": rt_ms,
                                        "onset": onset,
                                        "description": description
                                    })
                                    break
                        except (ValueError, AttributeError):
                            # If we can't parse, use duration as RT
                            if duration > 0:
                                rt_events.append({
                                    "participant_id": subject_id,
                                    "rt_ms": duration * 1000,  # Convert to ms
                                    "onset": onset,
                                    "description": description
                                })

                if rt_events:
                    behavioral_data.extend(rt_events)

            except Exception as e:
                # If mne is not available or file can't be read, try alternative methods
                print(f"Warning: Could not load {eeg_file}: {e}")
                continue

    if not behavioral_data:
        # If no RT data found in annotations, try to extract from .mat files
        # The PhysioNet dataset may have .mat files with behavioral data
        mat_files = glob.glob(os.path.join(raw_data_dir, "**/*.mat"), recursive=True)

        for mat_file in mat_files:
            try:
                import scipy.io
                mat_data = scipy.io.loadmat(mat_file)

                # Look for RT data in the mat file
                # Common keys: 'rt', 'reaction_time', 'response_time'
                rt_keys = [k for k in mat_data.keys() if any(term in k.lower() for term in ["rt", "reaction", "response"])]

                if rt_keys:
                    for key in rt_keys:
                        rt_values = mat_data[key]
                        if rt_values.ndim == 1:
                            for i, rt_val in enumerate(rt_values):
                                behavioral_data.append({
                                    "participant_id": os.path.basename(os.path.dirname(mat_file)),
                                    "rt_ms": rt_val * 1000 if rt_val < 1000 else rt_val,  # Assume seconds if > 1000
                                    "trial_id": i,
                                    "source": mat_file
                                })
                        elif rt_values.ndim == 2:
                            for i, row in enumerate(rt_values):
                                if len(row) > 0:
                                    behavioral_data.append({
                                        "participant_id": os.path.basename(os.path.dirname(mat_file)),
                                        "rt_ms": row[0] * 1000 if row[0] < 1000 else row[0],
                                        "trial_id": i,
                                        "source": mat_file
                                    })
            except Exception as e:
                print(f"Warning: Could not load {mat_file}: {e}")
                continue

    if not behavioral_data:
        raise RuntimeError(
            "No behavioral data found in the dataset. "
            "Please ensure the PhysioNet EEG Motor Movement/Imagery dataset is properly downloaded "
            "and contains the 'Simple Reaction Time' task files."
        )

    return pd.DataFrame(behavioral_data)


def extract_rt_from_eeg_annotations(raw_data_dir: str) -> pd.DataFrame:
    """
    Alternative method: Extract RT from EEG annotations using mne.

    Args:
        raw_data_dir: Path to the raw data directory.

    Returns:
        DataFrame with reaction time data.
    """
    import mne

    behavioral_data = []

    # Search for subject directories
    subject_dirs = sorted(glob.glob(os.path.join(raw_data_dir, "*", "EEG")))
    if not subject_dirs:
        subject_dirs = sorted(glob.glob(os.path.join(raw_data_dir, "sub-*", "EEG")))

    for subject_dir in subject_dirs:
        subject_id = os.path.basename(os.path.dirname(subject_dir))

        # Look for EEG files
        eeg_files = glob.glob(os.path.join(subject_dir, "*.edf"))
        if not eeg_files:
            eeg_files = glob.glob(os.path.join(subject_dir, "*.EDF"))

        for eeg_file in eeg_files:
            try:
                raw = mne.io.read_raw_edf(eeg_file, preload=False)
                annotations = raw.annotations

                # Extract RT events
                for onset, duration, description in zip(
                    annotations.onset, annotations.duration, annotations.description
                ):
                    desc_lower = description.lower()
                    if any(term in desc_lower for term in ["rt", "reaction", "button", "response"]):
                        # Try to extract RT value
                        rt_ms = None

                        # Method 1: Parse from description
                        parts = description.split("_")
                        for part in parts:
                            try:
                                val = float(part)
                                if 50 < val < 5000:  # Reasonable RT range in ms
                                    rt_ms = val
                                    break
                            except ValueError:
                                continue

                        # Method 2: Use duration if available
                        if rt_ms is None and duration > 0:
                            rt_ms = duration * 1000

                        if rt_ms is not None:
                            behavioral_data.append({
                                "participant_id": subject_id,
                                "rt_ms": rt_ms,
                                "onset": onset,
                                "description": description
                            })
            except Exception as e:
                print(f"Warning: Could not process {eeg_file}: {e}")
                continue

    if not behavioral_data:
        raise RuntimeError("No RT events found in EEG annotations.")

    return pd.DataFrame(behavioral_data)


def process_behavioral_data(df: pd.DataFrame) -> tuple:
    """
    Process behavioral data: filter outliers, calculate metrics, and generate exclusion logs.

    Args:
        df: DataFrame with RT data (columns: participant_id, rt_ms, ...)

    Returns:
        tuple: (metrics_df, exclusion_log_df)
        - metrics_df: DataFrame with columns (participant_id, median_rt, n_trials, n_trials_excluded)
        - exclusion_log_df: DataFrame with columns (participant_id, reason)
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Ensure rt_ms is numeric
    df['rt_ms'] = pd.to_numeric(df['rt_ms'], errors='coerce')
    df = df.dropna(subset=['rt_ms'])

    metrics_list = []
    exclusion_list = []

    # Group by participant
    for participant_id, group in df.groupby('participant_id'):
        original_n = len(group)
        rt_values = group['rt_ms'].values

        # Filter outliers (<100ms or >2000ms)
        valid_mask = (rt_values >= MIN_RT_MS) & (rt_values <= MAX_RT_MS)
        valid_rt = rt_values[valid_mask]
        n_excluded_outliers = original_n - len(valid_rt)

        # Calculate remaining trials
        remaining_trials = len(valid_rt)
        trial_ratio = remaining_trials / original_n if original_n > 0 else 0

        # Check minimum trial ratio (FR-004)
        if trial_ratio < MIN_TRIAL_RATIO:
            exclusion_list.append({
                'participant_id': participant_id,
                'reason': f"Insufficient trials after outlier removal: {trial_ratio:.2%} < {MIN_TRIAL_RATIO:.0%} (retained {remaining_trials}/{original_n})"
            })
            continue

        # Calculate median RT
        median_rt = np.median(valid_rt)

        metrics_list.append({
            'participant_id': participant_id,
            'median_rt': median_rt,
            'n_trials': remaining_trials,
            'n_trials_excluded': n_excluded_outliers
        })

    # Create DataFrames
    metrics_df = pd.DataFrame(metrics_list)
    exclusion_log_df = pd.DataFrame(exclusion_list)

    # Sort by participant_id
    metrics_df = metrics_df.sort_values('participant_id').reset_index(drop=True)
    exclusion_log_df = exclusion_log_df.sort_values('participant_id').reset_index(drop=True)

    return metrics_df, exclusion_log_df


def main():
    """Main entry point for T013."""
    parser = argparse.ArgumentParser(description="Extract behavioral metrics from EEG dataset.")
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Path to raw data directory. If not provided, uses config path."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Path to output directory. If not provided, uses config path."
    )
    args = parser.parse_args()

    # Determine input directory
    if args.input_dir:
        raw_data_dir = args.input_dir
    else:
        raw_data_dir = get_path("data_raw")

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = get_path("interim")

    # Ensure output directory exists
    ensure_dirs(output_dir)

    print(f"Loading behavioral data from {raw_data_dir}...")

    try:
        # Load data using primary method
        df = load_physionet_behavioral_data(raw_data_dir)
    except RuntimeError as e:
        print(f"Primary load failed: {e}. Trying alternative method...")
        try:
            df = extract_rt_from_eeg_annotations(raw_data_dir)
        except RuntimeError as e2:
            print(f"Alternative load also failed: {e2}")
            # If both fail, raise the original error
            raise e

    print(f"Loaded {len(df)} RT events.")

    # Process data
    print("Processing behavioral data...")
    metrics_df, exclusion_log_df = process_behavioral_data(df)

    # Define output paths
    metrics_path = os.path.join(output_dir, "behavioral_metrics.csv")
    exclusion_log_path = os.path.join(output_dir, "behavioral_exclusion_log.csv")

    # Write outputs
    print(f"Writing metrics to {metrics_path}...")
    metrics_df.to_csv(metrics_path, index=False)

    print(f"Writing exclusion log to {exclusion_log_path}...")
    exclusion_log_df.to_csv(exclusion_log_path, index=False)

    # Summary
    print(f"\nSummary:")
    print(f"  - Total participants processed: {len(metrics_df) + len(exclusion_log_df)}")
    print(f"  - Participants retained: {len(metrics_df)}")
    print(f"  - Participants excluded: {len(exclusion_log_df)}")
    if len(metrics_df) > 0:
        print(f"  - Median RT (overall): {metrics_df['median_rt'].median():.2f} ms")
    if len(exclusion_log_df) > 0:
        print(f"  - Exclusion reasons:")
        for reason in exclusion_log_df['reason'].unique():
            count = len(exclusion_log_df[exclusion_log_df['reason'] == reason])
            print(f"    - {reason}: {count}")

    print("\nT013 completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
