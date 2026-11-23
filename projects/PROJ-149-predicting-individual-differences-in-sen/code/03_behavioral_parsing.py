"""
T013: Implement behavioral parsing for RT data.

Parses RT logs, excludes outliers (RT < 100ms, RT > 2000ms),
retains participants with >= 70% trials remaining.

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

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

# Constants for outlier detection
MIN_RT_MS = 100
MAX_RT_MS = 2000
MIN_TRIAL_RETENTION_RATIO = 0.70

def load_physionet_behavioral_data():
    """
    Load behavioral data from the downloaded RT dataset.
    The dataset was downloaded by T007b to data/raw/rt_data/
    We expect event files in TSV format.
    """
    rt_data_dir = get_path("raw", "rt_data")
    if not os.path.exists(rt_data_dir):
        raise FileNotFoundError(
            f"RT data directory not found: {rt_data_dir}. "
            "Please run T007b (01_download_rt_data.py) first."
        )
    
    # Look for TSV files containing RT events
    # Based on OpenNeuro ds000224 structure: sub-*/task-rt_events.tsv
    tsv_files = []
    for root, dirs, files in os.walk(rt_data_dir):
        for file in files:
            if file.endswith('_events.tsv') or file.endswith('task-rt_events.tsv'):
                tsv_files.append(os.path.join(root, file))
    
    if not tsv_files:
        # Fallback: look for any .tsv in the rt_data directory
        tsv_files = glob.glob(os.path.join(rt_data_dir, "**/*.tsv"), recursive=True)
    
    if not tsv_files:
        raise FileNotFoundError(
            f"No behavioral event TSV files found in {rt_data_dir}. "
            "Ensure T007b successfully downloaded the dataset."
        )
    
    all_data = []
    for tsv_file in tsv_files:
        try:
            df = pd.read_csv(tsv_file, sep='\t')
            # Try to identify participant ID from filename or path
            # OpenNeuro format: sub-XX/task-rt_events.tsv
            path_parts = Path(tsv_file).parts
            sub_id = None
            for part in path_parts:
                if part.startswith('sub-'):
                    sub_id = part.replace('sub-', '')
                    break
            
            if sub_id:
                df['participant_id'] = sub_id
                all_data.append(df)
        except Exception as e:
            print(f"Warning: Could not parse {tsv_file}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No valid behavioral data could be loaded from TSV files.")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df

def extract_rt_from_annotations(df):
    """
    Extract Reaction Time values from the dataframe.
    Looks for columns like 'reaction_time', 'rt', 'response_time', or 'onset'/'duration' based logic.
    """
    # Common column names for RT
    rt_columns = ['reaction_time', 'rt', 'response_time', 'trial_rt']
    
    rt_col = None
    for col in rt_columns:
        if col in df.columns:
            rt_col = col
            break
    
    if rt_col is None:
        # If no explicit RT column, try to calculate from onset/duration if available
        if 'onset' in df.columns and 'duration' in df.columns:
            # Sometimes RT is encoded as duration of a response event
            if 'duration' in df.columns:
                df['calculated_rt'] = df['duration'] * 1000  # Convert to ms if in seconds
                rt_col = 'calculated_rt'
            else:
                raise ValueError("Could not identify RT column in behavioral data.")
        else:
            raise ValueError("Could not identify RT column in behavioral data.")
    
    return df[rt_col].dropna()

def process_behavioral_data(df):
    """
    Process behavioral data:
    1. Filter outliers (RT < 100ms or RT > 2000ms)
    2. Calculate median RT
    3. Track exclusion counts
    4. Exclude participants with < 70% trials remaining
    
    Returns:
      metrics_df: DataFrame with participant_id, median_rt, n_trials, n_trials_excluded
      exclusion_log_df: DataFrame with participant_id, reason
    """
    metrics = []
    exclusion_log = []
    
    # Group by participant
    if 'participant_id' not in df.columns:
        # If no participant ID, treat as a single batch (unlikely for this project)
        df['participant_id'] = 'unknown'
    
    for pid, group in df.groupby('participant_id'):
        # Extract RTs
        rts = extract_rt_from_annotations(group)
        total_trials = len(rts)
        
        if total_trials == 0:
            exclusion_log.append({
                'participant_id': pid,
                'reason': 'no_trials'
            })
            continue
        
        # Filter outliers
        valid_mask = (rts >= MIN_RT_MS) & (rts <= MAX_RT_MS)
        valid_rts = rts[valid_mask]
        n_excluded = total_trials - len(valid_rts)
        
        # Check retention ratio
        retention_ratio = len(valid_rts) / total_trials
        
        if retention_ratio < MIN_TRIAL_RETENTION_RATIO:
            exclusion_log.append({
                'participant_id': pid,
                'reason': 'low_retention',
                'retention_ratio': retention_ratio
            })
            continue
        
        # Calculate metrics
        median_rt = np.median(valid_rts)
        
        metrics.append({
            'participant_id': pid,
            'median_rt': median_rt,
            'n_trials': len(valid_rts),
            'n_trials_excluded': n_excluded
        })
    
    metrics_df = pd.DataFrame(metrics)
    exclusion_log_df = pd.DataFrame(exclusion_log)
    
    # Ensure columns are in correct order if not empty
    if not metrics_df.empty:
        metrics_df = metrics_df[['participant_id', 'median_rt', 'n_trials', 'n_trials_excluded']]
    
    return metrics_df, exclusion_log_df

def main():
    parser = argparse.ArgumentParser(description="T013: Parse behavioral RT data")
    parser.add_argument('--input', type=str, default=None, help='Input directory override')
    parser.add_argument('--output-metrics', type=str, default=None, help='Output metrics file override')
    parser.add_argument('--output-exclusion', type=str, default=None, help='Output exclusion log override')
    args = parser.parse_args()
    
    print("Loading behavioral data...")
    try:
        rt_df = load_physionet_behavioral_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(rt_df)} rows of behavioral data.")
    
    print("Processing behavioral data...")
    metrics_df, exclusion_log_df = process_behavioral_data(rt_df)
    
    # Determine output paths
    output_metrics_path = args.output_metrics or get_path("interim", "behavioral_metrics.csv")
    output_exclusion_path = args.output_exclusion or get_path("interim", "behavioral_exclusion_log.csv")
    
    # Ensure directories exist
    ensure_dirs(output_metrics_path)
    ensure_dirs(output_exclusion_path)
    
    # Write outputs
    print(f"Writing behavioral metrics to {output_metrics_path}...")
    metrics_df.to_csv(output_metrics_path, index=False)
    
    print(f"Writing exclusion log to {output_exclusion_path}...")
    exclusion_log_df.to_csv(output_exclusion_path, index=False)
    
    print(f"Completed. {len(metrics_df)} participants retained, {len(exclusion_log_df)} excluded.")
    
    # Exit with code 1 if no participants remain (fail loudly)
    if len(metrics_df) == 0:
        print("Error: No participants met the retention criteria. Feasibility check failed.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()