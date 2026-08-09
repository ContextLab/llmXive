import os
import sys
import json
import glob
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from config import get_path, ensure_dirs, get_seed, set_global_seed

def load_behavioral_trials(data_dir: str) -> pd.DataFrame:
    """
    Load behavioral trial data from the raw data directory.
    
    Expects PhysioNet EEG Motor Movement/Imagery dataset structure.
    Searches for .mat files containing reaction time data or 
    .csv files with trial-level data.
    
    Returns:
        DataFrame with columns: participant_id, trial_id, reaction_time_ms, condition
    """
    # Check for CSV files first (common format for processed behavioral data)
    csv_files = list(Path(data_dir).rglob("*.csv"))
    
    # Check for MATLAB files (original PhysioNet format)
    mat_files = list(Path(data_dir).rglob("*.mat"))
    
    if not csv_files and not mat_files:
        raise FileNotFoundError(
            f"No behavioral data files found in {data_dir}. "
            "Expected .csv or .mat files containing reaction time data."
        )
    
    all_trials = []
    
    # Try to load CSV files first
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # Normalize column names
            df.columns = [col.lower().strip() for col in df.columns]
            
            # Look for reaction time column
            rt_col = None
            possible_rt_cols = ['reaction_time', 'reactiontime', 'rt', 'trial_rt', 'response_time']
            for col in possible_rt_cols:
                if col in df.columns:
                    rt_col = col
                    break
            
            # Look for participant ID
            pid_col = None
            possible_pid_cols = ['participant_id', 'subject_id', 'participant', 'subject', 'id']
            for col in possible_pid_cols:
                if col in df.columns:
                    pid_col = col
                    break
            
            if rt_col and pid_col:
                # Extract participant ID from filename if not in data
                trials = df[[pid_col, rt_col]].copy()
                trials.columns = ['participant_id', 'reaction_time_ms']
                trials['trial_id'] = range(len(trials))
                trials['condition'] = 'unknown'  # Will be refined if available
                all_trials.append(trials)
                
        except Exception as e:
            print(f"Warning: Could not parse {csv_file}: {e}")
            continue
    
    # Try to load MATLAB files if CSV loading didn't work well
    if not all_trials and mat_files:
        try:
            import scipy.io
            for mat_file in mat_files:
                try:
                    mat_data = scipy.io.loadmat(mat_file)
                    # Look for common variable names in PhysioNet data
                    for var_name in mat_data:
                        if var_name.startswith('__'):
                            continue
                        data = mat_data[var_name]
                        if isinstance(data, np.ndarray) and data.ndim == 2:
                            # Try to interpret as trial data
                            if data.shape[1] >= 2:
                                # Assume first column is participant/trial info, second is RT
                                trials = pd.DataFrame({
                                    'participant_id': [int(mat_file.stem.split('_')[-1])],
                                    'reaction_time_ms': data[:, 1],
                                    'trial_id': range(len(data))
                                })
                                trials['condition'] = 'unknown'
                                all_trials.append(trials)
                                break
                except Exception as e:
                    print(f"Warning: Could not parse {mat_file}: {e}")
                    continue
        except ImportError:
            print("Warning: scipy not available for MATLAB file loading")
    
    if not all_trials:
        raise ValueError(
            "Could not extract trial-level data from any files. "
            "Ensure data files contain reaction time information."
        )
    
    combined = pd.concat(all_trials, ignore_index=True)
    
    # Ensure numeric types
    combined['reaction_time_ms'] = pd.to_numeric(
        combined['reaction_time_ms'], errors='coerce'
    )
    combined['participant_id'] = pd.to_numeric(
        combined['participant_id'], errors='coerce'
    )
    
    # Drop rows with missing RT or participant ID
    combined = combined.dropna(subset=['reaction_time_ms', 'participant_id'])
    
    return combined

