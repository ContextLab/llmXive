import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import existing utilities from the project
from src.utils.checksum import generate_checksum, write_checksum_file
from src.models.data_models import Dependency

# Ensure the project root is in the path if running as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def load_processed_data(json_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load the processed dependencies data from a JSON file.
    Defaults to data/processed/dependencies_processed.json if no path is provided.
    """
    if json_path is None:
        json_path = str(DATA_PROCESSED_DIR / "dependencies_processed.json")
    
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def fetch_real_sample_data() -> List[Dict[str, Any]]:
    """
    This function is a placeholder if real data needs to be fetched from an external source
    that hasn't been processed yet. However, T018 depends on T017 which produces the 
    processed data. Therefore, we primarily load from the processed file.
    
    If the processed file is missing, we raise an error to fail loudly rather than 
    fabricating data.
    """
    return load_processed_data()

def export_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export the list of dependency dictionaries to a CSV file.
    Handles nested structures by flattening or converting to JSON strings where appropriate.
    Specifically ensures `age_in_days` and `vulnerability_count` are present.
    """
    if not data:
        raise ValueError("No data to export. The dataset is empty.")
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine fieldnames from the first record, handling potential None values or nested dicts
    # We expect specific columns based on T017 requirements
    fieldnames = [
        'package_name', 
        'version', 
        'dependency_name', 
        'dependency_version',
        'last_release_date',
        'last_commit_date',
        'age_in_days',
        'vulnerability_count',
        'is_unmaintained',
        'category'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for row in data:
            # Ensure age_in_days is formatted correctly (null if missing)
            age = row.get('age_in_days')
            if age is None:
                row['age_in_days'] = '' # CSV empty string for null
            else:
                row['age_in_days'] = str(age)
            
            # Ensure vulnerability_count is present (0 if missing)
            if 'vulnerability_count' not in row:
                row['vulnerability_count'] = 0
            
            # Handle dates - convert to string if datetime object
            for date_key in ['last_release_date', 'last_commit_date']:
                val = row.get(date_key)
                if isinstance(val, datetime):
                    row[date_key] = val.isoformat()
                elif val is None:
                    row[date_key] = ''
            
            writer.writerow(row)

def main():
    """
    Main entry point for T018: Data Export.
    1. Loads processed data (from T017).
    2. Exports to data/processed/dependencies_raw.csv.
    3. Generates a checksum for the CSV file.
    """
    input_file = DATA_PROCESSED_DIR / "dependencies_processed.json"
    output_file = DATA_PROCESSED_DIR / "dependencies_raw.csv"
    checksum_file = DATA_PROCESSED_DIR / "dependencies_raw.csv.sha256"

    print(f"Loading processed data from {input_file}...")
    try:
        data = load_processed_data(str(input_file))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure T017 has been run successfully and dependencies_processed.json exists.")
        sys.exit(1)
    
    print(f"Exporting {len(data)} records to {output_file}...")
    try:
        export_to_csv(data, str(output_file))
    except Exception as e:
        print(f"ERROR during CSV export: {e}")
        sys.exit(1)
    
    print("Generating checksum...")
    try:
        checksum = generate_checksum(output_file)
        write_checksum_file(output_file, checksum)
        print(f"Checksum written to {checksum_file}")
        print(f"SHA256: {checksum}")
    except Exception as e:
        print(f"ERROR during checksum generation: {e}")
        sys.exit(1)
    
    print(f"SUCCESS: Data exported to {output_file}")

if __name__ == "__main__":
    main()
