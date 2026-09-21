"""
Preprocessing Script for Visual Aesthetics Study.

This script loads the raw submissions CSV, filters for complete sessions,
handles missing data, and reshapes the data into a wide format suitable
for Repeated-Measures ANOVA.

Output: data/processed/cleaned_data.csv
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
    current = Path(__file__).resolve()
    while current.name != "PROJ-205-the-influence-of-visual-aesthetics-on-pe":
        current = current.parent
        if current == current.parent:
            raise RuntimeError("Could not find project root")
    return current

PROJECT_ROOT = get_project_root()

def get_submissions_csv_path():
    return PROJECT_ROOT / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path():
    return PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"

def get_excluded_audit_path():
    return PROJECT_ROOT / "data" / "processed" / "excluded_audit.json"

def load_raw_data():
    path = get_submissions_csv_path()
    if not path.exists():
        raise FileNotFoundError(f"Raw submissions file not found: {path}")
    return pd.read_csv(path)

def validate_and_filter(df):
    """
    Filter the dataframe to keep only complete sessions.
    A complete session has ratings for all 4 stimuli.
    """
    # Identify rating columns (assuming columns like 'credibility_Professional', etc.)
    # We look for columns containing 'credibility' or 'professionalism'
    rating_cols = [col for col in df.columns if 'credibility' in col.lower() or 'professionalism' in col.lower()]
    
    if not rating_cols:
        # Fallback: look for generic rating columns if naming convention differs
        rating_cols = [col for col in df.columns if col.startswith('cred') or col.startswith('prof')]
    
    # Count non-null ratings per participant
    # Assuming one row per participant-stimulus, we need to pivot or group
    # The raw data is likely in long format: one row per stimulus rating
    # We need to check if a participant_id has 4 rows with valid ratings.
    
    if 'participant_id' not in df.columns:
        raise ValueError("Raw data must contain 'participant_id' column.")
    
    # Group by participant and count non-null ratings
    # We assume each participant has multiple rows (one per stimulus)
    participant_counts = df.groupby('participant_id')[rating_cols].count().min(axis=1)
    
    # Filter participants with exactly 4 ratings (assuming 4 stimuli)
    complete_participants = participant_counts[participant_counts == 4].index
    
    # Filter the original dataframe
    df_complete = df[df['participant_id'].isin(complete_participants)].copy()
    
    # Drop rows with any NaN in rating columns
    df_complete = df_complete.dropna(subset=rating_cols)
    
    return df_complete, complete_participants

def reshape_to_wide(df_complete):
    """
    Reshape the long-format data to wide format.
    Columns will be: participant_id, age, education, credibility_[Stimulus], professionalism_[Stimulus]
    """
    # Ensure we have the necessary columns
    required_cols = ['participant_id', 'age', 'education']
    if not all(col in df_complete.columns for col in required_cols):
        # Try to infer demographics if columns are named differently
        # For now, assume standard naming
        pass
    
    # Pivot the data
    # We need to pivot for credibility and professionalism separately or together
    # Let's pivot to have columns like: credibility_Professional, credibility_Minimalist, etc.
    
    # Identify the stimulus condition column
    stimulus_col = 'stimulus_id' if 'stimulus_id' in df_complete.columns else 'condition'
    if stimulus_col not in df_complete.columns:
        # Try to infer from column names
        stimulus_candidates = [c for c in df_complete.columns if 'stimulus' in c.lower() or 'condition' in c.lower()]
        if stimulus_candidates:
            stimulus_col = stimulus_candidates[0]
        else:
            raise ValueError("Could not identify stimulus condition column.")
    
    # Pivot credibility
    cred_cols = [c for c in df_complete.columns if 'credibility' in c.lower()]
    if cred_cols:
        cred_col = cred_cols[0]
        df_cred_wide = df_complete.pivot_table(
            index=['participant_id', 'age', 'education'],
            columns=stimulus_col,
            values=cred_col,
            aggfunc='first' # Should be unique
        ).reset_index()
        # Flatten column names
        df_cred_wide.columns.name = None
        df_cred_wide.columns = ['participant_id', 'age', 'education'] + [f"credibility_{str(col)}" for col in df_cred_wide.columns[3:]]
    else:
        df_cred_wide = df_complete[['participant_id', 'age', 'education']].drop_duplicates()
    
    # Pivot professionalism
    prof_cols = [c for c in df_complete.columns if 'professionalism' in c.lower()]
    if prof_cols:
        prof_col = prof_cols[0]
        df_prof_wide = df_complete.pivot_table(
            index=['participant_id', 'age', 'education'],
            columns=stimulus_col,
            values=prof_col,
            aggfunc='first'
        ).reset_index()
        df_prof_wide.columns.name = None
        df_prof_wide.columns = ['participant_id', 'age', 'education'] + [f"professionalism_{str(col)}" for col in df_prof_wide.columns[3:]]
    else:
        df_prof_wide = df_complete[['participant_id', 'age', 'education']].drop_duplicates()
    
    # Merge credibility and professionalism on participant_id
    df_wide = pd.merge(df_cred_wide, df_prof_wide, on=['participant_id', 'age', 'education'], how='outer')
    
    # Sort columns for readability
    # Put participant_id, age, education first
    base_cols = ['participant_id', 'age', 'education']
    other_cols = [c for c in df_wide.columns if c not in base_cols]
    df_wide = df_wide[base_cols + other_cols]
    
    return df_wide

def generate_audit_log(excluded_participants, total_participants):
    """
    Generate a JSON log of excluded participants and reasons.
    """
    audit = {
        "timestamp": datetime.now().isoformat(),
        "total_raw_participants": total_participants,
        "included_participants": len(excluded_participants), # Actually included count
        "excluded_count": total_participants - len(excluded_participants),
        "exclusion_reasons": {
            "incomplete_ratings": total_participants - len(excluded_participants)
        }
    }
    return audit

def write_outputs(df_wide, audit_log):
    """
    Write the cleaned wide data and audit log to disk.
    """
    output_csv = get_cleaned_csv_path()
    output_json = get_excluded_audit_path()
    
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    df_wide.to_csv(output_csv, index=False)
    print(f"Cleaned data saved to {output_csv}")
    
    with open(output_json, 'w') as f:
        json.dump(audit_log, f, indent=2)
    print(f"Audit log saved to {output_json}")

def main():
    print("Starting preprocessing...")
    
    try:
        df_raw = load_raw_data()
        print(f"Loaded {len(df_raw)} rows from raw data.")
        
        total_participants = df_raw['participant_id'].nunique()
        print(f"Total unique participants: {total_participants}")
        
        df_complete, included_ids = validate_and_filter(df_raw)
        print(f"Filtered to {len(df_complete)} rows for {len(included_ids)} complete participants.")
        
        df_wide = reshape_to_wide(df_complete)
        print(f"Reshaped to wide format with {len(df_wide)} participants.")
        
        audit_log = generate_audit_log(included_ids, total_participants)
        
        write_outputs(df_wide, audit_log)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during preprocessing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
