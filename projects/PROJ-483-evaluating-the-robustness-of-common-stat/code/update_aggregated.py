"""
Script to execute T014: Update aggregated results with trend verification.

This script reads results/aggregated.csv (produced by T013), calculates the
Spearman rank correlation to verify monotonic increase of error rates with
dependency strength, and updates the file with a 'trend_status' column.
"""
import os
import sys
from pathlib import Path

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from metrics import update_aggregated_with_trend

def main():
    """Main entry point for the trend verification script."""
    # Define paths relative to project root
    project_root = code_dir.parent
    input_file = project_root / "results" / "aggregated.csv"
    output_file = project_root / "results" / "aggregated.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        print("Please ensure T013 (sensitivity analysis sweep) has been run and produced results/aggregated.csv.")
        sys.exit(1)
    
    print(f"Reading aggregated data from: {input_file}")
    
    try:
        update_aggregated_with_trend(str(input_file), str(output_file))
        print("Trend verification completed successfully.")
    except Exception as e:
        print(f"Error during trend verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()