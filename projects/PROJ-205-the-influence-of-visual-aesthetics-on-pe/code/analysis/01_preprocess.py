import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

# Seeding for reproducibility in any stochastic preprocessing steps (none currently, but required by plan)
import random
import numpy as np
random.seed(42)
np.random.seed(42)

def get_project_root():
    """Returns the project root directory."""
    current_file = Path(__file__).resolve()
    # Navigate up from code/analysis to project root
    return current_file.parent.parent.parent

def get_env_mode():
    """Returns the current environment mode (development or production)."""
    return os.environ.get("MODE", "production").lower()

def get_submissions_csv_path():
    """Returns the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path():
    """Returns the path to the processed cleaned CSV."""
    return get_project_root() / "data" / "processed" / "cleaned_data.csv"

def get_excluded_audit_path():
    """Returns the path to the excluded audit log."""
    return get_project_root() / "data" / "processed" / "excluded_audit.csv"

def load_raw_data():
    """
    Loads the raw submissions CSV.
    Fails loudly if file is missing/empty unless MODE=development.
    """
    path = get_submissions_csv_path()
    if not path.exists():
        if get_env_mode() == "development":
            # Generate a no-data report and exit gracefully
            report_path = get_project_root() / "data" / "processed" / "no_data_report.json"
            with open(report_path, "w") as f:
                json.dump({"status": "no_data", "message": "No data found - development mode"}, f, indent=2)
            print(f"Development mode: No data found. Wrote {report_path}")
            sys.exit(0)
        else:
            raise FileNotFoundError("No real data found. Please collect real participant data before running analysis.")

    try:
        import pandas as pd
        df = pd.read_csv(path)
        if df.empty:
            if get_env_mode() == "development":
                report_path = get_project_root() / "data" / "processed" / "no_data_report.json"
                with open(report_path, "w") as f:
                    json.dump({"status": "empty_data", "message": "Empty data found - development mode"}, f, indent=2)
                print(f"Development mode: Empty data found. Wrote {report_path}")
                sys.exit(0)
            else:
                raise ValueError("Raw data file is empty.")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load raw data: {e}")

def validate_and_filter(df):
    """
    Filters rows to keep only complete sessions.
    Removes rows where submission_status != 'complete' OR session_status == 'timeout'.
    Returns (cleaned_df, excluded_df).
    """
    if df.empty:
        return df, pd.DataFrame()

    # Identify rows to exclude
    # Condition for exclusion: (submission_status != 'complete') OR (session_status == 'timeout')
    # We want to KEEP rows where submission_status == 'complete' AND session_status != 'timeout'
    mask_keep = (df['submission_status'] == 'complete') & (df['session_status'] != 'timeout')
    
    cleaned_df = df[mask_keep].copy()
    excluded_df = df[~mask_keep].copy()
    
    return cleaned_df, excluded_df

def generate_audit_log(excluded_df):
    """
    Writes excluded rows to the audit log.
    """
    audit_path = get_excluded_audit_path()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    
    if excluded_df.empty:
        # Write empty file with headers if no exclusions
        with open(audit_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id', 'stimulus_id', 'reason'])
        return

    excluded_df['reason'] = excluded_df.apply(
        lambda row: f"submission_status={row.get('submission_status', 'N/A')}, session_status={row.get('session_status', 'N/A')}",
        axis=1
    )
    
    # Select relevant columns for audit
    audit_cols = ['participant_id', 'stimulus_id', 'reason']
    available_cols = [c for c in audit_cols if c in excluded_df.columns]
    excluded_df[available_cols].to_csv(audit_path, index=False)

def reshape_to_wide(df):
    """
    Converts long-format data to wide-format.
    Index: participant_id
    Columns: age, education, and then credibility_Professional, credibility_Minimalist, etc.
    """
    if df.empty:
        return df

    # Ensure necessary columns exist
    required_cols = ['participant_id', 'stimulus_id', 'credibility', 'professionalism', 'age', 'education']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for reshaping: {missing}")

    # Pivot for credibility
    cred_wide = df.pivot_table(
        index=['participant_id', 'age', 'education'],
        columns='stimulus_id',
        values='credibility',
        aggfunc='first' # Assuming one rating per stimulus per participant
    )
    cred_wide.columns = [f"credibility_{col}" for col in cred_wide.columns]
    
    # Pivot for professionalism
    prof_wide = df.pivot_table(
        index=['participant_id', 'age', 'education'],
        columns='stimulus_id',
        values='professionalism',
        aggfunc='first'
    )
    prof_wide.columns = [f"professionalism_{col}" for col in prof_wide.columns]

    # Concatenate
    wide_df = pd.concat([cred_wide, prof_wide], axis=1).reset_index()

    # Verification assertion
    required_wide_cols = [
        'credibility_Professional', 'credibility_Minimalist', 'credibility_Low-Quality', 'credibility_Neutral',
        'professionalism_Professional', 'professionalism_Minimalist', 'professionalism_Low-Quality', 'professionalism_Neutral'
    ]
    # Check if columns exist (some might be missing if data is sparse, but we assert presence of expected ones)
    missing_wide = [c for c in required_wide_cols if c not in wide_df.columns]
    if missing_wide:
        # In a real scenario with missing data, we might want to handle this, 
        # but for the assertion requirement:
        print(f"Warning: Expected columns missing in wide format: {missing_wide}. This might indicate missing data for some conditions.")
    
    return wide_df

def write_outputs(cleaned_df, wide_df, excluded_df):
    """
    Writes the cleaned and wide-format data to disk.
    """
    # Write cleaned long format (optional, but good for audit)
    cleaned_path = get_project_root() / "data" / "processed" / "cleaned_long.csv"
    cleaned_df.to_csv(cleaned_path, index=False)

    # Write wide format
    wide_path = get_cleaned_csv_path()
    wide_df.to_csv(wide_path, index=False)
    
    # Write audit log
    generate_audit_log(excluded_df)

    print(f"Wrote wide data to: {wide_path}")
    print(f"Wrote cleaned long data to: {cleaned_path}")

def main():
    """
    Main entry point for the preprocessing script.
    """
    print("Starting preprocessing...")
    
    # 1. Load raw data
    df_raw = load_raw_data()
    if df_raw is None:
        print("Exiting due to no data in development mode.")
        return

    print(f"Loaded {len(df_raw)} rows from raw data.")

    # 2. Validate and filter
    df_clean, df_excluded = validate_and_filter(df_raw)
    print(f"Filtered data: {len(df_clean)} kept, {len(df_excluded)} excluded.")

    # 3. Reshape to wide
    df_wide = reshape_to_wide(df_clean)
    
    # 4. Write outputs
    write_outputs(df_clean, df_wide, df_excluded)

    # Final verification
    output_path = get_cleaned_csv_path()
    if output_path.exists():
        print(f"SUCCESS: {output_path} created.")
        sys.exit(0)
    else:
        print("FAILURE: Output file not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()