"""
Preprocessing script for survey data.

This script loads raw survey submissions, filters for complete sessions,
and reshapes the data into wide format for statistical analysis.
"""
import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_submissions_csv_path():
    """Get the path to the raw submissions CSV."""
    return get_project_root() / 'data' / 'raw' / 'submissions.csv'

def get_cleaned_csv_path():
    """Get the path to the cleaned data CSV."""
    return get_project_root() / 'data' / 'processed' / 'cleaned_data.csv'

def get_excluded_audit_path():
    """Get the path to the excluded audit log."""
    return get_project_root() / 'data' / 'processed' / 'excluded_audit.json'

def load_raw_data():
    """Load raw survey data from CSV."""
    csv_path = get_submissions_csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw data not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    return df

def validate_and_filter(df):
    """
    Filter for complete sessions and validate data quality.
    
    A complete session has exactly 4 stimuli rated (8 ratings total: 4 credibility + 4 professionalism).
    """
    # Group by participant
    participant_counts = df.groupby('participant_id').size()
    
    # Identify complete sessions (exactly 4 stimuli)
    complete_participants = participant_counts[participant_counts == 4].index.tolist()
    incomplete_participants = participant_counts[participant_counts != 4].index.tolist()
    
    # Filter to complete sessions only
    df_complete = df[df['participant_id'].isin(complete_participants)].copy()
    
    # Audit excluded rows
    excluded_rows = []
    for pid in incomplete_participants:
        pid_rows = df[df['participant_id'] == pid]
        for _, row in pid_rows.iterrows():
            excluded_rows.append({
                'participant_id': pid,
                'reason': f"Incomplete session: {int(row['stimulus_id'].count()) if isinstance(row['stimulus_id'], str) else len(pid_rows)} stimuli rated",
                'timestamp': row.get('timestamp', ''),
                'session_status': row.get('session_status', 'unknown')
            })
    
    # Additional validation: check for missing values
    missing_mask = df_complete[['credibility', 'professionalism']].isnull().any(axis=1)
    if missing_mask.any():
        missing_count = missing_mask.sum()
        df_complete = df_complete.dropna(subset=['credibility', 'professionalism'])
        excluded_rows.extend([
            {'participant_id': pid, 'reason': 'Missing rating values', 'timestamp': ''}
            for pid in df_complete[df_complete.index.isin(df_complete[missing_mask].index)]['participant_id'].unique()
        ])
    
    return df_complete, excluded_rows

def reshape_to_wide(df):
    """
    Reshape data from long to wide format for ANOVA.
    
    Creates one row per participant with columns for each condition's rating.
    """
    # Pivot for credibility
    credibility_wide = df.pivot_table(
        index='participant_id',
        columns='stimulus_id',
        values='credibility',
        aggfunc='mean'
    )
    credibility_wide.columns = [f'cred_{col}' for col in credibility_wide.columns]
    
    # Pivot for professionalism
    professionalism_wide = df.pivot_table(
        index='participant_id',
        columns='stimulus_id',
        values='professionalism',
        aggfunc='mean'
    )
    professionalism_wide.columns = [f'prof_{col}' for col in professionalism_wide.columns]
    
    # Merge demographics (take first occurrence)
    demographics = df.drop_duplicates(subset='participant_id')[['participant_id', 'age', 'education']]
    
    # Combine all
    wide_df = pd.merge(credibility_wide, professionalism_wide, left_index=True, right_index=True)
    wide_df = pd.merge(wide_df, demographics, left_index=True, right_index=True)
    
    # Reset index to make participant_id a column
    wide_df = wide_df.reset_index()
    
    return wide_df

def generate_audit_log(excluded_rows):
    """Generate audit log for excluded participants."""
    return {
        'generated_at': datetime.now().isoformat(),
        'total_excluded': len(excluded_rows),
        'excluded_participants': excluded_rows
    }

def write_outputs(wide_df, audit_log):
    """Write processed outputs to disk."""
    # Ensure processed directory exists
    output_dir = get_cleaned_csv_path().parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write cleaned data
    wide_df.to_csv(get_cleaned_csv_path(), index=False)
    
    # Write audit log
    with open(get_excluded_audit_path(), 'w') as f:
        json.dump(audit_log, f, indent=2)

def main():
    """Main entry point."""
    print("Loading raw data...")
    try:
        df = load_raw_data()
        print(f"Loaded {len(df)} rows.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    
    print("Validating and filtering...")
    df_clean, excluded = validate_and_filter(df)
    print(f"Kept {len(df_clean)} rows, excluded {len(excluded)} rows.")
    
    print("Reshaping to wide format...")
    df_wide = reshape_to_wide(df_clean)
    print(f"Reshaped to {len(df_wide)} participants.")
    
    print("Writing outputs...")
    audit_log = generate_audit_log(excluded)
    write_outputs(df_wide, audit_log)
    
    print(f"Saved cleaned data to: {get_cleaned_csv_path()}")
    print(f"Saved audit log to: {get_excluded_audit_path()}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
