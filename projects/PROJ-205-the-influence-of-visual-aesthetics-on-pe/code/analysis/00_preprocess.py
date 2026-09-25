"""
Preprocessing script for PROJ-205.
Loads raw submissions, filters for complete sessions, and reshapes to wide format.
"""
import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to path for imports
def get_project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_submissions_csv_path():
    """Get path to raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path():
    """Get path to processed cleaned CSV."""
    return get_project_root() / "data" / "processed" / "cleaned_data.csv"

def get_excluded_audit_path():
    """Get path to excluded rows audit log."""
    return get_project_root() / "data" / "processed" / "excluded_audit.csv"

def load_raw_data(chunksize: int = 1000):
    """
    Load raw data using chunked reading to handle large datasets.
    Returns a generator or concatenated dataframe depending on size.
    """
    input_path = get_submissions_csv_path()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Use chunked reading for memory efficiency
    chunks = []
    total_rows = 0
    for chunk in pd.read_csv(input_path, chunksize=chunksize):
        chunks.append(chunk)
        total_rows += len(chunk)

    if not chunks:
        raise ValueError("No data found in input file")

    df = pd.concat(chunks, ignore_index=True)
    print(f"Loaded {total_rows} rows from {input_path}")
    return df

def validate_and_filter(df):
    """
    Filter for complete sessions.
    A complete session has exactly 8 ratings (4 stimuli * 2 scales).
    Returns filtered dataframe and audit data for excluded rows.
    """
    # Define expected stimuli and scales
    expected_stimuli = ['Professional', 'Minimalist', 'Low-Quality', 'Neutral']
    # Each participant should have 2 ratings per stimulus (credibility, professionalism)
    # Total expected rows per participant = 8

    audit_data = []
    valid_participants = []
    invalid_participants = []

    # Group by participant_id
    grouped = df.groupby('participant_id')

    for pid, group in grouped:
        # Count unique stimuli rated
        unique_stimuli = group['stimulus_id'].unique()
        rating_count = len(group)

        # Check if all 4 stimuli are present
        has_all_stimuli = set(unique_stimuli) == set(expected_stimuli)
        has_correct_count = rating_count == 8

        if has_all_stimuli and has_correct_count:
            valid_participants.append(pid)
        else:
            invalid_participants.append({
                'participant_id': pid,
                'reason': 'Incomplete session',
                'stimuli_count': len(unique_stimuli),
                'total_ratings': rating_count,
                'expected_stimuli': len(expected_stimuli),
                'expected_ratings': 8
            })

    # Filter dataframe to only valid participants
    filtered_df = df[df['participant_id'].isin(valid_participants)].reset_index(drop=True)
    print(f"Filtered: {len(valid_participants)} complete sessions, {len(invalid_participants)} excluded")

    return filtered_df, invalid_participants

def reshape_to_wide(df):
    """
    Reshape dataframe from long to wide format for ANOVA.
    Each row is a participant, columns are condition-specific ratings.
    """
    if df.empty:
        raise ValueError("Cannot reshape empty dataframe")

    # Ensure we have the right columns
    required_cols = ['participant_id', 'stimulus_id', 'credibility', 'professionalism']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Create wide format for credibility
    credibility_wide = df.pivot_table(
        index='participant_id',
        columns='stimulus_id',
        values='credibility',
        aggfunc='mean'  # Should be unique, but mean handles duplicates safely
    )
    credibility_wide.columns = [f"cred_{col}" for col in credibility_wide.columns]

    # Create wide format for professionalism
    professionalism_wide = df.pivot_table(
        index='participant_id',
        columns='stimulus_id',
        values='professionalism',
        aggfunc='mean'
    )
    professionalism_wide.columns = [f"prof_{col}" for col in professionalism_wide.columns]

    # Combine and reset index
    wide_df = pd.concat([credibility_wide, professionalism_wide], axis=1).reset_index()

    # Ensure all expected columns exist (in case of missing data in some conditions)
    expected_cred = [f"cred_{s}" for s in ['Professional', 'Minimalist', 'Low-Quality', 'Neutral']]
    expected_prof = [f"prof_{s}" for s in ['Professional', 'Minimalist', 'Low-Quality', 'Neutral']]

    for col in expected_cred + expected_prof:
        if col not in wide_df.columns:
            wide_df[col] = np.nan

    # Reorder columns for clarity
    final_cols = ['participant_id'] + expected_cred + expected_prof
    wide_df = wide_df[final_cols]

    # Drop any rows with NaN (incomplete data after pivot)
    wide_df = wide_df.dropna().reset_index(drop=True)

    print(f"Reshaped to wide format: {len(wide_df)} participants")
    return wide_df

def generate_audit_log(invalid_participants):
    """Generate audit log for excluded rows."""
    if not invalid_participants:
        return None

    audit_df = pd.DataFrame(invalid_participants)
    return audit_df

def write_outputs(wide_df, audit_df):
    """Write cleaned data and audit log to disk."""
    # Ensure processed directory exists
    output_path = get_cleaned_csv_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wide_df.to_csv(output_path, index=False)
    print(f"Wrote cleaned data to {output_path}")

    if audit_df is not None:
        audit_path = get_excluded_audit_path()
        audit_df.to_csv(audit_path, index=False)
        print(f"Wrote audit log to {audit_path}")

def main():
    """Main execution function."""
    print("Starting preprocessing...")

    # Load raw data
    try:
        raw_df = load_raw_data()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Validate and filter
    filtered_df, invalid_participants = validate_and_filter(raw_df)

    if filtered_df.empty:
        print("ERROR: No complete sessions found in data.")
        # Still generate audit log
        audit_df = generate_audit_log(invalid_participants)
        if audit_df is not None:
            output_path = get_excluded_audit_path()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            audit_df.to_csv(output_path, index=False)
        sys.exit(1)

    # Reshape to wide
    try:
        wide_df = reshape_to_wide(filtered_df)
    except Exception as e:
        print(f"ERROR during reshaping: {e}")
        sys.exit(1)

    if wide_df.empty:
        print("ERROR: Reshaped dataframe is empty.")
        sys.exit(1)

    # Write outputs
    audit_df = generate_audit_log(invalid_participants)
    write_outputs(wide_df, audit_df)

    print("Preprocessing complete.")

if __name__ == "__main__":
    main()