def process_behavioral_data(
    trials_df: pd.DataFrame,
    min_rt_ms: float = 100.0,
    max_rt_ms: float = 2000.0,
    min_trial_ratio: float = 0.70
) -> tuple:
    """
    Process behavioral data to compute median RT and exclusion criteria.
    
    Args:
        trials_df: DataFrame with participant_id and reaction_time_ms
        min_rt_ms: Minimum valid RT threshold (outliers below this are excluded)
        max_rt_ms: Maximum valid RT threshold (outliers above this are excluded)
        min_trial_ratio: Minimum ratio of trials required to include participant
    
    Returns:
        tuple: (metrics_df, exclusion_log_df)
            - metrics_df: One row per included participant with median RT
            - exclusion_log_df: Log of all exclusion decisions
    """
    # Step 1: Identify and exclude outlier trials
    outlier_mask = (
        (trials_df['reaction_time_ms'] < min_rt_ms) | 
        (trials_df['reaction_time_ms'] > max_rt_ms)
    )
    
    outlier_trials = trials_df[outlier_mask].copy()
    outlier_trials['exclusion_reason'] = 'outlier_rt'
    
    valid_trials = trials_df[~outlier_mask].copy()
    
    # Step 2: Count trials per participant
    trial_counts = valid_trials.groupby('participant_id').size().reset_index(name='valid_trials')
    total_counts = trials_df.groupby('participant_id').size().reset_index(name='total_trials')
    
    # Merge to get ratios
    counts_df = total_counts.merge(trial_counts, on='participant_id', how='left')
    counts_df['valid_trials'] = counts_df['valid_trials'].fillna(0).astype(int)
    counts_df['trial_ratio'] = counts_df['valid_trials'] / counts_df['total_trials']
    
    # Step 3: Identify participants to exclude due to insufficient trials
  # Step 3: Identify participants to exclude due to insufficient trials
    insufficient_trials = counts_df[counts_df['trial_ratio'] < min_trial_ratio]
    
    # Create exclusion log
    exclusion_log = []
    
    # Log outlier exclusions
    for _, row in outlier_trials.iterrows():
        exclusion_log.append({
            'participant_id': int(row['participant_id']),
            'trial_id': int(row['trial_id']),
            'reaction_time_ms': float(row['reaction_time_ms']),
            'exclusion_reason': 'outlier_rt'
        })
    
    # Log participant exclusions
    for _, row in insufficient_trials.iterrows():
        exclusion_log.append({
            'participant_id': int(row['participant_id']),
            'trial_id': None,
            'reaction_time_ms': None,
            'exclusion_reason': f"insufficient_trials (ratio={row['trial_ratio']:.2f}, min={min_trial_ratio})"
        })
    
    exclusion_log_df = pd.DataFrame(exclusion_log)
    
    # Step 4: Compute metrics for included participants
    included_participants = counts_df[counts_df['trial_ratio'] >= min_trial_ratio]
    
    # Filter valid trials to only included participants
    included_trials = valid_trials[
        valid_trials['participant_id'].isin(included_participants['participant_id'])
    ]
    
    # Compute median RT per participant
    metrics = included_trials.groupby('participant_id')['reaction_time_ms'].agg([
        ('median_rt_ms', 'median'),
        ('mean_rt_ms', 'mean'),
        ('std_rt_ms', 'std'),
        ('n_valid_trials', 'count'),
        ('n_total_trials', lambda x: total_counts[total_counts['participant_id'] == x.name]['total_trials'].values[0] if len(total_counts[total_counts['participant_id'] == x.name]) > 0 else 0)
    ]).reset_index()
    
    # Add trial ratio to metrics
    metrics = metrics.merge(
        included_participants[['participant_id', 'trial_ratio']], 
        on='participant_id'
    )
    
    # Ensure numeric types
    metrics['participant_id'] = metrics['participant_id'].astype(int)
    metrics['median_rt_ms'] = metrics['median_rt_ms'].round(2)
    metrics['mean_rt_ms'] = metrics['mean_rt_ms'].round(2)
    metrics['std_rt_ms'] = metrics['std_rt_ms'].round(2)
    metrics['trial_ratio'] = metrics['trial_ratio'].round(3)
    
    return metrics, exclusion_log_df

def main():
    """
    Main entry point for behavioral metrics extraction.
    
    Outputs:
        - data/interim/behavioral_metrics.csv: One row per included participant
        - data/interim/behavioral_exclusion_log.csv: Log of all exclusions
    """
    parser = argparse.ArgumentParser(
        description='Extract behavioral metrics from trial data'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default=None,
        help='Path to raw data directory (defaults to data/raw/behavioral)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Path to output directory (defaults to data/interim)'
    )
    parser.add_argument(
        '--min-rt',
        type=float,
        default=100.0,
        help='Minimum valid reaction time in ms'
    )
    parser.add_argument(
        '--max-rt',
        type=float,
        default=2000.0,
        help='Maximum valid reaction time in ms'
    )
    parser.add_argument(
        '--min-trial-ratio',
        type=float,
        default=0.70,
        help='Minimum ratio of valid trials required'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Set seed
    set_global_seed(args.seed)
    
    # Determine paths
    data_dir = args.data_dir or str(get_path('raw_behavioral'))
    output_dir = args.output_dir or str(get_path('interim'))
    
    # Ensure output directory exists
    ensure_dirs([output_dir])
    
    print(f"Loading behavioral data from: {data_dir}")
    
    # Load trial data
    try:
        trials_df = load_behavioral_trials(data_dir)
        print(f"Loaded {len(trials_df)} trials from {trials_df['participant_id'].nunique()} participants")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading behavioral data: {e}")
        sys.exit(1)
    
    # Process data
    print(f"Processing behavioral data (min_rt={args.min_rt}ms, max_rt={args.max_rt}ms, min_ratio={args.min_trial_ratio})")
    metrics_df, exclusion_log_df = process_behavioral_data(
        trials_df,
        min_rt_ms=args.min_rt,
        max_rt_ms=args.max_rt,
        min_trial_ratio=args.min_trial_ratio
    )
    
    # Save outputs
    metrics_path = Path(output_dir) / 'behavioral_metrics.csv'
    exclusion_path = Path(output_dir) / 'behavioral_exclusion_log.csv'
    
    metrics_df.to_csv(metrics_path, index=False)
    exclusion_log_df.to_csv(exclusion_path, index=False)
    
    print(f"\nResults:")
    print(f"  Included participants: {len(metrics_df)}")
    print(f"  Excluded participants: {exclusion_log_df['participant_id'].nunique()}")
    print(f"  Outlier trials: {len(exclusion_log_df[exclusion_log_df['exclusion_reason'] == 'outlier_rt'])}")
    print(f"  Insufficient trials: {len(exclusion_log_df[exclusion_log_df['exclusion_reason'].str.contains('insufficient')])}")
    print(f"\nOutput files:")
    print(f"  Metrics: {metrics_path}")
    print(f"  Exclusion log: {exclusion_path}")
    
    # Verify outputs exist
    if not metrics_path.exists():
        raise RuntimeError(f"Failed to create {metrics_path}")
    if not exclusion_path.exists():
        raise RuntimeError(f"Failed to create {exclusion_path}")
    
    print("\nBehavioral metrics extraction completed successfully.")

if __name__ == '__main__':
    main()
