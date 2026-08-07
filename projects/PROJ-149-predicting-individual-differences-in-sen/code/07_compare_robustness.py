"""
T027: Compare R² stability and report percentage difference in alpha power means (FR-008).

This script consumes:
1. data/processed/model_results.json (from T017, primary 4s window with ICA)
2. data/processed/robustness_report.csv (from T026, 2s window without ICA)

It produces:
1. data/processed/robustness_comparison.json (R² stability metrics)
2. Updates data/processed/robustness_report.csv to include the alpha power difference
"""
import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, get_seed

def load_model_results():
    """Load the primary model results."""
    path = get_path("model_results")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Primary model results not found at {path}. "
                                "Ensure T017 has completed successfully.")
    with open(path, 'r') as f:
        return json.load(f)

def load_robustness_data():
    """Load the robustness analysis report."""
    path = get_path("robustness_report")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Robustness report not found at {path}. "
                                "Ensure T026 has completed successfully.")
    return pd.read_csv(path)

def calculate_r2_stability(primary_results, robustness_df):
    """
    Compare R² values between primary and robustness models.
    
    Returns a dict with stability metrics.
    """
    primary_r2 = primary_results.get("adjusted_r2")
    if primary_r2 is None:
        # Fallback to raw r2 if adjusted is missing
        primary_r2 = primary_results.get("r2")
    
    if primary_r2 is None:
        raise ValueError("Primary model results missing both 'r2' and 'adjusted_r2'.")

    # Extract robustness R² (assuming T026 produced a row with model R²)
    # T026 should have run the modeling pipeline on 2s/no-ICA data and saved R²
    # We look for the 'r2' or 'adjusted_r2' column in the robustness report
    robust_r2 = None
    if 'adjusted_r2' in robustness_df.columns:
        robust_r2 = robustness_df['adjusted_r2'].iloc[0]
    elif 'r2' in robustness_df.columns:
        robust_r2 = robustness_df['r2'].iloc[0]
    
    if robust_r2 is None:
        # If T026 didn't save R² directly, we might need to infer or fail
        # For this task, we assume T026 saved the R² of the 2s/no-ICA run
        raise ValueError("Robustness report does not contain R² or adjusted_R². "
                         "Ensure T026 saves model metrics to the report.")

    # Calculate percentage difference in R²
    # Formula: |Primary - Robust| / |Primary| * 100
    if primary_r2 == 0:
        pct_diff_r2 = float('inf') if robust_r2 != 0 else 0.0
    else:
        pct_diff_r2 = abs(primary_r2 - robust_r2) / abs(primary_r2) * 100

    return {
        "primary_r2": primary_r2,
        "robustness_r2": robust_r2,
        "r2_difference": primary_r2 - robust_r2,
        "r2_percentage_difference": pct_diff_r2,
        "stability_status": "stable" if pct_diff_r2 < 20 else "unstable" # Threshold heuristic
    }

