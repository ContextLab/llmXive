"""
Feasibility Join Script (T008a)

Joins EEG and RT datasets on participant_id.
Identifies continuous recording segments from EEG metadata.
Outputs joined metadata and exclusion logs.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

def load_physionet_metadata(manifest_path: Path) -> pd.DataFrame:
    """
    Load EEG metadata from the data source manifest.
    Extracts participant_id and segment information.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"EEG manifest not found: {manifest_path}")
        
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    # Expected structure: list of files with metadata
    records = []
    for file_entry in manifest_data.get('files', []):
        # Extract subject ID from filename or metadata
        # Format expected: sub-XX_ses-XX_task-XX_eeg.edf or similar
        file_path = file_entry.get('path', '')
        filename = os.path.basename(file_path)
        
        # Parse subject ID (assuming format sub-XX or SXX)
        # Handle both PhysioNet (SXX) and BIDS (sub-XX) formats
        if filename.startswith('sub-'):
            parts = filename.split('_')
            subject_id = parts[0].replace('sub-', '')
        elif filename.startswith('S'):
            # Extract number after S
            subject_id = filename.split('.')[0].replace('S', '')
        else:
            # Try to find S followed by digits
            import re
            match = re.search(r'S(\d+)', filename)
            if match:
                subject_id = match.group(1)
            else:
                continue
        
        # Extract session info if present
        session_id = None
        if 'ses-' in filename:
            ses_match = re.search(r'ses-(\w+)', filename)
            if ses_match:
                session_id = ses_match.group(1)
        
        # Calculate segment duration (in seconds)
        # For raw EEG files, we estimate based on typical recording lengths
        # or read from metadata if available
        duration_seconds = file_entry.get('duration', 3600)  # Default 1 hour
        
        records.append({
            'participant_id': f"S{subject_id.zfill(2)}",
            'eeg_file': file_path,
            'session_id': session_id,
            'segment_id': f"{f'S{subject_id.zfill(2)}'}_seg1",  # Single continuous segment per file
            'segment_duration': duration_seconds,
            'file_hash': file_entry.get('hash', '')
        })
    
    return pd.DataFrame(records)

