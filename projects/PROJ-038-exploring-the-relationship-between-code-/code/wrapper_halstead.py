"""
Wrapper script to calculate Halstead Volume for every Java file in the Defects4J dataset.

This script:
1. Reads the list of Java files from a generated list (e.g., from ingest.py).
2. Calls the metrics_halstead module to compute Halstead Volume.
3. Aggregates the results into a CSV or JSON file for downstream processing.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add the code directory to the path so we can import src modules
code_root = Path(__file__).parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.metrics_halstead import calculate_halstead_batch

def load_file_list(file_list_path: str) -> List[str]:
    """
    Load a list of file paths from a text file (one path per line).
    """
    with open(file_list_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def save_results(results: List[Dict[str, Any]], output_path: str, format: str = 'csv'):
    """
    Save the calculation results to a file.
    """
    if format == 'csv':
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if results:
                fieldnames = results[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in results:
                    writer.writerow(row)
    elif format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")

def main():
    parser = argparse.ArgumentParser(description="Calculate Halstead Volume for Java files.")
    parser.add_argument('--input-list', required=True, help="Path to a text file containing Java file paths (one per line).")
    parser.add_argument('--output', required=True, help="Path to the output file (CSV or JSON).")
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help="Output format (default: csv).")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_list):
        print(f"Error: Input file list not found: {args.input_list}")
        sys.exit(1)
        
    print(f"Loading file list from {args.input_list}...")
    file_paths = load_file_list(args.input_list)
    print(f"Loaded {len(file_paths)} files.")
    
    if not file_paths:
        print("No files to process.")
        sys.exit(0)
        
    print("Calculating Halstead Volume...")
    results = calculate_halstead_batch(file_paths)
    
    print(f"Saving results to {args.output}...")
    save_results(results, args.output, args.format)
    
    print("Done.")

if __name__ == "__main__":
    main()