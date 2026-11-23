"""
Generate the final results metrics CSV file.

This script aggregates effect sizes from the OLS model (T030/T031) and
sensitivity statistics (T033/T034) into a single summary file:
data/processed/results_metrics.csv.

It relies on the outputs of:
- code/models.py (effect sizes) -> data/processed/effect_sizes.csv
- code/sensitivity.py (sensitivity analysis) -> data/processed/sensitivity_analysis.csv
- code/calculate_stability.py (stability report) -> data/processed/significance_stability_report.csv
- code/calculate_flip_rate.py (flip rate report) -> data/processed/significance_flip_rate_report.csv
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if running as script
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
data_dir = project_root / "data" / "processed"

# Ensure paths exist
os.makedirs(data_dir, exist_ok=True)

def load_effect_sizes(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load effect sizes from the models output."""
    if filepath is None:
        filepath = data_dir / "effect_sizes.csv"
    if not filepath.exists():
        raise FileNotFoundError(f"Effect sizes file not found: {filepath}")
    return pd.read_csv(filepath)

def load_sensitivity_stats(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load sensitivity analysis stats."""
    if filepath is None:
        filepath = data_dir / "sensitivity_analysis.csv"
    if not filepath.exists():
        raise FileNotFoundError(f"Sensitivity analysis file not found: {filepath}")
    return pd.read_csv(filepath)

def load_stability_metrics(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load significance stability metrics."""
    if filepath is None:
        filepath = data_dir / "significance_stability_report.csv"
    if not filepath.exists():
        raise FileNotFoundError(f"Stability report file not found: {filepath}")
    return pd.read_csv(filepath)

def load_flip_rate_metrics(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load significance flip rate metrics."""
    if filepath is None:
        filepath = data_dir / "significance_flip_rate_report.csv"
    if not filepath.exists():
        raise FileNotFoundError(f"Flip rate report file not found: {filepath}")
    return pd.read_csv(filepath)

def merge_metrics(
    effect_sizes: pd.DataFrame,
    sensitivity: pd.DataFrame,
    stability: pd.DataFrame,
    flip_rate: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge all metrics into a single dataframe.

    Expected structure:
    - effect_sizes: comparison, coef, std_err, p_value, cohens_d
    - stability: comparison, stability_rate, num_shifts, total_shifts
    - flip_rate: comparison, flip_rate, num_flips, total_shifts

    Returns a unified dataframe with one row per comparison.
    """
    # Ensure comparison columns are consistent for merging
    for df in [effect_sizes, stability, flip_rate]:
        if 'comparison' not in df.columns:
            # Try to infer if the index is the comparison
            if df.index.name == 'comparison':
                df = df.reset_index()
            else:
                raise ValueError(f"DataFrame {df.columns} missing 'comparison' column")

    # Merge on 'comparison'
    merged = effect_sizes.merge(stability, on='comparison', how='outer')
    merged = merged.merge(flip_rate, on='comparison', how='outer')

    # Add sensitivity stats (usually a single row summary or per-boundary)
    # If sensitivity is per-boundary, we might need to aggregate or just join the summary row.
    # Assuming sensitivity_analysis.csv has a summary row or we take the first/mean.
    # For this implementation, we assume it has a 'comparison' column or is a single summary.
    if 'comparison' in sensitivity.columns:
        # If it has multiple rows per comparison (e.g., per boundary shift), aggregate
        agg_sensitivity = sensitivity.groupby('comparison').agg({
            'avg_p_value': 'mean',
            'significant_count': 'sum',
            'total_count': 'first' # or sum if it's per row
        }).reset_index()
        merged = merged.merge(agg_sensitivity, on='comparison', how='outer')
    else:
        # Assume single summary row for the whole experiment
        summary_row = sensitivity.iloc[0]
        for col in summary_row.index:
            merged[col] = summary_row[col]

    # Fill NaNs with 0 or appropriate defaults where logical
    numeric_cols = merged.select_dtypes(include=[np.number]).columns
    merged[numeric_cols] = merged[numeric_cols].fillna(0)

    return merged

def save_results_metrics(df: pd.DataFrame, filepath: Optional[Path] = None) -> None:
    """Save the merged metrics to CSV."""
    if filepath is None:
        filepath = data_dir / "results_metrics.csv"
    df.to_csv(filepath, index=False)
    print(f"Saved results metrics to {filepath}")

def main():
    """Main entry point to generate the results metrics file."""
    try:
        # Load dependencies
        print("Loading effect sizes...")
        effect_sizes = load_effect_sizes()

        print("Loading sensitivity stats...")
        sensitivity = load_sensitivity_stats()

        print("Loading stability metrics...")
        stability = load_stability_metrics()

        print("Loading flip rate metrics...")
        flip_rate = load_flip_rate_metrics()

        # Merge
        print("Merging metrics...")
        results = merge_metrics(effect_sizes, sensitivity, stability, flip_rate)

        # Save
        print("Saving results...")
        save_results_metrics(results)

        print("T035 Complete: data/processed/results_metrics.csv generated.")
        return 0

    except FileNotFoundError as e:
        print(f"Error: Missing required input file. {e}")
        print("Ensure T030, T031, T032, T033, and T034 have been executed successfully.")
        return 1
    except Exception as e:
        print(f"Error generating results metrics: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
