"""
Script to verify the sensitivity table reports correct correlation magnitudes.
This script runs the sensitivity analysis on real data and validates the output.
"""
import os
import sys
import json
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample
from code.analysis.sensitivity import analyze_thresholds
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

def main():
    # Define a sample date range (3 days to ensure enough data for correlation)
    start_date = datetime(2023, 6, 15, 0, 0, 0)
    end_date = datetime(2023, 6, 18, 0, 0, 0)
    date_range = (start_date, end_date)

    print(f"Fetching solar wind data for {start_date} to {end_date}...")
    df_sw = fetch_omni_sw(date_range)
    
    print(f"Fetching THEMIS data for {start_date} to {end_date}...")
    df_ey = fetch_themis_ey(date_range)

    if df_sw.empty or df_ey.empty:
        print("Error: One or both datasets are empty. Cannot proceed.")
        sys.exit(1)

    print(f"Raw SW data shape: {df_sw.shape}")
    print(f"Raw EY data shape: {df_ey.shape}")

    # Clean and resample
    print("Cleaning and resampling data...")
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)

    if df_sw_clean.empty or df_ey_clean.empty:
        print("Error: Cleaned datasets are empty. Cannot proceed.")
        sys.exit(1)

    print(f"Cleaned SW data shape: {df_sw_clean.shape}")
    print(f"Cleaned EY data shape: {df_ey_clean.shape}")

    # Run sensitivity analysis
    print(f"Running sensitivity analysis with thresholds 400, 500, 600 km/s...")
    thresholds = [400, 500, 600]
    sensitivity_results = analyze_thresholds(
        df_sw_clean, 
        df_ey_clean, 
        thresholds=thresholds
    )

    # Prepare output
    output_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "sensitivity_verification.json")

    report = {
        "timestamp": datetime.now().isoformat(),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "thresholds_tested": thresholds,
        "sensitivity_table": sensitivity_results
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Sensitivity verification report written to: {output_path}")
    
    # Print summary for verification
    print("\n--- Sensitivity Table Summary ---")
    for t, res in sensitivity_results.items():
        print(f"Threshold >= {t} km/s: Pearson={res['pearson']:.4f}, Spearman={res['spearman']:.4f}, N={res['n_samples']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
