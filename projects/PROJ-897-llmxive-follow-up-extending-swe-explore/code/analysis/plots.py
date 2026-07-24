"""
T031: Visualization of coverage and survival curves.
Generates plots for coverage distribution, boxplots, survival curves (Kaplan-Meier),
and correlation scatter plots.
"""
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
# Use non-interactive backend for headless execution
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Attempt to import lifelines for survival analysis plotting
# If missing, we will skip survival plots but allow the script to run for other plots
try:
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test
    HAS_LIFELINES = True
except ImportError:
    HAS_LIFELINES = False
    print("WARNING: lifelines not installed. Survival curves will be skipped.")

from config import get_path, ensure_directories, get_config_summary

# --- Data Loading ---

def load_metrics_for_plotting(input_path: str) -> Dict[str, Any]:
    """
    Load the final metrics JSON produced by T030c.
    Expects a structure with 'coverage' and 'ranking' lists/objects.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input metrics file not found: {input_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Validate basic structure
    if 'coverage' not in data or 'ranking' not in data:
        raise ValueError("Input metrics missing 'coverage' or 'ranking' keys.")

    return data

# --- Plotting Functions ---

def plot_coverage_histogram(coverage_data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot histogram of coverage scores for Baseline vs Iterative.
    """
    baseline = coverage_data.get('baseline', [])
    iterative = coverage_data.get('iterative', [])

    plt.figure(figsize=(10, 6))
    plt.hist(baseline, bins=20, alpha=0.5, label='Baseline', color='blue', edgecolor='black')
    plt.hist(iterative, bins=20, alpha=0.5, label='Iterative', color='orange', edgecolor='black')

    plt.title('Distribution of Coverage Scores')
    plt.xlabel('Coverage Score (%)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_boxplot_coverage(coverage_data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot boxplot comparing coverage scores.
    """
    baseline = coverage_data.get('baseline', [])
    iterative = coverage_data.get('iterative', [])

    plt.figure(figsize=(8, 6))
    plt.boxplot([baseline, iterative], labels=['Baseline', 'Iterative'], patch_artist=True)
    
    # Color the boxes
    plt.gca().patches[0].set_facecolor('lightblue')
    plt.gca().patches[1].set_facecolor('lightcoral')

    plt.title('Coverage Score Comparison')
    plt.ylabel('Coverage Score (%)')
    plt.grid(axis='y', alpha=0.3)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_survival_curve(ranking_data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot Kaplan-Meier survival curves for Ranking Efficiency.
    'Survival' here means 'not yet found the relevant line'.
    X-axis: Position (Rank), Y-axis: Probability of not having found the line yet.
    """
    if not HAS_LIFELINES:
        print("Skipping survival curve: lifelines library not available.")
        # Create a placeholder image or skip file creation? 
        # Best to skip file creation to avoid confusion, or create a text note.
        # We will skip creating the image file if the library is missing.
        return

    baseline = ranking_data.get('baseline', [])
    iterative = ranking_data.get('iterative', [])

    if not baseline or not iterative:
        print("No ranking data available for survival plot.")
        return

    kmf_baseline = KaplanMeierFitter()
    kmf_iterative = KaplanMeierFitter()

    # Data format expected: list of dicts with 'time' (rank) and 'event' (found: 1, censored: 0)
    # In our context: 'time' is the rank. 'event' is 1 if the relevant line was found at that rank.
    # If the relevant line was NEVER found (censored), the 'time' is the max rank + 1 (or N+1) and 'event' is 0.
    # The stats.py script should have prepared this data in the format:
    # [{'time': rank, 'event': 1}, ...]
    
    # We assume the input data is already in the correct format for lifelines
    # If the data comes as raw lists, we need to transform it.
    # Assuming ranking_data['baseline'] is a list of {'time': float, 'event': int}
    
    try:
        kmf_baseline.fit(durations=baseline['time'], event_observed=baseline['event'], label='Baseline')
        kmf_iterative.fit(durations=iterative['time'], event_observed=iterative['event'], label='Iterative')
    except (KeyError, TypeError) as e:
        print(f"Error formatting survival data: {e}. Skipping plot.")
        return

    plt.figure(figsize=(10, 6))
    kmf_baseline.plot_survival_function(ax=plt.gca())
    kmf_iterative.plot_survival_function(ax=plt.gca())

    plt.title('Survival Analysis: Ranking Efficiency')
    plt.xlabel('Rank (Position of First Relevant Line)')
    plt.ylabel('Probability of Not Yet Finding Relevant Line')
    plt.grid(True)
    plt.legend()

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_correlation_scatter(coverage_data: Dict[str, Any], ranking_data: Dict[str, Any], output_path: Path) -> None:
    """
    Scatter plot of Coverage vs Ranking Efficiency (First Relevant Position).
    Note: Higher ranking efficiency means lower number (better).
    """
    # We need to pair coverage and ranking by issue_id.
    # Assuming the input data structure allows us to zip them or they are aligned.
    # If the data is aggregated, we might not have per-issue pairs here.
    # For this task, we assume the 'metrics' JSON contains a 'paired' section or we can reconstruct.
    
    # If we don't have paired data, we skip this plot or plot aggregated stats.
    # Let's assume the input format includes 'paired_data' if available.
    if 'paired_data' not in coverage_data:
        print("No paired data found for correlation scatter. Skipping.")
        return

    paired = coverage_data['paired_data']
    coverages = [p['coverage'] for p in paired]
    rankings = [p['ranking_efficiency'] for p in paired]

    plt.figure(figsize=(10, 6))
    plt.scatter(coverages, rankings, alpha=0.6, edgecolors='w', s=50)
    
    plt.title('Coverage vs. Ranking Efficiency')
    plt.xlabel('Coverage Score (%)')
    plt.ylabel('First Relevant Position (Lower is Better)')
    plt.grid(True, alpha=0.3)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_all_plots(input_path: str, output_dir: str) -> Dict[str, str]:
    """
    Orchestrates the generation of all plots.
    Returns a dict mapping plot names to their file paths.
    """
    metrics = load_metrics_for_plotting(input_path)
    
    # Extract sub-sections
    coverage_data = metrics.get('coverage', {})
    ranking_data = metrics.get('ranking', {})
    
    # Ensure output directory exists
    out_path = Path(output_dir)
    ensure_directories(out_path)

    generated_files = {}

    # 1. Coverage Histogram
    hist_path = out_path / "coverage_histogram.png"
    plot_coverage_histogram(coverage_data, hist_path)
    generated_files['coverage_histogram'] = str(hist_path)

    # 2. Coverage Boxplot
    box_path = out_path / "coverage_boxplot.png"
    plot_boxplot_coverage(coverage_data, box_path)
    generated_files['coverage_boxplot'] = str(box_path)

    # 3. Survival Curve
    surv_path = out_path / "survival_curve.png"
    if HAS_LIFELINES:
        plot_survival_curve(ranking_data, surv_path)
        generated_files['survival_curve'] = str(surv_path)
    else:
        print("Skipping survival_curve.png (lifelines missing)")

    # 4. Correlation Scatter
    corr_path = out_path / "coverage_ranking_scatter.png"
    plot_correlation_scatter(coverage_data, ranking_data, corr_path)
    if str(corr_path) in generated_files.values():
        generated_files['coverage_ranking_scatter'] = str(corr_path)

    return generated_files

def main():
    """
    CLI entry point.
    Usage: python code/analysis/plots.py --input data/results/final_metrics.json --output docs/figures/
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate analysis plots from final metrics.")
    parser.add_argument('--input', type=str, required=True, help="Path to final_metrics.json")
    parser.add_argument('--output', type=str, required=True, help="Directory to save plots")
    
    args = parser.parse_args()

    try:
        files = generate_all_plots(args.input, args.output)
        print("Generated plots:")
        for name, path in files.items():
            print(f"  - {name}: {path}")
        
        # Write a manifest
        manifest_path = Path(args.output) / "plots_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(files, f, indent=2)
        print(f"Manifest written to {manifest_path}")

    except Exception as e:
        print(f"Error generating plots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
