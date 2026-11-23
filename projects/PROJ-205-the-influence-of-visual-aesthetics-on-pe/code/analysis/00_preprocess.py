"""
Preprocessing script for the Visual Aesthetics Credibility Study.

This script loads raw survey submissions, verifies data integrity via checksums,
cleans the data (type casting, filtering), and exports a clean dataset for analysis.

Output: data/processed/clean_data.csv
"""
import os
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.checksums import verify_checksum, FileChecksumError, get_project_root, get_checksum_store_path
from utils.helpers import get_submissions_csv_path, get_cleaned_csv_path, ensure_data_dirs
from utils.helpers import set_reproducibility_seed
from dotenv import load_dotenv

# Load environment variables for seed
load_dotenv()

def load_raw_data(input_path: str):
    """
    Load raw CSV data from the specified path.
    
    Args:
        input_path (str): Path to the raw submissions CSV.
        
    Returns:
        list[dict]: List of rows as dictionaries.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    if not data:
        raise ValueError("Input file is empty or contains no data rows.")
    
    return data

def validate_and_filter(data: list[dict]) -> list[dict]:
    """
    Validate data types and filter out invalid rows.
    
    Requirements:
    - Cast 'age' to integer.
    - Cast 'education' to string.
    - Cast rating columns to float.
    - Drop rows with missing 'participant_id' or 'stimulus_id'.
    
    Args:
        data (list[dict]): Raw data rows.
        
    Returns:
        list[dict]: Cleaned and validated data rows.
    """
    cleaned_data = []
    invalid_count = 0
    required_columns = ['participant_id', 'stimulus_id', 'age', 'education', 
                        'credibility_rating', 'professionalism_rating']
    
    for row in data:
        # Check required columns exist and are not empty
        if not row.get('participant_id') or not row.get('stimulus_id'):
            invalid_count += 1
            continue
        
        try:
            # Type casting
            # Age must be integer
            age = int(row['age'])
            if age < 0 or age > 120:
                invalid_count += 1
                continue
            
            # Education is string (keep as is)
            education = str(row['education'])
            
            # Ratings must be float
            credibility = float(row['credibility_rating'])
            professionalism = float(row['professionalism_rating'])
            
            # Construct cleaned row
            cleaned_row = {
                'participant_id': row['participant_id'],
                'stimulus_id': row['stimulus_id'],
                'age': age,
                'education': education,
                'timestamp': row.get('timestamp', ''),
                'hashed_ip': row.get('hashed_ip', ''),
                'browser_version': row.get('browser_version', ''),
                'session_start_time': row.get('session_start_time', ''),
                'credibility_rating': credibility,
                'professionalism_rating': professionalism
            }
            cleaned_data.append(cleaned_row)
            
        except (ValueError, TypeError) as e:
            # Skip rows with invalid data types
            invalid_count += 1
            continue
    
    if invalid_count > 0:
        print(f"Warning: {invalid_count} rows were dropped due to invalid data.")
    
    return cleaned_data

def write_outputs(cleaned_data: list[dict], output_path: str):
    """
    Write cleaned data to CSV.
    
    Args:
        cleaned_data (list[dict]): Data to write.
        output_path (str): Path to output CSV.
    """
    if not cleaned_data:
        raise ValueError("No data to write. Output cannot be empty.")
    
    ensure_data_dirs(output_path)
    
    fieldnames = [
        'participant_id', 'stimulus_id', 'age', 'education',
        'timestamp', 'hashed_ip', 'browser_version', 'session_start_time',
        'credibility_rating', 'professionalism_rating'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_data)
    
    print(f"Clean data written to: {output_path}")

def main():
    """Main entry point for preprocessing."""
    parser = argparse.ArgumentParser(description="Preprocess survey data.")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to raw submissions CSV. Defaults to project default.")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to output clean CSV. Defaults to project default.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    
    # Set seed if provided or from env
    seed = args.seed if args.seed is not None else int(os.getenv('RANDOM_SEED', 42))
    set_reproducibility_seed(seed)
    
    # Resolve paths
    input_path = args.input if args.input else str(get_submissions_csv_path())
    output_path = args.output if args.output else str(get_cleaned_csv_path())
    
    # Ensure output directory exists
    ensure_data_dirs(output_path)
    
    print(f"Loading data from {input_path}...")
    
    # 1. Verify Checksum
    # The task requires calling verify_checksum from code/utils/checksums.py
    # We verify the input file against the stored checksum
    try:
        verify_checksum(input_path)
        print("Checksum verification passed.")
    except FileChecksumError as e:
        print(f"ERROR: Checksum verification failed: {e}")
        print("Raw data integrity compromised. Aborting preprocessing.")
        sys.exit(1)
    except FileNotFoundError as e:
        # If checksum file doesn't exist, we might be in a fresh run without checksums yet.
        # However, per T057b, checksums should be saved after T022f.
        # If this is the first run and no checksums exist, we might need to handle gracefully
        # or fail loudly if the spec requires it.
        # Given the strict "fail loudly" constraint on data integrity:
        if os.path.exists(get_checksum_store_path()):
            print(f"ERROR: Checksum file exists but verification failed or input missing: {e}")
            sys.exit(1)
        else:
            # No checksum file found. This implies data was not saved with checksums.
            # This is a violation of T057b/T022f contract.
            print("ERROR: No checksum file found. Raw data integrity cannot be verified.")
            print("This indicates a failure in the data collection pipeline (T057b).")
            sys.exit(1)

    # 2. Load Raw Data
    try:
        raw_data = load_raw_data(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # 3. Validate and Filter
    print("Validating and filtering data...")
    cleaned_data = validate_and_filter(raw_data)
    
    if not cleaned_data:
        print("ERROR: No valid data rows found after cleaning.")
        sys.exit(1)
    
    # 4. Write Output
    print(f"Writing cleaned data to {output_path}...")
    write_outputs(cleaned_data, output_path)
    
    print("Preprocessing complete.")

if __name__ == "__main__":
    main()
