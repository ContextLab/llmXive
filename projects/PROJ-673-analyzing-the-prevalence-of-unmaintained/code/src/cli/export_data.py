import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from existing API surface
from src.utils.checksum import generate_checksum, write_checksum_file
from src.models.data_models import Dependency

# Ensure the project root is in the path if running as a script
if __name__ == "__main__" and "code" not in sys.path[0]:
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Load dependency data from a JSON file (output of T016/T017).
    Expects a list of dependency objects with calculated fields.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        # Handle case where data might be wrapped in an object
        if isinstance(data, dict) and 'dependencies' in data:
            return data['dependencies']
        raise ValueError(f"Expected list of dependencies in {input_path}, got {type(data)}")
    
    return data

def export_to_csv(data: List[Dict[str, Any]], output_path: str) -> str:
    """
    Export dependency data to a CSV file at the specified output_path.
    Returns the checksum of the generated file.
    
    Required columns based on T018/T017 requirements:
    - age_in_days (calculated in T017)
    - last_release_date
    - last_commit_date
    - vulnerability_count
    - package_name, version, etc.
    """
    if not data:
        raise ValueError("No data to export")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Define standard columns to ensure consistency
    fieldnames = [
        "package_name", "version", "category",
        "last_release_date", "last_commit_date",
        "age_in_days", "vulnerability_count",
        "is_unmaintained", "source_repo"
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for row in data:
            # Ensure age_in_days is present (it is calculated in T017)
            # If a row lacks age_in_days, it should have been handled in T017,
            # but we ensure it's not None to avoid CSV errors (write empty string if null)
            record = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(record)

    # Generate checksum for the output file
    checksum = generate_checksum(output_file)
    write_checksum_file(output_file, checksum)
    
    return checksum

def main():
    """
    Main entry point for the export script.
    Usage: python code/src/cli/export_data.py --input <input.json> --output <output.csv>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Export dependency data to CSV with checksum.")
    parser.add_argument("--input", required=True, help="Path to input JSON file (processed data)")
    parser.add_argument("--output", required=True, help="Path to output CSV file")
    args = parser.parse_args()

    print(f"Loading data from {args.input}...")
    try:
        data = load_processed_data(args.input)
        print(f"Loaded {len(data)} dependencies.")
    except Exception as e:
        print(f"Error loading data: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Exporting to {args.output}...")
    try:
        checksum = export_to_csv(data, args.output)
        print(f"Successfully exported {len(data)} rows to {args.output}")
        print(f"Checksum: {checksum}")
    except Exception as e:
        print(f"Error exporting data: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
