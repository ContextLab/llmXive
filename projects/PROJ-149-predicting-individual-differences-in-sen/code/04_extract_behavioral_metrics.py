"""
T013: Implement behavioral parsing.

Extracts median Reaction Time (RT) from the PhysioNet EEG Motor Movement/Imagery dataset.
Excludes outliers (<100ms, >2000ms) and participants with <70% valid trials remaining.

Outputs:
    data/interim/behavioral_metrics.csv
    data/interim/behavioral_exclusion_log.csv
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

# Constants for RT filtering
MIN_RT_MS = 100
MAX_RT_MS = 2000
MIN_VALID_TRIAL_RATIO = 0.70


def load_physionet_behavioral_data(raw_data_dir: str) -> pd.DataFrame:
    """
    Load behavioral data from PhysioNet EEG Motor Movement/Imagery dataset.
    
    The dataset structure typically contains .edf files. We need to extract
    reaction time annotations from these files. Since the raw EEG files 
    contain annotations for events, we parse those.
    
    For this specific dataset (PhysioNet EEG Motor Movement/Imagery),
    reaction time data is often embedded in the annotations or requires
    parsing the specific task conditions.
    
    Returns:
        pd.DataFrame: DataFrame with columns including participant_id, 
                      task_name, and raw RT events (if available).
    """
    # The PhysioNet EEG Motor Movement/Imagery dataset does not natively
    # provide a separate CSV of RTs. The "Simple Reaction Time" task 
    # (if present in the specific subset) has events marked in the EDF.
    # However, standard PhysioNet Motor Imagery data (2008) primarily 
    # contains Motor Imagery and Foot/Hand movement tasks, not necessarily 
    # a dedicated "Simple RT" task with explicit RT values in a CSV.
    
    # We will attempt to find any CSV files that might contain RT data 
    # (sometimes provided in competition versions or specific subsets)
    # or extract from EDF annotations if they contain time-delta info.
    
    # Strategy 1: Look for existing RT CSVs in the raw directory
    rt_csvs = glob.glob(os.path.join(raw_data_dir, "**/*rt*.csv"), recursive=True)
    rt_csvs += glob.glob(os.path.join(raw_data_dir, "**/*reaction*.csv"), recursive=True)
    
    if rt_csvs:
        dfs = []
        for csv_file in rt_csvs:
            try:
                df = pd.read_csv(csv_file)
                dfs.append(df)
            except Exception as e:
                print(f"Warning: Could not read {csv_file}: {e}")
        
        if dfs:
            return pd.concat(dfs, ignore_index=True)
    
    # Strategy 2: If no CSVs, we must parse the EDF files for annotations.
    # The task description implies "Simple Reaction Time" task exists.
    # If the dataset is the standard 2008 Motor Imagery, it might not have 
    # explicit RT values in a format we can easily parse without a specific 
    # protocol definition.
    
    # Fallback: If the data is missing or not in expected format, 
    # we must raise an error to fail loudly as per constraints.
    # We will scan for .edf files and attempt to read annotations.
    
    edf_files = glob.glob(os.path.join(raw_data_dir, "**/*.edf"), recursive=True)
    if not edf_files:
        raise FileNotFoundError(
            f"No behavioral data found (no RT CSVs or EDF files) in {raw_data_dir}. "
            "The dataset must contain 'Simple Reaction Time' task data."
        )
    
    # Attempt to extract RTs from EDF annotations
    # This assumes the annotations contain events like 'stimulus' and 'response'
    # or specific labels indicating RT tasks.
    import mne
    
    all_events = []
    
    for edf_path in edf_files:
        try:
            raw = mne.io.read_raw_edf(edf_path, preload=False)
            events, event_id = mne.events_from_annotations(raw)
            
            # Extract subject ID from filename
            base_name = os.path.basename(edf_path)
            # Format often: S001R01.edf -> Subject 1
            if 'S' in base_name:
                parts = base_name.split('S')
                if len(parts) > 1:
                    sub_id = int(parts[1].split('R')[0])
                else:
                    sub_id = 0
            else:
                sub_id = 0
            
            # Look for specific RT-related events
            # In many RT tasks, we look for pairs of events or specific codes
            # Since we don't have the exact event code mapping for RT in this generic 
            # dataset without more spec, we will assume the task description implies
            # we can find 'RT' or similar in annotations or we are simulating the 
            # extraction based on the task requirement.
            
            # However, strict adherence to "Real Data Only" means we cannot fake this.
            # If the standard PhysioNet dataset does not have explicit RT values,
            # we must report that.
            
            # Let's assume the presence of a specific annotation type 'RT' or 
            # we are parsing the 'Simple Reaction Time' task specifically.
            # If the dataset is purely Motor Imagery, this task might be impossible
            # without a specific RT subset.
            
            # For the purpose of this implementation, we will check if the 
            # annotations contain a 'response' or 'reaction' label.
            annotations = raw.annotations
            rt_events = []
            
            for i, (onset, duration, description) in enumerate(zip(
                annotations.onset, annotations.duration, annotations.description
            )):
                desc_lower = description.lower()
                if 'rt' in desc_lower or 'reaction' in desc_lower or 'response' in desc_lower:
                    rt_events.append({
                        'onset': onset,
                        'description': description,
                        'subject_id': sub_id
                    })
            
            if rt_events:
                all_events.extend(rt_events)
                
        except Exception as e:
            print(f"Warning: Could not process {edf_path}: {e}")
    
    if not all_events:
        # If we cannot find explicit RT events, we check if there is a 
        # known mapping or if we are expected to use a specific subset.
        # If the task requires "Simple Reaction Time" and it's not found,
        # we must fail.
        raise ValueError(
            "No 'Simple Reaction Time' task data found in the provided dataset. "
            "The PhysioNet EEG Motor Movement/Imagery dataset primarily contains "
            "Motor Imagery tasks. Please ensure the correct subset with RT data "
            "is provided or that the dataset contains the required task."
        )
    
    # Convert events to a DataFrame
    df = pd.DataFrame(all_events)
    # This is a simplified extraction. In a real scenario, we would need 
    # the specific event codes for stimulus and response to calculate RT.
    # If the data is not in the expected format, we raise.
    
    # Since the standard dataset might not have explicit RT values in annotations,
    # we might need to rely on a specific file provided with the task or 
    # a specific version of the data.
    
    # If we reach here, we assume the data was found but we need to format it.
    # We will return a placeholder structure that the user must fill with 
    # actual RT calculation logic if the raw events don't contain RT directly.
    # However, the constraint says "NO SYNTHETIC FALLBACKS".
    
    # Given the ambiguity of the dataset content vs task requirement, 
    # we will assume the task expects us to find a specific CSV or file 
    # that was downloaded in T007.
    
    # Let's re-scan for any CSV that might have been downloaded.
    # If T007 downloaded the dataset, it might have included a metadata file.
    metadata_files = glob.glob(os.path.join(raw_data_dir, "**/*metadata*.csv"), recursive=True)
    metadata_files += glob.glob(os.path.join(raw_data_dir, "**/*info*.csv"), recursive=True)
    
    if metadata_files:
        for mf in metadata_files:
            try:
                df_meta = pd.read_csv(mf)
                if 'rt' in df_meta.columns or 'reaction_time' in df_meta.columns:
                    return df_meta
            except:
                pass
    
    # If still nothing, we must fail.
    raise FileNotFoundError(
        "Could not locate any file containing Reaction Time data. "
        "The dataset must include a file with RT values for 'Simple Reaction Time' task."
    )


def extract_rt_from_eeg_annotations(raw_data_dir: str) -> pd.DataFrame:
    """
    Extracts RT values from EEG annotations if available.
    This is a fallback if no CSV is found.
    """
    # This function is a placeholder if the data is not in CSV format.
    # It attempts to parse EDF files for RT pairs.
    import mne
    
    edf_files = glob.glob(os.path.join(raw_data_dir, "**/*.edf"), recursive=True)
    rt_data = []
    
    for edf_path in edf_files:
        try:
            raw = mne.io.read_raw_edf(edf_path, preload=False)
            events, event_id = mne.events_from_annotations(raw)
            
            # Extract subject ID
            base_name = os.path.basename(edf_path)
            sub_id = int(base_name.split('S')[1].split('R')[0]) if 'S' in base_name else 0
            
            # Look for stimulus and response events
            # This is highly dataset-specific.
            # Assuming 'stimulus' and 'response' are in event_id or description
            stim_times = []
            resp_times = []
            
            for onset, duration, desc in zip(raw.annotations.onset, raw.annotations.duration, raw.annotations.description):
                if 'stimulus' in desc.lower():
                    stim_times.append(onset)
                elif 'response' in desc.lower():
                    resp_times.append(onset)
            
            if stim_times and resp_times:
                # Pair them up (simple assumption: one-to-one or first match)
                # This is a simplification. Real RT analysis needs precise pairing.
                for i, stim in enumerate(stim_times):
                    if i < len(resp_times):
                        rt = (resp_times[i] - stim) * 1000  # ms
                        rt_data.append({'participant_id': sub_id, 'rt_ms': rt})
                        
        except Exception as e:
            print(f"Warning: Error processing {edf_path}: {e}")
            
    return pd.DataFrame(rt_data)


def process_behavioral_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Processes behavioral data to compute median RT and exclusion logs.
    
    Args:
        df: DataFrame containing participant_id and rt_ms (or similar).
    
    Returns:
        Tuple[metrics_df, exclusion_log_df]
    """
    # Ensure participant_id is present
    if 'participant_id' not in df.columns:
        # Try to infer from index or other columns
        if 'subject_id' in df.columns:
            df = df.rename(columns={'subject_id': 'participant_id'})
        else:
            raise ValueError("Input DataFrame must contain 'participant_id' or 'subject_id'")
    
    # Ensure RT column exists
    rt_col = None
    for col in ['rt_ms', 'reaction_time', 'rt', 'response_time']:
        if col in df.columns:
            rt_col = col
            break
    
    if rt_col is None:
        raise ValueError("Input DataFrame must contain a reaction time column (rt_ms, reaction_time, etc.)")
    
    # Filter outliers
    valid_trials = df[(df[rt_col] >= MIN_RT_MS) & (df[rt_col] <= MAX_RT_MS)]
    invalid_trials = df[(df[rt_col] < MIN_RT_MS) | (df[rt_col] > MAX_RT_MS)]
    
    # Group by participant
    metrics = []
    exclusion_log = []
    
    for pid, group in df.groupby('participant_id'):
        total_trials = len(group)
        valid_group = valid_trials[valid_trials['participant_id'] == pid]
        valid_count = len(valid_group)
        excluded_count = total_trials - valid_count
        
        # Check minimum valid trial ratio
        if total_trials == 0:
            exclusion_log.append({'participant_id': pid, 'reason': 'No trials found'})
            continue
        
        ratio = valid_count / total_trials
        if ratio < MIN_VALID_TRIAL_RATIO:
            exclusion_log.append({
                'participant_id': pid, 
                'reason': f'Insufficient valid trials ({ratio:.2f} < {MIN_VALID_TRIAL_RATIO})'
            })
            continue
        
        # Compute median RT
        median_rt = valid_group[rt_col].median()
        
        metrics.append({
            'participant_id': pid,
            'median_rt': median_rt,
            'n_trials': total_trials,
            'n_trials_excluded': excluded_count
        })
    
    metrics_df = pd.DataFrame(metrics)
    exclusion_df = pd.DataFrame(exclusion_log)
    
    return metrics_df, exclusion_df


