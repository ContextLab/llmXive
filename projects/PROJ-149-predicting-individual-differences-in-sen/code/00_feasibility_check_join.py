"""
T008a [US0] Create code/00_feasibility_check_join.py to join EEG and RT datasets.
Checks: Verify RT dataset contains "Simple Reaction Time" task; verify demographic metadata.
Filter out participants with missing RT data; log to data/interim/feasibility_exclusion_log.csv.
Output: data/interin/joined_metadata.csv on success (excluding missing RT participants).
If join fails or tasks mismatch, generate data/processed/feasibility_report.md and exit with code 1.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from config import get_path, ensure_dirs

def load_physionet_metadata(data_dir: str) -> pd.DataFrame:
    """
    Load EEG metadata from PhysioNet directory structure.
    Scans for subject directories and extracts metadata.
    """
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    subjects = []
    # PhysioNet EEG Motor Movement/Imagery structure: sub-XX/ sub-XX/
    for item in sorted(os.listdir(data_dir)):
        if item.startswith("sub-"):
            subject_id = item.replace("sub-", "")
            # Check for task files to determine available tasks
            subject_path = os.path.join(data_dir, item)
            tasks_found = []
            if os.path.isdir(subject_path):
                for f in os.listdir(subject_path):
                    if f.endswith(".edf") or f.endswith(".vhdr"):
                        # Extract task name from filename if possible, otherwise default
                        # Format: sub-XX_task-YY_run-ZZ.edf
                        if "_task-" in f:
                            task_part = f.split("_task-")[1].split("_")[0]
                            tasks_found.append(task_part)
                        else:
                            tasks_found.append("unknown")

            if tasks_found:
                # Create one row per task found for this subject
                for task in tasks_found:
                    subjects.append({
                        'participant_id': subject_id,
                        'task': task,
                        'source': 'eeg'
                    })

    if not subjects:
        raise RuntimeError("No EEG subject data found in directory.")

    return pd.DataFrame(subjects)

def load_behavioral_metadata(data_dir: str) -> pd.DataFrame:
    """
    Load behavioral metadata.
    In this dataset, behavioral data is often embedded in EEG annotations or separate CSVs.
    We attempt to find a behavioral CSV or derive from EEG annotations if available.
    For this implementation, we assume a 'behavioral_metadata.csv' exists in data_dir
    or we derive simple metrics from the EEG structure if the file is missing (fallback to mock for structure only, 
    but T007/T013 will populate real data later. Here we just ensure the join logic works).
    
    NOTE: Per T008a requirements, we must verify "Simple Reaction Time" exists.
    If the real behavioral file is missing, we raise an error to prevent proceeding with fake data.
    """
    # Try to find a behavioral file
    possible_names = ["behavioral_metadata.csv", "rt_data.csv", "subjects_info.csv"]
    bf_path = None
    for name in possible_names:
        candidate = os.path.join(data_dir, name)
        if os.path.exists(candidate):
            bf_path = candidate
            break

    if bf_path:
        df = pd.read_csv(bf_path)
        # Ensure participant_id column exists
        if 'participant_id' not in df.columns:
            # Try to infer
            if 'subject_id' in df.columns:
                df['participant_id'] = df['subject_id']
            else:
                raise ValueError("Behavioral metadata missing 'participant_id' or 'subject_id' column.")
        return df
    else:
        # If no behavioral file found, we cannot verify RT tasks.
        # However, T007 downloads data. If T007 succeeded but no behavioral file exists,
        # we must fail hard per T008a "hard HALT" requirement.
        # We do NOT generate synthetic data.
        raise FileNotFoundError(
            f"Behavioral metadata file not found in {data_dir}. "
            f"Expected one of: {possible_names}. "
            "T008a requires real RT data to verify 'Simple Reaction Time' task."
        )

def main():
    print("Starting feasibility check join...")

    # Determine data directory
    data_dir = get_path("raw_data")
    if not os.path.exists(data_dir):
        data_dir = get_path("data_raw")
    
    if not os.path.exists(data_dir):
        print("ERROR: Data directory not found. Ensure T007 (download) has run.")
        sys.exit(1)

    # Load data
    try:
        eeg_meta = load_physionet_metadata(data_dir)
        print(f"Loaded EEG metadata: {len(eeg_meta)} rows.")
    except Exception as e:
        report_content = f"Feasibility Failed: EEG metadata load error - {str(e)}"
        report_path = get_path("processed", "feasibility_report.md")
        ensure_dirs(report_path)
        with open(report_path, 'w') as f:
            f.write(f"# Feasibility Report\n\n{report_content}\n")
        print(report_content)
        sys.exit(1)

    try:
        rt_meta = load_behavioral_metadata(data_dir)
        print(f"Loaded Behavioral metadata: {len(rt_meta)} rows.")
    except Exception as e:
        report_content = f"Feasibility Failed: Behavioral metadata load error - {str(e)}"
        report_path = get_path("processed", "feasibility_report.md")
        ensure_dirs(report_path)
        with open(report_path, 'w') as f:
            f.write(f"# Feasibility Report\n\n{report_content}\n")
        print(report_content)
        sys.exit(1)

    # Verify RT dataset contains "Simple Reaction Time"
    task_col = None
    for col in ['task', 'task_name', 'condition']:
        if col in rt_meta.columns:
            task_col = col
            break
    
    if task_col:
        unique_tasks = rt_meta[task_col].unique()
        if "Simple Reaction Time" not in unique_tasks:
            # Generate report and exit
            report_content = f"Feasibility Failed: No 'Simple Reaction Time' task found in RT dataset. Found: {unique_tasks}"
            report_path = get_path("processed", "feasibility_report.md")
            ensure_dirs(report_path)
            with open(report_path, 'w') as f:
                f.write(f"# Feasibility Report\n\n{report_content}\n")
            print(report_content)
            sys.exit(1)
        print("Verified: 'Simple Reaction Time' task exists in RT dataset.")
    else:
        # If no task column, we can't verify. Fail hard.
        report_content = "Feasibility Failed: RT dataset missing 'task' column. Cannot verify 'Simple Reaction Time'."
        report_path = get_path("processed", "feasibility_report.md")
        ensure_dirs(report_path)
        with open(report_path, 'w') as f:
            f.write(f"# Feasibility Report\n\n{report_content}\n")
        print(report_content)
        sys.exit(1)

    # Join on participant_id
    try:
        # Standardize column names for join
        eeg_join = eeg_meta[['participant_id', 'task']].rename(columns={'task': 'task_eeg'})
        rt_join = rt_meta[['participant_id', task_col]].rename(columns={task_col: 'task_rt'})
        
        # Add median_rt if present, otherwise assume it will be populated later or is missing
        if 'median_rt' in rt_meta.columns:
            rt_join = rt_join.merge(rt_meta[['participant_id', 'median_rt']], on='participant_id', how='left')
        
        joined = pd.merge(eeg_join, rt_join, on='participant_id', how='inner')
    except Exception as e:
        report_content = f"Feasibility Failed: Join error - {str(e)}"
        report_path = get_path("processed", "feasibility_report.md")
        ensure_dirs(report_path)
        with open(report_path, 'w') as f:
            f.write(f"# Feasibility Report\n\n{report_content}\n")
        print(report_content)
        sys.exit(1)

    # Filter out missing RT data
    initial_count = len(joined)
    excluded_ids = []
    
    if 'median_rt' in joined.columns:
        # Drop rows where median_rt is NaN
        valid_mask = joined['median_rt'].notna()
        excluded_ids = joined.loc[~valid_mask, 'participant_id'].tolist()
        joined = joined[valid_mask]
    else:
        # If median_rt column is missing entirely, exclude all as per "missing RT data" rule
        excluded_ids = joined['participant_id'].tolist()
        joined = joined.iloc[:0]

    excluded_count = initial_count - len(joined)

    # Log exclusion
    exclusion_log_path = get_path("interim", "feasibility_exclusion_log.csv")
    ensure_dirs(exclusion_log_path)
    if excluded_ids:
        pd.DataFrame({
            'participant_id': excluded_ids,
            'reason': ['missing_rt'] * len(excluded_ids)
        }).to_csv(exclusion_log_path, index=False)
    else:
        # Create empty file with headers
        pd.DataFrame(columns=['participant_id', 'reason']).to_csv(exclusion_log_path, index=False)

    # Save joined metadata
    joined_path = get_path("interim", "joined_metadata.csv")
    ensure_dirs(joined_path)
    joined.to_csv(joined_path, index=False)

    print(f"Join completed. {initial_count} initial, {excluded_count} excluded, {len(joined)} retained.")
    print(f"Exclusion log: {exclusion_log_path}")
    print(f"Joined metadata: {joined_path}")

if __name__ == "__main__":
    main()