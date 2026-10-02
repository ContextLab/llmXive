import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
import hashlib

# Import checksum logic from T057 (code/utils/checksums.py)
# We import the specific functions to verify the file integrity before processing.
try:
    from utils.checksums import verify_submissions_integrity, compute_sha256
except ImportError:
    # Fallback for direct execution without package structure if needed, 
    # though the project structure implies utils is importable.
    # If running as script, we adjust path.
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from utils.checksums import verify_submissions_integrity, compute_sha256


class FileChecksumError(Exception):
    """Raised when data integrity verification fails."""
    pass

class FileNotFoundError(Exception):
    """Raised when the required input file is missing."""
    pass

def get_project_root():
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_submissions_csv_path():
    """Returns the path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path():
    """Returns the path to the cleaned CSV file."""
    # Task T024a specifies output: data/processed/clean_data.csv
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def get_excluded_audit_path():
    """Returns the path to the excluded audit log file."""
    return get_project_root() / "data" / "processed" / "excluded_audit.csv"

def load_raw_data(input_path):
    """Loads raw data from the specified CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)
        return data
    except Exception as e:
        raise FileNotFoundError(f"Error reading input file {input_path}: {e}")

def validate_and_filter(data):
    """Validates and filters the raw data based on required schema fields."""
    # Required fields based on T022f and T069 schema
    required_fields = [
        'participant_id', 'age', 'education', 'timestamp', 
        'hashed_ip', 'browser_version', 'session_duration'
    ]
    
    validated_data = []
    excluded_rows = []

    for row in data:
        # Check if all required keys exist
        missing_keys = [k for k in required_fields if k not in row]
        
        if missing_keys:
            excluded_rows.append({
                'reason': f"Missing fields: {', '.join(missing_keys)}",
                'row_data': json.dumps(row)
            })
            continue

        # Basic type validation (age must be numeric)
        try:
            int(row['age'])
        except ValueError:
            excluded_rows.append({
                'reason': "Invalid age (non-numeric)",
                'row_data': json.dumps(row)
            })
            continue

        validated_data.append(row)

    return validated_data, excluded_rows

def reshape_to_wide_data(data):
    """
    Reshapes the data from long format (one row per stimulus rating) to wide format.
    Expected input: List of dicts where each row has stimulus_id and rating columns.
    Output: List of dicts where columns are participant_id, condition_1_credibility, etc.
    """
    if not data:
        return []

    # Group by participant_id
    participants = {}
    for row in data:
        pid = row['participant_id']
        if pid not in participants:
            participants[pid] = {
                'participant_id': pid,
                'age': row['age'],
                'education': row['education'],
                'timestamp': row['timestamp'],
                'hashed_ip': row['hashed_ip'],
                'browser_version': row['browser_version'],
                'session_duration': row['session_duration'],
                'ratings': {}
            }
        
        # Expecting columns: stimulus_id, credibility_rating, professionalism_rating
        if 'stimulus_id' in row and 'credibility_rating' in row:
            stim_id = row['stimulus_id']
            participants[pid]['ratings'][stim_id] = {
                'credibility': row['credibility_rating'],
                'professionalism': row.get('professionalism_rating', '')
            }

    # Flatten to wide format
    wide_data = []
    for pid, p_data in participants.items():
        wide_row = {
            'participant_id': p_data['participant_id'],
            'age': p_data['age'],
            'education': p_data['education'],
            'timestamp': p_data['timestamp'],
            'hashed_ip': p_data['hashed_ip'],
            'browser_version': p_data['browser_version'],
            'session_duration': p_data['session_duration']
        }
        
        # Sort stimulus IDs to ensure consistent column order
        sorted_stims = sorted(p_data['ratings'].keys())
        for stim in sorted_stims:
            r = p_data['ratings'][stim]
            wide_row[f"{stim}_credibility"] = r['credibility']
            wide_row[f"{stim}_professionalism"] = r['professionalism']
            # We also need the condition (aesthetic type) for ANOVA
            # Assuming stimulus_id maps to condition or we extract it from ID naming
            # For now, we assume stimulus_id IS the condition or contains it.
            # If stimulus_id is "professional", "minimalist", etc., we use that.
            wide_row[f"{stim}_condition"] = stim 

        wide_data.append(wide_row)

    return wide_data

def generate_audit_log(excluded_rows, output_path):
    """Generates an audit log of excluded rows."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['reason', 'row_data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in excluded_rows:
            writer.writerow(row)

def write_outputs(data, cleaned_csv_path, excluded_audit_path):
    """Writes the processed data to output files."""
    os.makedirs(os.path.dirname(cleaned_csv_path), exist_ok=True)
    
    with open(cleaned_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        if not data:
            # Write empty file with headers if possible, or just empty
            # We don't have headers if data is empty, so we skip writing or write generic?
            # Better to write headers if we know them, but here we infer from first row
            pass
        else:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

def main():
    """Main function to preprocess the data."""
    try:
        input_path = get_submissions_csv_path()
        
        # 1. Check if file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # 2. Verify Data Integrity (Checksum) using T057 logic
        # This function raises an error if checksum mismatches or file is missing
        try:
            verify_submissions_integrity(input_path)
            print(f"Checksum verification passed for {input_path}")
        except Exception as e:
            # Wrap in our specific error type for clarity
            raise FileChecksumError(f"Data integrity check failed: {e}")

        # 3. Load Raw Data
        raw_data = load_raw_data(input_path)
        print(f"Loaded {len(raw_data)} rows from {input_path}")

        # 4. Validate and Filter
        validated_data, excluded_rows = validate_and_filter(raw_data)
        print(f"Validated {len(validated_data)} rows, excluded {len(excluded_rows)}")

        # 5. Reshape to Wide Data (for ANOVA)
        wide_data = reshape_to_wide_data(validated_data)
        print(f"Reshaped to {len(wide_data)} participants in wide format")

        # 6. Write Outputs
        cleaned_csv_path = get_cleaned_csv_path()
        excluded_audit_path = get_excluded_audit_path()
        
        write_outputs(wide_data, cleaned_csv_path, excluded_audit_path)
        generate_audit_log(excluded_rows, excluded_audit_path)

        # 7. Compute and Store Checksum for the NEW clean file (optional but good practice)
        # The task T024a specifically asks to verify input checksum. 
        # We do not strictly need to store the output checksum unless required by downstream,
        # but T024b mentions verifying output checksum. Let's ensure the file exists.
        
        if not os.path.exists(cleaned_csv_path):
            raise FileNotFoundError(f"Output file was not created: {cleaned_csv_path}")

        print(f"Preprocessing complete. Output: {cleaned_csv_path}")
        print(f"Audit log: {excluded_audit_path}")

    except FileChecksumError as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during data preprocessing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()