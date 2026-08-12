"""
T013: Behavioral Metrics Extraction

Extracts median Reaction Time (RT) from PhysioNet EEG Motor Movement/Imagery
annotations, excludes outliers (<100ms, >2000ms), and filters participants
with insufficient trials (<70% remaining).

Outputs:
  - data/interim/behavioral_metrics.csv: Cleaned metrics per participant
  - data/interim/behavioral_exclusion_log.csv: Log of excluded participants
"""

import os
import sys
import json
import glob
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_path, ensure_dirs, get_seed


def load_physionet_behavioral_data(data_dir: str) -> dict:
    """
    Load behavioral data (annotations) from PhysioNet EEG Motor Movement/Imagery dataset.
    The dataset structure typically has .edf files with annotations containing 'Trial' info.
    We parse the annotations to extract reaction times.

    Returns a dict mapping participant_id -> list of RTs (in ms).
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    # PhysioNet EEG Motor Movement/Imagery dataset structure:
    # Subject directories: 1, 2, ..., 109
    # Files: sub-<id>_run-<run>_eeg.edf
    # Annotations are embedded in the EDF files.

    participant_data = {}

    # Find all EDF files
    edf_files = glob.glob(str(data_path / "*" / "*.edf"))
    if not edf_files:
        # Try alternative structure (flat directory)
        edf_files = glob.glob(str(data_path / "*.edf"))

    if not edf_files:
        raise FileNotFoundError("No .edf files found in the data directory.")

    try:
        import mne
    except ImportError:
        raise ImportError("mne is required to read EDF annotations. Install it via requirements.txt.")

    for edf_path in edf_files:
        try:
            raw = mne.io.read_raw_edf(edf_path, preload=False)
            annotations = raw.annotations

            if len(annotations) == 0:
                continue

            # Extract participant ID from filename
            # Expected format: sub-<id>_run-<run>_eeg.edf or similar
            filename = os.path.basename(edf_path)
            # Heuristic: look for digits at the start or after 'sub-'
            import re
            match = re.search(r'(?:sub-)?(\d+)', filename)
            if not match:
                continue
            participant_id = int(match.group(1))

            # Extract RTs from annotations
            # In PhysioNet dataset, annotations often contain 'Trial' or specific markers
            # We look for annotations that represent reaction events
            rts = []
            for i, desc in enumerate(annotations.description):
                # Check if this annotation represents a reaction time event
                # The dataset uses specific annotation descriptions for events
                # We assume 'Trial' or numeric values in description indicate RT
                if 'Trial' in desc or desc.isdigit():
                    # If description is a number, it might be the RT in ms
                    try:
                        rt_val = float(desc)
                        # If the value is small (< 100), it might be seconds, convert to ms
                        if rt_val < 100 and rt_val > 0:
                            rt_val = rt_val * 1000
                        rts.append(rt_val)
                    except ValueError:
                        pass
                # Also check onset duration if it represents RT
                # Sometimes RT is stored in the duration field
                elif annotations.onset[i] > 0 and (annotations.duration[i] > 0):
                    # If duration is plausible as RT (100ms - 2000ms)
                    dur_ms = annotations.duration[i] * 1000
                    if 100 <= dur_ms <= 2000:
                        rts.append(dur_ms)

            if rts:
                if participant_id not in participant_data:
                    participant_data[participant_id] = []
                participant_data[participant_id].extend(rts)

        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Could not process {edf_path}: {e}")
            continue

    if not participant_data:
        raise ValueError("No valid behavioral data extracted from EDF files.")

    return participant_data


def extract_rt_from_eeg_annotations(annotations, participant_id: int) -> list:
    """
    Extract reaction times from MNE annotations for a specific participant.
    This is a helper if we need to process annotations differently.
    """
    rts = []
    for i, desc in enumerate(annotations.description):
        # Logic similar to above
        if 'Trial' in desc:
            try:
                rt_val = float(desc.split()[-1]) if ' ' in desc else float(desc)
                if rt_val < 100 and rt_val > 0:
                    rt_val *= 1000
                rts.append(rt_val)
            except ValueError:
                pass
    return rts


def process_behavioral_data(participant_data: dict) -> tuple:
    """
    Process raw RT data to compute median RT, exclude outliers, and filter participants.

    Args:
        participant_data: Dict mapping participant_id -> list of RTs (ms)

    Returns:
        tuple: (metrics_df, exclusion_log_df)
    """
    metrics = []
    exclusion_log = []

    outlier_low = 100.0
    outlier_high = 2000.0
    min_trial_ratio = 0.70

    for pid, rts in participant_data.items():
        if not rts:
            exclusion_log.append({
                'participant_id': pid,
                'reason': 'no_trials',
                'initial_trials': 0,
                'outliers_removed': 0,
                'remaining_trials': 0,
                'retention_ratio': 0.0
            })
            continue

        initial_count = len(rts)
        rts_array = np.array(rts)

        # Exclude outliers
        valid_mask = (rts_array >= outlier_low) & (rts_array <= outlier_high)
        valid_rts = rts_array[valid_mask]
        outliers_removed = initial_count - len(valid_rts)

        if len(valid_rts) == 0:
            exclusion_log.append({
                'participant_id': pid,
                'reason': 'all_outliers',
                'initial_trials': initial_count,
                'outliers_removed': outliers_removed,
                'remaining_trials': 0,
                'retention_ratio': 0.0
            })
            continue

        remaining_count = len(valid_rts)
        retention_ratio = remaining_count / initial_count

        if retention_ratio < min_trial_ratio:
            exclusion_log.append({
                'participant_id': pid,
                'reason': 'insufficient_trials',
                'initial_trials': initial_count,
                'outliers_removed': outliers_removed,
                'remaining_trials': remaining_count,
                'retention_ratio': retention_ratio
            })
            continue

        # Compute median RT
        median_rt = float(np.median(valid_rts))
        mean_rt = float(np.mean(valid_rts))
        std_rt = float(np.std(valid_rts))

        metrics.append({
            'participant_id': pid,
            'median_rt_ms': median_rt,
            'mean_rt_ms': mean_rt,
            'std_rt_ms': std_rt,
            'initial_trials': initial_count,
            'outliers_removed': outliers_removed,
            'remaining_trials': remaining_count,
            'retention_ratio': retention_ratio
        })

    metrics_df = pd.DataFrame(metrics)
    exclusion_log_df = pd.DataFrame(exclusion_log)

    return metrics_df, exclusion_log_df


def main():
    parser = argparse.ArgumentParser(description='Extract behavioral metrics from PhysioNet EEG data.')
    parser.add_argument('--data-dir', type=str, default=None,
                        help='Path to the raw data directory. Defaults to config setting.')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Path to the output directory. Defaults to config setting.')
    args = parser.parse_args()

    # Set seed for reproducibility (though not strictly needed for this task)
    seed = get_seed()
    np.random.seed(seed)

    # Determine paths
    if args.data_dir:
        data_dir = args.data_dir
    else:
        data_dir = get_path('raw', 'eeg')

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = get_path('interim')

    ensure_dirs([output_dir])

    print(f"Loading behavioral data from: {data_dir}")
    try:
        participant_data = load_physionet_behavioral_data(data_dir)
        print(f"Loaded data for {len(participant_data)} participants.")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    print("Processing behavioral data...")
    metrics_df, exclusion_log_df = process_behavioral_data(participant_data)

    # Save outputs
    metrics_path = os.path.join(output_dir, 'behavioral_metrics.csv')
    exclusion_path = os.path.join(output_dir, 'behavioral_exclusion_log.csv')

    metrics_df.to_csv(metrics_path, index=False)
    exclusion_log_df.to_csv(exclusion_path, index=False)

    print(f"Saved metrics to: {metrics_path}")
    print(f"Saved exclusion log to: {exclusion_path}")
    print(f"Total participants processed: {len(metrics_df) + len(exclusion_log_df)}")
    print(f"Participants retained: {len(metrics_df)}")
    print(f"Participants excluded: {len(exclusion_log_df)}")

    if len(metrics_df) == 0:
        print("Warning: No participants passed the inclusion criteria.")
        sys.exit(1)


if __name__ == '__main__':
    main()
