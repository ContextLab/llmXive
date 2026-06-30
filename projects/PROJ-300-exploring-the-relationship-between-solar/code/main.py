import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import numpy as np

from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample
from data.lag import calculate_physics_lag, apply_lag_shift
from analysis.correlation import calculate_correlation, circular_block_permutation
from analysis.lag_search import find_optimal_lag
from viz.plots import plot_scatter, plot_timeseries
from config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, TAIL_DISTANCE_RE, EARTH_RADIUS_KM

def run_pipeline(
    start_date: str,
    end_date: str,
    output_dir: str = "data/processed",
    results_dir: str = "results"
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline for solar wind speed vs. geomagnetic tail reconnection.
    Implements US-1, US-2, and US-3 requirements including lag calculation and reporting.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # 1. Ingest Data
    print(f"Fetching data for {start_date} to {end_date}...")
    df_sw = fetch_omni_sw((start_date, end_date))
    df_ey = fetch_themis_ey((start_date, end_date))

    if df_sw.empty or df_ey.empty:
        raise ValueError("Ingested data is empty. Check date range and API availability.")

    # 2. Clean and Resample
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)

    # 3. Calculate Physics-based Lag (L_phys)
    # Using mean Vsw from the cleaned dataset
    vsw_mean = df_sw_clean['Vsw'].mean()
    l_phys = calculate_physics_lag(vsw_mean)
    print(f"Calculated Physics Lag (L_phys): {l_phys:.2f} minutes")

    # 4. Find Optimal Lag (L*) via Search Window
    # Sweep LAG_WINDOW_MIN to LAG_WINDOW_MAX
    optimal_lag, lag_correlation = find_optimal_lag(
        df_sw_clean['Vsw'],
        df_ey_clean['Ey'],
        min_lag=LAG_WINDOW_MIN,
        max_lag=LAG_WINDOW_MAX,
        step=LAG_STEP
    )
    print(f"Optimal Lag (L*): {optimal_lag} minutes, Correlation: {lag_correlation:.4f}")

    # 5. Calculate Lag Difference (SC-002)
    # |L* - L_phys|
    lag_difference = abs(optimal_lag - l_phys)
    print(f"Lag Difference |L* - L_phys|: {lag_difference:.2f} minutes")

    # 6. Final Correlation with Optimal Lag
    # Apply the optimal lag shift to Vsw before final correlation
    df_sw_lagged = apply_lag_shift(df_sw_clean, optimal_lag, lag_type='minutes')
    pearson, spearman = calculate_correlation(df_sw_lagged['Vsw'], df_ey_clean['Ey'])

    # 7. Permutation Test for Significance
    p_val_permutation = circular_block_permutation(
        df_sw_lagged['Vsw'].values,
        df_ey_clean['Ey'].values,
        iterations=10000
    )
    significant_flag = p_val_permutation < 0.05

    # 8. Prepare Results Dictionary
    results = {
        "run_timestamp": datetime.now().isoformat(),
        "date_range": {"start": start_date, "end": end_date},
        "physics_lag_minutes": round(l_phys, 2),
        "optimal_lag_minutes": int(optimal_lag),
        "lag_correlation_value": round(lag_correlation, 4),
        "lag_difference_minutes": round(lag_difference, 2),  # SC-002
        "pearson": round(pearson, 4),
        "spearman": round(spearman, 4),
        "p_val_permutation": round(p_val_permutation, 6),
        "significant_flag": significant_flag
    }

    # 9. Write JSON Report
    report_path = os.path.join(results_dir, "us1_correlation.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {report_path}")

    # 10. Generate Plots (US-3)
    plot_scatter(df_sw_lagged['Vsw'], df_ey_clean['Ey'], optimal_lag, output_path=os.path.join(results_dir, "plot_scatter.png"))
    plot_timeseries(df_sw_lagged, df_ey_clean, optimal_lag, output_path=os.path.join(results_dir, "plot_timeseries.png"))

    return results

if __name__ == "__main__":
    # Default sample range for testing if no args provided
    start = "2023-01-01"
    end = "2023-01-02"
    if len(sys.argv) >= 3:
        start = sys.argv[1]
        end = sys.argv[2]

    run_pipeline(start, end)