def load_behavioral_metadata(manifest_path: Path) -> pd.DataFrame:
    """
    Load RT data metadata from the data source manifest.
    Extracts participant_id and RT file information.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"RT manifest not found: {manifest_path}")
        
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    records = []
    for file_entry in manifest_data.get('files', []):
        file_path = file_entry.get('path', '')
        filename = os.path.basename(file_path)
        
        # Parse subject ID from filename
        # Expected formats: sub-XX_task-rt_events.tsv or sub-XX_task-rt_bold.json
        if filename.startswith('sub-'):
            parts = filename.split('_')
            subject_id = parts[0].replace('sub-', '')
        elif filename.startswith('S'):
            subject_id = filename.split('.')[0].replace('S', '')
        else:
            import re
            match = re.search(r'S(\d+)', filename)
            if match:
                subject_id = match.group(1)
            else:
                continue
        
        records.append({
            'participant_id': f"S{subject_id.zfill(2)}",
            'rt_file': file_path,
            'file_hash': file_entry.get('hash', '')
        })
    
    return pd.DataFrame(records)

def join_datasets(eeg_df: pd.DataFrame, rt_df: pd.DataFrame) -> tuple:
    """
    Join EEG and RT datasets on participant_id.
    Returns (joined_df, exclusion_log_df)
    """
    # Perform inner join to find matching participants
    joined = pd.merge(
        eeg_df, 
        rt_df, 
        on='participant_id', 
        how='inner'
    )
    
    # Identify exclusions
    exclusion_records = []
    
    # Participants with EEG but no RT
    eeg_only = eeg_df[~eeg_df['participant_id'].isin(rt_df['participant_id'])]
    for _, row in eeg_only.iterrows():
        exclusion_records.append({
            'participant_id': row['participant_id'],
            'reason': 'missing_rt',
            'segment_count': 1  # Assuming one segment per file
        })
    
    # Participants with RT but no EEG
    rt_only = rt_df[~rt_df['participant_id'].isin(eeg_df['participant_id'])]
    for _, row in rt_only.iterrows():
        exclusion_records.append({
            'participant_id': row['participant_id'],
            'reason': 'missing_eeg',
            'segment_count': 0
        })
    
    exclusion_df = pd.DataFrame(exclusion_records)
    
    return joined, exclusion_df

def write_feasibility_report(joined_df: pd.DataFrame, exclusion_df: pd.DataFrame, 
                             output_dir: Path, timestamp: str):
    """
    Write the joined metadata and exclusion logs to disk.
    """
    # Ensure output directory exists
    ensure_dirs(output_dir)
    
    # Write joined metadata
    joined_path = output_dir / 'joined_metadata.csv'
    joined_df.to_csv(joined_path, index=False)
    print(f"✓ Joined metadata written to: {joined_path}")
    
    # Write exclusion log
    exclusion_path = output_dir / 'feasibility_exclusion_log.csv'
    exclusion_df.to_csv(exclusion_path, index=False)
    print(f"✓ Exclusion log written to: {exclusion_path}")
    
    # Write summary report
    summary = {
        'timestamp': timestamp,
        'total_eeg_participants': len(eeg_df) if 'eeg_df' in locals() else 0,
        'total_rt_participants': len(rt_df) if 'rt_df' in locals() else 0,
        'matched_participants': len(joined_df),
        'excluded_participants': len(exclusion_df),
        'exclusion_breakdown': {
            'missing_rt': len(exclusion_df[exclusion_df['reason'] == 'missing_rt']),
            'missing_eeg': len(exclusion_df[exclusion_df['reason'] == 'missing_eeg'])
        }
    }
    
    summary_path = output_dir / 'join_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Summary written to: {summary_path}")
    
    return summary

def main():
    """
    Main entry point for the feasibility join script.
    """
    print("=" * 60)
    print("Feasibility Join: EEG + RT Datasets")
    print("=" * 60)
    
    # Define paths
    eeg_manifest_path = get_path('interim', 'data_source_manifest.json')
    rt_manifest_path = get_path('interim', 'rt_data_manifest.json')
    output_dir = get_path('interim')
    
    # Check if manifests exist
    if not eeg_manifest_path.exists():
        print(f"ERROR: EEG manifest not found at {eeg_manifest_path}")
        print("Please run T007a (download_data.py) first.")
        sys.exit(1)
    
    if not rt_manifest_path.exists():
        print(f"ERROR: RT manifest not found at {rt_manifest_path}")
        print("Please run T007b (download_rt_data.py) first.")
        sys.exit(1)
    
    # Load metadata
    print("\n[1/4] Loading EEG metadata...")
    try:
        eeg_df = load_physionet_metadata(eeg_manifest_path)
        print(f"    Loaded {len(eeg_df)} EEG records")
    except Exception as e:
        print(f"ERROR: Failed to load EEG metadata: {e}")
        sys.exit(1)
    
    print("\n[2/4] Loading RT metadata...")
    try:
        rt_df = load_behavioral_metadata(rt_manifest_path)
        print(f"    Loaded {len(rt_df)} RT records")
    except Exception as e:
        print(f"ERROR: Failed to load RT metadata: {e}")
        sys.exit(1)
    
    # Join datasets
    print("\n[3/4] Joining datasets on participant_id...")
    try:
        joined_df, exclusion_df = join_datasets(eeg_df, rt_df)
        print(f"    Matched: {len(joined_df)} participants")
        print(f"    Excluded: {len(exclusion_df)} participants")
    except Exception as e:
        print(f"ERROR: Failed to join datasets: {e}")
        sys.exit(1)
    
    # Write outputs
    print("\n[4/4] Writing output files...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        summary = write_feasibility_report(joined_df, exclusion_df, output_dir, timestamp)
    except Exception as e:
        print(f"ERROR: Failed to write output files: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Feasibility Join Complete!")
    print(f"  Matched participants: {summary['matched_participants']}")
    print(f"  Excluded (missing RT): {summary['exclusion_breakdown']['missing_rt']}")
    print(f"  Excluded (missing EEG): {summary['exclusion_breakdown']['missing_eeg']}")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())