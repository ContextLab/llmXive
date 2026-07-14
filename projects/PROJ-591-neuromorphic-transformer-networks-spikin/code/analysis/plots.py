"""
Visualization script for Sensitivity Curves and Trade-off Plots.
Generates plots for User Story 3 (Statistical Analysis).
"""
import os
import sys
import argparse
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

# Ensure the code directory is in the path for imports
_code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

from analysis.sensitivity_analysis import run_sensitivity_sweep, load_metrics_data

# Constants for paths
DATA_DIR = "data"
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
FIGURES_DIR = os.path.join(DATA_DIR, "figures")

# Ensure output directories exist
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

def load_sensitivity_results(csv_path: str) -> pd.DataFrame:
    """
    Load sensitivity analysis results from CSV.
    Expected columns: threshold, fp_rate, fn_rate, accuracy, energy_reduction_mean
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Sensitivity results file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    # Ensure numeric types
    numeric_cols = ['threshold', 'fp_rate', 'fn_rate', 'accuracy', 'energy_reduction_mean']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def plot_sensitivity_curves(
    df: pd.DataFrame, 
    output_path: str, 
    title: str = "Sensitivity Analysis: Error Rates vs Threshold"
) -> None:
    """
    Plot False Positive and False Negative rates against energy reduction thresholds.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    if 'threshold' not in df.columns or 'fp_rate' not in df.columns or 'fn_rate' not in df.columns:
        raise ValueError("DataFrame missing required columns: threshold, fp_rate, fn_rate")

    x = df['threshold']
    y_fp = df['fp_rate']
    y_fn = df['fn_rate']

    ax.plot(x, y_fp, marker='o', linestyle='-', color='#d62728', label='False Positive Rate')
    ax.plot(x, y_fn, marker='s', linestyle='-', color='#1f77b4', label='False Negative Rate')

    # Mark the ground truth threshold (30% reduction)
    # Assuming 0.30 is the target, highlight it
    target_threshold = 0.30
    if target_threshold in x.values:
        ax.axvline(x=target_threshold, color='gray', linestyle='--', alpha=0.7, label='Target Threshold (30%)')

    ax.set_xlabel('Energy Reduction Threshold', fontsize=12)
    ax.set_ylabel('Error Rate', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='best')
    ax.set_ylim(bottom=0.0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Sensitivity curve saved to: {output_path}")

def plot_trade_off_curve(
    baseline_df: pd.DataFrame,
    spiking_df: pd.DataFrame,
    output_path: str,
    title: str = "Performance vs Energy: Baseline vs Spiking"
) -> None:
    """
    Plot Perplexity vs Energy per Token for Baseline and Spiking models.
    Aggregates by seed to show mean and error bars.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    # Aggregate by seed
    if 'seed' not in baseline_df.columns or 'perplexity' not in baseline_df.columns or 'energy_per_token_kWh' not in baseline_df.columns:
        raise ValueError("Baseline DataFrame missing required columns.")
    
    if 'seed' not in spiking_df.columns or 'perplexity' not in spiking_df.columns or 'energy_per_token_kWh' not in spiking_df.columns:
        raise ValueError("Spiking DataFrame missing required columns.")

    # Group by seed to get the final epoch or mean performance per seed
    # Assuming the last row per seed is the final result, or we take the mean of the last 3 epochs
    def get_final_metrics(group):
        # Sort by epoch descending and take the last one
        group = group.sort_values('epoch', ascending=False)
        return group.iloc[0]

    baseline_final = baseline_df.groupby('seed').apply(get_final_metrics).reset_index(drop=True)
    spiking_final = spiking_df.groupby('seed').apply(get_final_metrics).reset_index(drop=True)

    # Plot Baseline
    ax.scatter(
        baseline_final['energy_per_token_kWh'],
        baseline_final['perplexity'],
        color='#1f77b4',
        label='Baseline Transformer',
        s=100,
        alpha=0.7,
        edgecolors='black',
        linewidth=1.5
    )

    # Plot Spiking
    ax.scatter(
        spiking_final['energy_per_token_kWh'],
        spiking_final['perplexity'],
        color='#d62728',
        label='Spiking Transformer',
        s=100,
        alpha=0.7,
        edgecolors='black',
        linewidth=1.5,
        marker='s'
    )

    # Connect paired seeds with lines to visualize the shift
    # Ensure both have the same seeds
    common_seeds = sorted(set(baseline_final['seed']).intersection(set(spiking_final['seed'])))
    
    for seed in common_seeds:
        b_row = baseline_final[baseline_final['seed'] == seed].iloc[0]
        s_row = spiking_final[spiking_final['seed'] == seed].iloc[0]
        
        ax.plot(
            [b_row['energy_per_token_kWh'], s_row['energy_per_token_kWh']],
            [b_row['perplexity'], s_row['perplexity']],
            color='gray',
            linestyle=':',
            alpha=0.5
        )

    ax.set_xlabel('Energy per Token (kWh)', fontsize=12)
    ax.set_ylabel('Perplexity (Validation)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='best')
    
    # Invert X axis if we want lower energy to be on the right? 
    # Usually lower energy is better (left), lower perplexity is better (down).
    # So bottom-left is ideal.
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Trade-off curve saved to: {output_path}")

def plot_combined_analysis(
    sensitivity_csv: str,
    baseline_csv: str,
    spiking_csv: str,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Generates all required plots for T026.
    Returns a dictionary of generated file paths.
    """
    if output_dir is None:
        output_dir = FIGURES_DIR
    
    os.makedirs(output_dir, exist_ok=True)

    generated_files = {}

    # 1. Sensitivity Curves
    try:
        sens_df = load_sensitivity_results(sensitivity_csv)
        sens_plot_path = os.path.join(output_dir, "sensitivity_curves.png")
        plot_sensitivity_curves(sens_df, sens_plot_path)
        generated_files['sensitivity_curve'] = sens_plot_path
    except FileNotFoundError as e:
        print(f"Warning: Could not generate sensitivity curve: {e}")
        print("Make sure 'data/results/sensitivity_analysis.csv' exists.")
    except Exception as e:
        print(f"Error generating sensitivity curve: {e}")

    # 2. Trade-off Curve
    try:
        baseline_df = pd.read_csv(baseline_csv)
        spiking_df = pd.read_csv(spiking_csv)
        tradeoff_plot_path = os.path.join(output_dir, "energy_perplexity_tradeoff.png")
        plot_trade_off_curve(baseline_df, spiking_df, tradeoff_plot_path)
        generated_files['trade_off_curve'] = tradeoff_plot_path
    except FileNotFoundError as e:
        print(f"Warning: Could not generate trade-off curve: {e}")
    except Exception as e:
        print(f"Error generating trade-off curve: {e}")

    return generated_files

def main():
    parser = argparse.ArgumentParser(description="Generate visualization plots for US3 analysis.")
    parser.add_argument(
        "--sensitivity",
        type=str,
        default=os.path.join(PROCESSED_DIR, "sensitivity_analysis.csv"),
        help="Path to sensitivity analysis CSV (usually data/results/sensitivity_analysis.csv)"
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=os.path.join(PROCESSED_DIR, "baseline_metrics.csv"),
        help="Path to baseline metrics CSV"
    )
    parser.add_argument(
        "--spiking",
        type=str,
        default=os.path.join(PROCESSED_DIR, "spiking_metrics.csv"),
        help="Path to spiking metrics CSV"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=FIGURES_DIR,
        help="Directory to save output plots"
    )

    args = parser.parse_args()

    # Correct the default path for sensitivity if it was set to processed but usually it's in results
    if args.sensitivity == os.path.join(PROCESSED_DIR, "sensitivity_analysis.csv"):
        # Check if it exists in processed, if not try results
        if not os.path.exists(args.sensitivity):
            alt_path = os.path.join(RESULTS_DIR, "sensitivity_analysis.csv")
            if os.path.exists(alt_path):
                args.sensitivity = alt_path
                print(f"Using sensitivity data from: {alt_path}")

    print(f"Generating plots from:")
    print(f"  Sensitivity: {args.sensitivity}")
    print(f"  Baseline:    {args.baseline}")
    print(f"  Spiking:     {args.spiking}")
    print(f"  Output Dir:  {args.output_dir}")

    results = plot_combined_analysis(
        sensitivity_csv=args.sensitivity,
        baseline_csv=args.baseline,
        spiking_csv=args.spiking,
        output_dir=args.output_dir
    )

    if results:
        print("\nSuccessfully generated the following plots:")
        for name, path in results.items():
            print(f"  - {name}: {path}")
    else:
        print("\nNo plots were generated. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()