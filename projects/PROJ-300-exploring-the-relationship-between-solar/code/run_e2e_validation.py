"""
End-to-End Validation Script for Solar Wind - Reconnection Rate Analysis.

This script executes the full pipeline on a multi-day interval to ensure
reproducibility and that all required outputs (JSON results, PNG plots)
are generated correctly as per Constitution Principle I.

File path: code/run_e2e_validation.py
"""
import os
import sys
import json
import shutil
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Ensure the project root is in the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.main import run_pipeline
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

def run_e2e_validation():
    """
    Runs the full analysis pipeline on a sample multi-day interval.
    
    1. Defines a 3-day window (e.g., 2024-03-20 to 2024-03-23).
    2. Executes the main pipeline.
    3. Verifies existence of expected artifacts in the `results/` directory.
    4. Prints a summary of the validation.
    """
    # Define a specific multi-day interval for reproducibility
    # Using a period known to have solar activity (March 2024)
    start_date = datetime(2024, 3, 20, 0, 0, 0)
    end_date = datetime(2024, 3, 23, 0, 0, 0)
    
    print(f"Starting E2E Validation for period: {start_date} to {end_date}")
    print(f"Lag Search Window: {LAG_WINDOW_MIN} to {LAG_WINDOW_MAX} minutes (step {LAG_STEP})")
    
    # Define results directory
    results_dir = os.path.join(project_root, "data", "processed", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Execute the pipeline
    try:
        # run_pipeline expects start_date, end_date and returns the report dict
        # It handles data ingestion, cleaning, lag analysis, and plotting
        report = run_pipeline(start_date, end_date)
        
        if report is None:
            print("ERROR: Pipeline returned None. Validation Failed.")
            return False
            
        print("Pipeline execution successful.")
        
    except Exception as e:
        print(f"ERROR: Pipeline execution failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Verification Phase: Check for expected artifacts
    expected_files = [
        "us1_correlation.json",
        "plot_scatter.png",
        "plot_timeseries.png",
        "quality_log.json"
    ]
    
    missing_files = []
    found_files = []
    
    for filename in expected_files:
        filepath = os.path.join(results_dir, filename)
        if os.path.exists(filepath):
            found_files.append(filename)
            # Optional: Check file size to ensure it's not empty
            size = os.path.getsize(filepath)
            if size == 0:
                print(f"WARNING: {filename} exists but is empty.")
        else:
            missing_files.append(filename)
    
    # Print Summary
    print("\n--- E2E Validation Summary ---")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Found Artifacts: {len(found_files)}/{len(expected_files)}")
    
    if missing_files:
        print(f"MISSING ARTIFACTS: {missing_files}")
        print("Validation FAILED.")
        return False
    else:
        print("All expected artifacts generated successfully.")
        
        # Validate JSON content structure
        json_path = os.path.join(results_dir, "us1_correlation.json")
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            required_keys = ["pearson", "spearman", "p_val_permutation", "optimal_lag", "sensitivity_table"]
            missing_keys = [k for k in required_keys if k not in data]
            
            if missing_keys:
                print(f"JSON Structure Incomplete: Missing keys {missing_keys}")
                return False
            
            print(f"JSON Structure Valid. Optimal Lag: {data.get('optimal_lag')} min")
            print(f"Correlation (Pearson): {data.get('pearson'):.4f}")
            print(f"Significance (p < 0.05): {data.get('p_val_permutation', 1.0) < 0.05}")
            
        except Exception as e:
            print(f"Error validating JSON content: {e}")
            return False
        
        print("Validation PASSED.")
        return True

if __name__ == "__main__":
    success = run_e2e_validation()
    sys.exit(0 if success else 1)
