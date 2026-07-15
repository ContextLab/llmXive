"""
Sample runner for User Story 3 (Visualization and Sensitivity).
This script demonstrates the integration of sensitivity analysis and plotting.
File: code/run_us3_sample.py
"""
import os
import sys
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from viz.plots import plot_scatter, plot_timeseries
from analysis.sensitivity import run_sensitivity_sweep
from data.clean import clean_and_resample
from data.lag import calculate_physics_lag, apply_lag_shift
from analysis.lag_search import find_optimal_lag
from analysis.correlation import calculate_correlation


def generate_synthetic_data_for_demo():
    """
    Generate synthetic data for demonstration purposes only.
    In a real run, this would be replaced by fetch_omni_sw and fetch_themis_ey.
    """
    np.random.seed(42)
    n = 1000
    start = datetime(2023, 1, 1)
    timestamps = [start + timedelta(minutes=i*5) for i in range(n)]
    
    # Create correlated data with a known lag
    true_lag = 45
    vsw = np.random.uniform(300, 800, n)
    # Ey is Vsw shifted by true_lag steps (45 min = 9 steps of 5 min) + noise
    shift_idx = true_lag // 5
    ey = 0.02 * np.roll(vsw, -shift_idx) + np.random.normal(0, 0.5, n)
    
    df_vsw = pd.DataFrame({'timestamp': timestamps, 'Vsw': vsw})
    df_ey = pd.DataFrame({'timestamp': timestamps, 'Ey': ey})
    
    return df_vsw, df_ey


def main():
    """
    Execute the US3 sample pipeline:
    1. Load/Clean data
    2. Run sensitivity analysis
    3. Generate plots with optimal lag annotation
    4. Save results to data/processed/
    """
    print("Starting US3 Sample Run...")
    
    # 1. Load Data (Using synthetic for demo, replace with real fetch in production)
    # df_vsw, df_ey = fetch_omni_sw(...), fetch_themis_ey(...)
    df_vsw, df_ey = generate_synthetic_data_for_demo()
    
    # 2. Clean and Resample
    df_vsw_clean, df_ey_clean = clean_and_resample(df_vsw, df_ey)
    
    # 3. Find Optimal Lag (for plotting annotation)
    optimal_lag, corr_val, _ = find_optimal_lag(
        df_vsw_clean['Vsw'], 
        df_vsw_clean['Ey'] if 'Ey' in df_vsw_clean.columns else df_ey_clean['Ey'],
        lag_window_min=30,
        lag_window_max=90,
        lag_step=5
    )
    # Fix column mismatch if necessary (assuming clean_and_resample aligns them)
    # For this demo, we assume clean_and_resample merges them or we merge manually
    if 'Ey' not in df_vsw_clean.columns:
        merged = pd.merge(df_vsw_clean, df_ey_clean, on='timestamp')
        vsw_col = merged['Vsw']
        ey_col = merged['Ey']
    else:
        merged = df_vsw_clean
        vsw_col = merged['Vsw']
        ey_col = merged['Ey']

    optimal_lag, corr_val, _ = find_optimal_lag(vsw_col, ey_col)
    print(f"Optimal Lag Found: {optimal_lag} min")

    # 4. Sensitivity Analysis
    print("Running Sensitivity Analysis...")
    sensitivity_df = run_sensitivity_sweep(merged)
    print(sensitivity_df)
    
    # Save sensitivity table to JSON
    results_dir = "data/processed"
    os.makedirs(results_dir, exist_ok=True)
    output_json = os.path.join(results_dir, "us3_sensitivity.json")
    with open(output_json, 'w') as f:
        # Convert numpy types for JSON serialization
        json_records = sensitivity_df.replace([np.nan], [None]).to_dict(orient='records')
        json.dump(json_records, f, indent=2)
    print(f"Sensitivity table saved to {output_json}")

    # 5. Generate Plots
    print("Generating Plots...")
    
    # Scatter Plot
    scatter_path = os.path.join(results_dir, "plot_scatter.png")
    plot_scatter(merged, optimal_lag=optimal_lag, output_path=scatter_path)
    print(f"Scatter plot saved to {scatter_path}")
    
    # Time Series Plot
    ts_path = os.path.join(results_dir, "plot_timeseries.png")
    plot_timeseries(merged[['timestamp', 'Vsw']], merged[['timestamp', 'Ey']], 
                    optimal_lag=optimal_lag, output_path=ts_path)
    print(f"Time series plot saved to {ts_path}")
    
    print("US3 Sample Run Complete.")


if __name__ == "__main__":
    main()
