"""
Script to extract and display bug fix descriptions from Defects4J data.
This script demonstrates the functionality of extract_bug_fix_description.

Usage:
    python code/run_extract_bug_description.py [row_index]

If no row_index is provided, it defaults to 0.
"""
import sys
from pathlib import Path
from data_loader import ensure_data_loaded_and_integrity_recorded, extract_bug_fix_description

def main():
    # Determine row index from arguments
    if len(sys.argv) > 1:
        try:
            row_idx = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid row index '{sys.argv[1]}'. Must be an integer.")
            sys.exit(1)
    else:
        row_idx = 0
    
    print(f"Loading Defects4J data and verifying integrity...")
    try:
        df = ensure_data_loaded_and_integrity_recorded()
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    print(f"Data loaded. Total rows: {len(df)}")
    
    try:
        prompt = extract_bug_fix_description(df, row_idx)
        print(f"\nExtracted Prompt for Row {row_idx}:")
        print("-" * 40)
        print(prompt)
        print("-" * 40)
    except (IndexError, KeyError) as e:
        print(f"Error extracting description: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
