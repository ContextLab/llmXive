import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
import hashlib

def get_project_root():
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_submissions_csv_path():
    """Returns the path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path():
    """Returns the path to the cleaned CSV file."""
    return get_project_root() / "data" / "processed" / "cleaned_submissions.csv"

def get_excluded_audit_path():
    """Returns the path to the excluded audit log file."""
    return get_project_root() / "data" / "processed" / "excluded_audit.csv"

def load_raw_data(input_path):
    """Loads raw data from the specified CSV file."""
    try:
        with open(input_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_path}")

def validate_and_filter(data):
    """Validates and filters the raw data."""
    validated_data = []
    for row in data:
        # Add validation logic here. For example, check if required fields are present.
        if all(key in row for key in ['participant_id', 'age', 'education', 'timestamp', 'hashed_ip']):
            validated_data.append(row)
        else:
            print(f"Skipping invalid row: {row}")  # Log invalid rows
    return validated_data

def reshape_to_wide_data(data):
    """Reshapes the data to a wide format (if needed)."""
    # Implement data reshaping logic here.
    return data

def generate_audit_log(excluded_rows, output_path):
    """Generates an audit log of excluded rows."""
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['reason', 'row']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in excluded_rows:
            writer.writerow({'reason': 'Invalid data', 'row': row})

def compute_sha256(filepath):
    """Computes the SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_data_checksum(filepath, expected_checksum):
    """Verifies the checksum of a file."""
    actual_checksum = compute_sha256(filepath)
    if actual_checksum != expected_checksum:
        raise ValueError(f"Checksum mismatch for {filepath}. Expected {expected_checksum}, got {actual_checksum}")

def write_outputs(data, cleaned_csv_path, excluded_audit_path):
    """Writes the processed data to output files."""
    with open(cleaned_csv_path, 'w', newline='') as csvfile:
        fieldnames = data[0].keys() if data else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main function to preprocess the data."""
    try:
        input_path = get_submissions_csv_path()
        raw_data = load_raw_data(input_path)
        validated_data = validate_and_filter(raw_data)
        wide_data = reshape_to_wide_data(validated_data)
        
        cleaned_csv_path = get_cleaned_csv_path()
        excluded_audit_path = get_excluded_audit_path()
        
        write_outputs(wide_data, cleaned_csv_path, excluded_audit_path)

        # Verify checksum after writing
        expected_checksum = "some_checksum_value" # Replace with actual expected checksum from checksums.py
        verify_data_checksum(cleaned_csv_path, expected_checksum)

        print("Data preprocessing completed successfully.")
    except Exception as e:
        print(f"Error during data preprocessing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()