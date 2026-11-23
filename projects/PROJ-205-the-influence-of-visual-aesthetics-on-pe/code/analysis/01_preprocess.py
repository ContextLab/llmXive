import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_env_mode() -> str:
    """Get the environment mode."""
    return os.getenv('MODE', 'development')

def get_submissions_csv_path() -> Path:
    """Return the path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path() -> Path:
    """Return the path to the cleaned data CSV file."""
    return get_project_root() / "data" / "processed" / "cleaned_data.csv"

def get_excluded_audit_path() -> Path:
    """Return the path to the excluded audit log CSV file."""
    return get_project_root() / "data" / "raw" / "excluded_audit.csv"

def load_raw_data() -> list:
    """Load the raw submissions data."""
    path = get_submissions_csv_path()
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    with open(path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def validate_and_filter(data: list) -> tuple:
    """
    Validate and filter the data.
    Returns (cleaned_data, excluded_rows)
    """
    cleaned = []
    excluded = []
    
    required_fields = ['participant_id', 'stimulus_id', 'credibility', 'professionalism', 'age', 'education']
    
    for row in data:
        valid = True
        reason = ""
        
        # Check required fields
        for field in required_fields:
            if field not in row or row[field] is None or row[field] == '':
                valid = False
                reason = f"Missing {field}"
                break
        
        # Check numeric fields
        if valid:
            try:
                int(row['age'])
                int(row['credibility'])
                int(row['professionalism'])
                int(row['education'])
            except ValueError:
                valid = False
                reason = "Invalid numeric value"
        
        if valid:
            cleaned.append(row)
        else:
            row['exclusion_reason'] = reason
            excluded.append(row)
    
    return cleaned, excluded

def generate_audit_log(excluded_rows: list) -> None:
    """Generate an audit log of excluded rows."""
    path = get_excluded_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(excluded_rows[0].keys()) if excluded_rows else []
    
    with open(path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(excluded_rows)

def reshape_to_wide(cleaned_data: list) -> list:
    """
    Reshape the data from long to wide format.
    Each participant becomes a row, with columns for each stimulus rating.
    """
    if not cleaned_data:
        return []
    
    # Group by participant_id
    participants = {}
    for row in cleaned_data:
        pid = row['participant_id']
        if pid not in participants:
            participants[pid] = {
                'age': row['age'],
                'education': row['education'],
                'stimuli': {}
            }
        stim_id = row['stimulus_id']
        participants[pid]['stimuli'][stim_id] = {
            'credibility': row['credibility'],
            'professionalism': row['professionalism']
        }
    
    # Convert to wide format
    wide_data = []
    for pid, data in participants.items():
        row = {
            'participant_id': pid,
            'age': data['age'],
            'education': data['education']
        }
        for stim_id, ratings in data['stimuli'].items():
            row[f"{stim_id}_credibility"] = ratings['credibility']
            row[f"{stim_id}_professionalism"] = ratings['professionalism']
        wide_data.append(row)
    
    return wide_data

def write_outputs(cleaned_data: list, wide_data: list) -> None:
    """Write the cleaned and wide data to CSV files."""
    # Write cleaned data (long format)
    path = get_cleaned_csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if cleaned_data:
        fieldnames = list(cleaned_data[0].keys())
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_data)
    else:
        # Write empty file with headers
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            f.write("participant_id,stimulus_id,credibility,professionalism,timestamp,hashed_ip,age,education,duplicate_flag,session_status,submission_status\n")

def main():
    """Main entry point for the preprocessing script."""
    print("Starting preprocessing...")
    
    try:
        raw_data = load_raw_data()
        print(f"Loaded {len(raw_data)} rows.")
        
        cleaned_data, excluded_data = validate_and_filter(raw_data)
        print(f"Cleaned data: {len(cleaned_data)} rows.")
        print(f"Excluded data: {len(excluded_data)} rows.")
        
        if excluded_data:
            generate_audit_log(excluded_data)
            print(f"Audit log written to {get_excluded_audit_path()}")
        
        wide_data = reshape_to_wide(cleaned_data)
        print(f"Wide data: {len(wide_data)} rows.")
        
        write_outputs(cleaned_data, wide_data)
        print(f"Cleaned data written to {get_cleaned_csv_path()}")
        
        print("Preprocessing complete.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()