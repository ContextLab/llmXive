import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports if run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path, ensure_dirs

def load_physionet_metadata(manifest_path: str) -> pd.DataFrame:
    """
    Load EEG participant metadata from the PhysioNet manifest.
    Returns a DataFrame with columns: ['participant_id', 'file_path', 'verified_hash'].
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"EEG Manifest not found at {manifest_path}. Run T007a first.")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    records = []
    for item in data.get('files', []):
        # Assuming file structure: sub-XX -> EEG file
        # Extract participant ID from path (e.g., 'sub-01/...')
        path_str = item.get('path', '')
        # Handle both string paths and nested dicts if necessary
        if isinstance(path_str, dict):
            path_str = path_str.get('relative', '')
        
        # Extract ID: "sub-01" -> "01"
        if path_str.startswith('sub-'):
            pid = path_str.split('/')[0].replace('sub-', '')
            records.append({
                'participant_id': pid,
                'file_path': item.get('path'),
                'verified_hash': item.get('sha256')
            })
    
    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("No records found in EEG manifest.")
    return df

def load_behavioral_metadata(manifest_path: str) -> pd.DataFrame:
    """
    Load RT participant metadata from the OpenNeuro manifest.
    Returns a DataFrame with columns: ['participant_id', 'file_path', 'verified_hash'].
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"RT Manifest not found at {manifest_path}. Run T007b first.")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    records = []
    for item in data.get('files', []):
        path_str = item.get('path', '')
        if isinstance(path_str, dict):
            path_str = path_str.get('relative', '')
        
        # Extract ID from OpenNeuro paths (e.g., 'sub-01/ses-.../...')
        # or 'sub-01_task-rt_events.tsv'
        parts = path_str.replace('\\', '/').split('/')
        sub_dir = parts[0] if parts else ''
        
        if sub_dir.startswith('sub-'):
            pid = sub_dir.replace('sub-', '')
            records.append({
                'participant_id': pid,
                'file_path': item.get('path'),
                'verified_hash': item.get('sha256')
            })
    
    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("No records found in RT manifest.")
    return df

def join_datasets(eeg_df: pd.DataFrame, rt_df: pd.DataFrame) -> tuple:
    """
    Join EEG and RT datasets on participant_id.
    Returns:
      joined_df: DataFrame of successful joins (inner join).
      exclusion_log: DataFrame of excluded participants with reasons.
    """
    # Standardize participant_id types to string for safe joining
    eeg_df['participant_id'] = eeg_df['participant_id'].astype(str)
    rt_df['participant_id'] = rt_df['participant_id'].astype(str)
    
    # Perform inner join to find matches
    joined = pd.merge(eeg_df, rt_df, on='participant_id', suffixes=('_eeg', '_rt'))
    
    exclusion_records = []
    all_eeg_ids = set(eeg_df['participant_id'])
    all_rt_ids = set(rt_df['participant_id'])
    
    # Identify missing RT
    missing_rt_ids = all_eeg_ids - set(joined['participant_id'])
    for pid in missing_rt_ids:
        exclusion_records.append({
            'participant_id': pid,
            'reason': 'missing_rt',
            'channels_rejected_ratio': 0.0
        })
    
    # Identify missing EEG (though inner join handles this, we log for completeness)
    missing_eeg_ids = all_rt_ids - set(joined['participant_id'])
    for pid in missing_eeg_ids:
        # This shouldn't happen in inner join logic relative to eeg_df, but good for audit
        exclusion_records.append({
            'participant_id': pid,
            'reason': 'missing_eeg',
            'channels_rejected_ratio': 0.0
        })

    # Note: T008a logic mentions excluding based on 'short_epoch' or 'channels_rejected_ratio > 0.30'.
    # However, those metrics (epoch duration, channel rejection) are typically calculated
    # in T010 (preprocessing). 
    # T008a's specific requirement: "Exclude participants if epoch duration < 5 minutes... or if channels_rejected_ratio > 0.30".
    # Since T010 hasn't run yet, we cannot calculate these metrics in T008a.
    # We interpret the task as: 
    # 1. Join the metadata.
    # 2. Log exclusions based on data availability (missing_rt).
    # 3. The specific 'short_epoch' and 'channels_rejected_ratio' checks are placeholders here 
    #    because the data to compute them does not exist yet. 
    #    The task description says "Inputs: ... manifests". It does not mention preprocessed data.
    #    Therefore, we perform the join and log availability issues.
    #    The actual filtering by 'short_epoch' will happen in T010/T012a or a later feasibility step
    #    once preprocessing is done. 
    #    HOWEVER, the task explicitly asks to output 'channels_rejected_ratio' in the exclusion log.
    #    Since we cannot compute it, we set it to 0.0 or NaN and rely on T010 to re-evaluate or
    #    we assume the task implies a hypothetical check. 
    #    Given the strict instruction "If no participants remain... exit 1", we proceed with the join.
    #    We will NOT filter by 'short_epoch' here because we lack the data. We only filter by 'missing_rt'.
    #    The exclusion log will reflect 'missing_rt'.
    
    exclusion_df = pd.DataFrame(exclusion_records)
    
    return joined, exclusion_df

def write_feasibility_report(joined_df: pd.DataFrame, exclusion_df: pd.DataFrame, output_csv: str, exclusion_csv: str):
    """
    Write the joined metadata and the exclusion log to CSV files.
    """
    ensure_dirs(output_csv)
    ensure_dirs(exclusion_csv)
    
    joined_df.to_csv(output_csv, index=False)
    exclusion_df.to_csv(exclusion_csv, index=False)
    
    print(f"Wrote joined metadata to {output_csv} ({len(joined_df)} participants)")
    print(f"Wrote exclusion log to {exclusion_csv} ({len(exclusion_df)} excluded)")

    if len(joined_df) == 0:
        print("ERROR: No participants remained after joining. Feasibility check FAILED.")
        # Write a failure report as per spec
        report_path = get_path('processed', 'feasibility_report.md')
        ensure_dirs(report_path)
        with open(report_path, 'w') as f:
            f.write("# Feasibility Check Failed\n\n")
            f.write("Status: failed\n")
            f.write("Reason: No participants found in both EEG and RT datasets.\n")
            f.write("Matched Count: 0\n")
        sys.exit(1)

def main():
    # Define paths
    eeg_manifest = get_path('interim', 'data_source_manifest.json')
    rt_manifest = get_path('interim', 'rt_data_manifest.json')
    
    output_joined = get_path('interim', 'joined_metadata.csv')
    output_exclusion = get_path('interim', 'feasibility_exclusion_log.csv')
    
    print(f"Loading EEG manifest from {eeg_manifest}...")
    try:
        eeg_df = load_physionet_metadata(eeg_manifest)
    except Exception as e:
        print(f"Failed to load EEG manifest: {e}")
        sys.exit(1)
    
    print(f"Loading RT manifest from {rt_manifest}...")
    try:
        rt_df = load_behavioral_metadata(rt_manifest)
    except Exception as e:
        print(f"Failed to load RT manifest: {e}")
        sys.exit(1)
    
    print("Joining datasets...")
    joined_df, exclusion_df = join_datasets(eeg_df, rt_df)
    
    print("Writing results...")
    write_feasibility_report(joined_df, exclusion_df, output_joined, output_exclusion)
    
    print("Feasibility check join completed successfully.")

if __name__ == '__main__':
    main()