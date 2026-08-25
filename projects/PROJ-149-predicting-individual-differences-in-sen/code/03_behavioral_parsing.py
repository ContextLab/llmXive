"""
Behavioral Data Parsing and Filtering (Task T013)

Parses reaction time (RT) logs from the PhysioNet EEG Motor Movement/Imagery dataset.
Excludes outliers (RT < 100ms or RT > 2000ms) and participants with insufficient trials.
Generates behavioral metrics and exclusion logs.

Inputs:
    - data/interin/joined_metadata.csv (from T008a)
    - Raw behavioral files from data/raw/ (downloaded by T007)

Outputs:
    - data/interim/behavioral_metrics.csv
    - data/interim/behavioral_exclusion_log.csv
"""

import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_path, ensure_dirs

# Constants
MIN_RT_MS = 100.0
MAX_RT_MS = 2000.0
MIN_TRIAL_RETENTION_RATIO = 0.70  # 70%

def load_physionet_behavioral_data(raw_data_dir: str) -> List[Dict[str, Any]]:
    """
    Load behavioral data files from the PhysioNet dataset.
    The dataset structure typically contains .edf files with annotations.
    We look for annotation files or specific behavioral text files if available.
    In the Motor Movement/Imagery dataset, reaction times are often embedded
    in the annotations of the .edf files or separate CSVs if processed.

    Since T007 downloads the raw data, we assume standard PhysioNet structure:
    data_raw_dir / subject / sub-XX_task-YY_eeg.edf

    We will attempt to extract RTs from annotations if present, or load
    pre-extracted CSVs if T007/T008a produced them.
    """
    # Check for pre-extracted behavioral CSVs (common in pipeline intermediates)
    # If T008a produced joined_metadata, it might have paths to behavioral data.
    # For this implementation, we look for specific patterns in the raw directory.
    
    behavioral_data = []
    
    # Strategy: Look for CSV files in the raw directory that might contain RTs
    # PhysioNet EEG Motor Movement/Imagery often has annotations.
    # If the raw data is just .edf, we might need to parse annotations.
    # However, for this task, we assume the existence of a parsed behavioral source
    # or we attempt to find a 'behavioral' or 'rt' folder if created by previous steps.
    
    # Fallback: If we can't find specific RT files, we assume the 'joined_metadata'
    # from T008a might contain the necessary info or we scan for .csv in raw.
    
    # Let's scan for any CSV files in the raw directory that look like behavioral data
    # or look for a specific 'behavioral' subdirectory if it exists.
    candidate_patterns = [
        os.path.join(raw_data_dir, "**", "*.csv"),
        os.path.join(raw_data_dir, "**", "*.txt"),
    ]
    
    found_files = []
    for pattern in candidate_patterns:
        found_files.extend(glob.glob(pattern, recursive=True))
    
    # Filter for likely behavioral files (containing 'rt', 'behavior', 'response')
    # or simply load all if they match a specific schema we expect.
    # Given the constraints, we assume the raw data might have been partially processed
    # by T007/T008a into a format we can read, or we look for the specific PhysioNet
    # annotation CSVs if they exist.
    
    # For the purpose of this task, we will simulate the reading of a standard
    # behavioral CSV format if found, or raise an error if no data is found.
    # In a real run, T007/T008a should have prepared this.
    
    # Let's try to find a file named 'behavioral_data.csv' or similar in the interim
    # or raw folder.
    potential_rt_file = os.path.join(raw_data_dir, "behavioral_data.csv")
    if os.path.exists(potential_rt_file):
        df = pd.read_csv(potential_rt_file)
        # Expected columns: participant_id, rt_ms, trial_type, etc.
        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        if 'participant_id' in df.columns and 'rt' in df.columns:
            # Ensure RT is numeric
            df['rt'] = pd.to_numeric(df['rt'], errors='coerce')
            behavioral_data.append(df)
    
    # If not found in root, scan subdirectories
    if not behavioral_data:
        for root, dirs, files in os.walk(raw_data_dir):
            for file in files:
                if file.endswith('.csv') or file.endswith('.tsv'):
                    # Heuristic: file contains 'rt' or 'behavior' or is in a subject folder
                    # and has columns matching our expectation.
                    try:
                        df = pd.read_csv(os.path.join(root, file))
                        cols = [c.strip().lower() for c in df.columns]
                        if 'participant_id' in cols and any('rt' in c for c in cols):
                            # Normalize RT column name to 'rt'
                            rt_col = next(c for c in cols if 'rt' in c)
                            if rt_col != 'rt':
                                df = df.rename(columns={rt_col: 'rt'})
                            df['rt'] = pd.to_numeric(df['rt'], errors='coerce')
                            behavioral_data.append(df)
                    except Exception:
                        continue
    
    if not behavioral_data:
        # If still nothing, we might need to look at the joined_metadata to see if
        # it points to a specific file, or we assume the data is missing.
        # For this task, we will raise an error if no data is found to avoid silent failure.
        raise FileNotFoundError(
            "No behavioral data files (CSV/TSV with 'participant_id' and 'rt') found in raw_data_dir. "
            "Ensure T007 and T008a have successfully downloaded and joined the data."
        )
    
    return behavioral_data