def main():
    parser = argparse.ArgumentParser(description="Extract behavioral metrics from PhysioNet data.")
    parser.add_argument("--input-dir", type=str, default=None, help="Path to raw data directory. Defaults to config.")
    args = parser.parse_args()
    
    # Determine input directory
    if args.input_dir:
        raw_data_dir = args.input_dir
    else:
        raw_data_dir = get_path("raw_data")
    
    # Ensure output directories exist
    interim_dir = get_path("interim")
    ensure_dirs(interim_dir)
    
    metrics_path = os.path.join(interim_dir, "behavioral_metrics.csv")
    exclusion_path = os.path.join(interim_dir, "behavioral_exclusion_log.csv")
    
    print(f"Loading behavioral data from {raw_data_dir}...")
    
    try:
        # Try to load from CSV first
        df = load_physionet_behavioral_data(raw_data_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Processing {len(df)} trials...")
    
    try:
        metrics_df, exclusion_df = process_behavioral_data(df)
    except ValueError as e:
        print(f"Error processing data: {e}")
        sys.exit(1)
    
    # Save outputs
    print(f"Saving metrics to {metrics_path}...")
    metrics_df.to_csv(metrics_path, index=False)
    
    print(f"Saving exclusion log to {exclusion_path}...")
    exclusion_df.to_csv(exclusion_path, index=False)
    
    print(f"Done. Processed {len(metrics_df)} participants. Excluded {len(exclusion_df)}.")


if __name__ == "__main__":
    main()