def calculate_alpha_power_difference(robustness_df, primary_features_path=None):
    """
    Calculate percentage difference in mean alpha power between primary and robustness pipelines.
    
    Since T026 re-runs the feature extraction, we need to compare the mean alpha power
    of the robustness features against the primary features.
    
    If primary_features_path is not provided, we assume the robustness_df contains
    the necessary mean values or we calculate from raw data (which is expensive).
    
    However, FR-008 asks for "percentage difference in alpha power means".
    A pragmatic approach for T027:
    1. If T026 saved mean alpha power in robustness_report.csv, use that.
    2. If not, we must load the primary features (data/processed/features.csv) 
       and re-calculate means from the robustness features (if available) or 
       assume the robustness report has the summary stats.
    
    Let's assume T026 output includes 'mean_alpha_power' or similar.
    If not, we will calculate it from the primary features and the robustness features 
    if they exist.
    
    Simplified assumption for this implementation:
    The robustness_report.csv from T026 contains a row with the mean alpha power 
    of the robustness dataset. We load the primary features.csv to get the primary mean.
    """
    
    # Load primary features
    if primary_features_path is None:
        primary_features_path = get_path("features")
    
    if not os.path.exists(primary_features_path):
        raise FileNotFoundError(f"Primary features not found at {primary_features_path}.")
    
    primary_df = pd.read_csv(primary_features_path)
    
    # Identify alpha column
    alpha_col = None
    possible_cols = ['alpha_power', 'alpha', 'rel_alpha_power', 'rel_alpha']
    for col in possible_cols:
        if col in primary_df.columns:
            alpha_col = col
            break
    
    if alpha_col is None:
        # Try to find any column containing 'alpha'
        alpha_cols = [c for c in primary_df.columns if 'alpha' in c.lower()]
        if alpha_cols:
            alpha_col = alpha_cols[0]
        else:
            raise ValueError("Could not find alpha power column in primary features.")
    
    primary_mean_alpha = primary_df[alpha_col].mean()
    
    # Check robustness report for mean alpha
    robust_mean_alpha = None
    if 'mean_alpha_power' in robustness_df.columns:
        robust_mean_alpha = robustness_df['mean_alpha_power'].iloc[0]
    elif 'alpha_power_mean' in robustness_df.columns:
        robust_mean_alpha = robustness_df['alpha_power_mean'].iloc[0]
    else:
        # Fallback: If T026 didn't save it, we might need to re-run feature extraction 
        # or fail. For now, we assume T026 saved it. If not, we calculate from the 
        # robustness features file if it exists (T026 might have produced it).
        robust_features_path = get_path("robustness_features", base_dir="data/processed")
        if os.path.exists(robust_features_path):
            robust_df = pd.read_csv(robust_features_path)
            if alpha_col in robust_df.columns:
                robust_mean_alpha = robust_df[alpha_col].mean()
    
    if robust_mean_alpha is None:
        raise ValueError("Could not determine mean alpha power from robustness analysis. "
                         "Ensure T026 outputs mean alpha power or robustness features.")
    
    if primary_mean_alpha == 0:
        pct_diff = float('inf') if robust_mean_alpha != 0 else 0.0
    else:
        pct_diff = abs(primary_mean_alpha - robust_mean_alpha) / abs(primary_mean_alpha) * 100
    
    return {
        "primary_mean_alpha": primary_mean_alpha,
        "robustness_mean_alpha": robust_mean_alpha,
        "alpha_difference": primary_mean_alpha - robust_mean_alpha,
        "alpha_percentage_difference": pct_diff
    }

def main():
    parser = argparse.ArgumentParser(description="Compare robustness metrics (T027)")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading primary model results...")
    primary_results = load_model_results()
    
    print("Loading robustness report...")
    robustness_df = load_robustness_data()
    
    print("Calculating R² stability...")
    r2_metrics = calculate_r2_stability(primary_results, robustness_df)
    
    print("Calculating alpha power difference...")
    alpha_metrics = calculate_alpha_power_difference(robustness_df)
    
    # Compile final comparison report
    comparison_report = {
        "task_id": "T027",
        "description": "Comparison of Primary (4s, ICA) vs Robustness (2s, No-ICA) pipelines",
        "r2_stability": r2_metrics,
        "alpha_power_stability": alpha_metrics,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Save JSON report
    json_path = output_dir / "robustness_comparison.json"
    with open(json_path, 'w') as f:
        json.dump(comparison_report, f, indent=2)
    print(f"Saved R² and alpha stability report to {json_path}")
    
    # Update robustness_report.csv to include the alpha difference
    # We add a new column or a summary row
    if 'alpha_percentage_difference' not in robustness_df.columns:
        robustness_df['alpha_percentage_difference'] = alpha_metrics['alpha_percentage_difference']
    
    updated_csv_path = output_dir / "robustness_report.csv"
    robustness_df.to_csv(updated_csv_path, index=False)
    print(f"Updated robustness report with alpha difference at {updated_csv_path}")
    
    # Print summary
    print("\n--- Robustness Comparison Summary ---")
    print(f"Primary R²: {r2_metrics['primary_r2']:.4f}")
    print(f"Robustness R²: {r2_metrics['robustness_r2']:.4f}")
    print(f"R² % Difference: {r2_metrics['r2_percentage_difference']:.2f}%")
    print(f"Stability Status: {r2_metrics['stability_status']}")
    print(f"Primary Mean Alpha: {alpha_metrics['primary_mean_alpha']:.4f}")
    print(f"Robustness Mean Alpha: {alpha_metrics['robustness_mean_alpha']:.4f}")
    print(f"Alpha % Difference: {alpha_metrics['alpha_percentage_difference']:.2f}%")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())