def extract_rt_from_annotations(edf_path: str) -> Optional[pd.DataFrame]:
    """
    Attempt to extract RTs from EDF annotations if CSVs are not available.
    This is a fallback for raw .edf files.
    """
    try:
        import mne
        raw = mne.io.read_raw_edf(edf_path, preload=False)
        events, event_id = mne.events_from_annotations(raw)
        
        # Look for annotations that might represent responses
        # This is highly dataset-specific. In PhysioNet Motor Imagery,
        # there aren't always explicit RT annotations unless it's a specific task.
        # We'll return None if we can't find clear RT markers.
        if not events.size:
            return None
        
        # Construct a dummy dataframe if we find events, assuming event durations or
        # specific codes represent RTs. This is a placeholder logic.
        # In reality, we rely on the CSV extraction above.
        return None
    except Exception:
        return None

def process_behavioral_data(
    behavioral_data: List[pd.DataFrame],
    joined_metadata_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process behavioral data:
    1. Filter outliers (RT < 100ms or RT > 2000ms)
    2. Calculate median RT per participant
    3. Retain participants with >= 70% trials remaining
    4. Generate exclusion log
    """
    # Load joined metadata to know which participants we expect
    try:
        joined_df = pd.read_csv(joined_metadata_path)
    except FileNotFoundError:
        # If no joined metadata, we process all found data
        joined_ids = set()
    else:
        joined_ids = set(joined_df['participant_id'].astype(str))
    
    all_records = []
    exclusion_records = []
    
    for df in behavioral_data:
        # Ensure participant_id is string for consistent joining
        if 'participant_id' in df.columns:
            df['participant_id'] = df['participant_id'].astype(str)
        
        # If we have joined_ids, filter to only those
        if joined_ids:
            df = df[df['participant_id'].isin(joined_ids)]
        
        if df.empty:
            continue
        
        # Group by participant
        for pid, group in df.groupby('participant_id'):
            total_trials = len(group)
            if total_trials == 0:
                exclusion_records.append({
                    'participant_id': pid,
                    'reason': 'no_trials'
                })
                continue
            
            # Filter outliers
            valid_mask = (group['rt'] >= MIN_RT_MS) & (group['rt'] <= MAX_RT_MS)
            valid_trials = group[valid_mask]
            n_valid = len(valid_trials)
            n_excluded = total_trials - n_valid
            
            # Check retention ratio
            retention_ratio = n_valid / total_trials
            
            if retention_ratio < MIN_TRIAL_RETENTION_RATIO:
                exclusion_records.append({
                    'participant_id': pid,
                    'reason': 'low_trial_retention'
                })
                continue
            
            # Calculate metrics
            median_rt = valid_trials['rt'].median()
            
            all_records.append({
                'participant_id': pid,
                'median_rt': median_rt,
                'n_trials': n_valid,
                'n_trials_excluded': n_excluded
            })
    
    metrics_df = pd.DataFrame(all_records)
    exclusion_df = pd.DataFrame(exclusion_records)
    
    return metrics_df, exclusion_df

def main():
    parser = argparse.ArgumentParser(description="Parse behavioral data and filter outliers.")
    parser.add_argument("--raw-data-dir", type=str, default=None,
                        help="Path to raw data directory. Defaults to config 'data_raw'.")
    parser.add_argument("--joined-metadata", type=str, default=None,
                        help="Path to joined metadata CSV. Defaults to config 'interim/joined_metadata.csv'.")
    args = parser.parse_args()
    
    # Resolve paths
    if args.raw_data_dir:
        raw_data_dir = args.raw_data_dir
    else:
        raw_data_dir = get_path("data_raw")
    
    if args.joined_metadata:
        joined_metadata_path = args.joined_metadata
    else:
        joined_metadata_path = get_path("interim", "joined_metadata.csv")
    
    # Ensure output directories exist
    interim_dir = get_path("interim")
    ensure_dirs(interim_dir)
    
    metrics_path = os.path.join(interim_dir, "behavioral_metrics.csv")
    exclusion_path = os.path.join(interim_dir, "behavioral_exclusion_log.csv")
    
    print(f"Loading behavioral data from: {raw_data_dir}")
    print(f"Using joined metadata: {joined_metadata_path}")
    
    # Load data
    try:
        behavioral_data_list = load_physionet_behavioral_data(raw_data_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print(f"Found {len(behavioral_data_list)} behavioral data files.")
    
    # Process data
    metrics_df, exclusion_df = process_behavioral_data(behavioral_data_list, joined_metadata_path)
    
    # Save outputs
    metrics_df.to_csv(metrics_path, index=False)
    exclusion_df.to_csv(exclusion_path, index=False)
    
    print(f"Saved behavioral metrics to: {metrics_path}")
    print(f"Saved exclusion log to: {exclusion_path}")
    print(f"Total participants processed: {len(metrics_df)}")
    print(f"Total participants excluded: {len(exclusion_df)}")

if __name__ == "__main__":
    main()