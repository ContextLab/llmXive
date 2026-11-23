"""
Sensitivity Analysis for Correlation Results (T026)

Implements FR-009: Sweeps p-value thresholds to assess stability of significant findings.
Reads: data/interim/correlations_raw.csv
Writes:
  - data/processed/sensitivity_report.csv
  - data/processed/sensitivity_plot.png
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Import config utilities
# We handle the flexible get_path signature found in the project
try:
    from config import get_path
except ImportError:
    # Fallback if config import fails in some contexts, though tasks.md says config exists
    def get_path(*args, **kwargs):
        # Fallback logic if needed, but we assume config.py is correct per task constraints
        if len(args) == 1:
            # Likely a named key like "processed"
            base = Path("data")
            if args[0] in ["processed", "interim", "raw"]:
                return base / args[0]
            return Path(args[0])
        elif len(args) == 2:
            # Likely base_dir, relative_path
            return Path(args[0]) / args[1]
        raise ValueError(f"Unexpected get_path args: {args}")

def load_correlations():
    """
    Load the raw correlations from the interim directory.
    Expected columns: band, r_value, p_value, n
    """
    # Determine path based on project structure
    # tasks.md says: Reads `data/interim/correlations_raw.csv`
    input_path = Path("data/interim/correlations_raw.csv")

    if not input_path.exists():
        # Try alternative path if the standard one is missing (defensive)
        # Attempting to use config.get_path if available
        try:
            alt_path = get_path("interim", "correlations_raw.csv")
            if not isinstance(alt_path, Path):
                alt_path = Path(alt_path)
            if alt_path.exists():
                input_path = alt_path
        except Exception:
            pass

        if not input_path.exists():
            raise FileNotFoundError(f"Correlations file not found at {input_path}")

    df = pd.read_csv(input_path)
    required_cols = {'band', 'p_value'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Correlations file missing required columns. Found: {df.columns}, Required: {required_cols}")
    return df

def run_sensitivity_sweep(df, min_p=0.001, max_p=0.20, step=0.005):
    """
    Sweep p-value thresholds and count significant correlations.

    Args:
        df: DataFrame with 'p_value' column
        min_p: Start of sweep
        max_p: End of sweep (inclusive)
        step: Step size

    Returns:
        DataFrame with 'threshold' and 'significant_count'
    """
    thresholds = np.arange(min_p, max_p + step/2, step) # +step/2 to handle float precision
    results = []

    for t in thresholds:
        # Round threshold for display consistency
        t_rounded = round(t, 3)
        count = (df['p_value'] <= t_rounded).sum()
        results.append({
            'threshold': t_rounded,
            'significant_count': int(count)
        })

    return pd.DataFrame(results)

def generate_plot(sensitivity_df, output_path):
    """
    Generate and save the sensitivity plot.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(sensitivity_df['threshold'], sensitivity_df['significant_count'],
             marker='o', linestyle='-', color='b', linewidth=2, markersize=8)

    plt.title('Sensitivity Analysis: Significant Correlations vs. P-Value Threshold', fontsize=14)
    plt.xlabel('P-Value Threshold', fontsize=12)
    plt.ylabel('Number of Significant Correlations', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)

    # Set x-ticks to avoid overcrowding if many steps
    if len(sensitivity_df) <= 20:
        plt.xticks(sensitivity_df['threshold'])
    else:
        # Show every 3rd tick or so
        tick_indices = range(0, len(sensitivity_df), max(1, len(sensitivity_df)//10))
        plt.xticks(sensitivity_df.iloc[tick_indices]['threshold'])

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Sensitivity plot saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on correlation results.")
    parser.add_argument('--input', type=str, default=None, help="Path to correlations_raw.csv")
    parser.add_argument('--output-csv', type=str, default=None, help="Path for sensitivity_report.csv")
    parser.add_argument('--output-plot', type=str, default=None, help="Path for sensitivity_plot.png")
    args = parser.parse_args()

    print("Loading correlations data...")
    try:
        df = load_correlations()
        print(f"Loaded {len(df)} correlations.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading correlations: {e}")
        sys.exit(1)

    print("Running sensitivity sweep...")
    sensitivity_df = run_sensitivity_sweep(df)

    # Determine output paths
    if args.output_csv:
        report_path = Path(args.output_csv)
    else:
        # Default path per tasks.md
        report_path = Path("data/processed/sensitivity_report.csv")
        # Try to use config if available to resolve 'processed'
        try:
            p = get_path("processed", "sensitivity_report.csv")
            if p:
                if not isinstance(p, Path):
                    p = Path(p)
                report_path = p
        except Exception:
            pass

    if args.output_plot:
        plot_path = Path(args.output_plot)
    else:
        plot_path = Path("data/processed/sensitivity_plot.png")
        try:
            p = get_path("processed", "sensitivity_plot.png")
            if p:
                if not isinstance(p, Path):
                    p = Path(p)
                plot_path = p
        except Exception:
            pass

    # Write CSV
    report_path.parent.mkdir(parents=True, exist_ok=True)
    sensitivity_df.to_csv(report_path, index=False)
    print(f"Sensitivity report saved to {report_path}")

    # Generate Plot
    generate_plot(sensitivity_df, plot_path)

    print("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()