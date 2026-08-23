"""
T063: Implement Baseline Variance Visualization.

Generates a plot in results/analysis/baseline_variance_plot.png showing the distribution
of latency and success rates for the 3D baseline across runs (or the deterministic subset
from T060) to demonstrate negligible variance compared to the 2D agent.

Dependencies:
    - T060: baseline_determinism_report.md (implies baseline runs exist)
    - results/analysis/final_paired_dataset.csv (contains 3d_latency and 3d_success)
    - results/runs/ (contains individual run logs if available for granular analysis)
"""

import os
import sys
import json
import logging
import argparse
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt

# Project imports
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

def load_paired_dataset(csv_path: str) -> List[Dict[str, Any]]:
    """Load the final paired dataset CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Paired dataset not found at {csv_path}. "
                                "Ensure T047_exec has run.")
    data = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_baseline_runs_json(runs_dir: str) -> List[Dict[str, Any]]:
    """
    Load individual baseline run results if available.
    Expected pattern: results/runs/baseline_run_{run_id}.json or similar.
    If not available, we rely on the aggregated paired dataset.
    """
    runs = []
    if not os.path.exists(runs_dir):
        return runs

    # Try to find baseline specific run files.
    # Based on T017b/T023b patterns, results might be in results/runs/
    # or a specific baseline directory.
    # We look for files containing 'baseline' in the name.
    for filename in os.listdir(runs_dir):
        if 'baseline' in filename.lower() and filename.endswith('.json'):
            filepath = os.path.join(runs_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    runs.append(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not read {filepath}: {e}")
    return runs

def calculate_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate mean, std, min, max for latency and success rate.
    Handles the case where data might be aggregated (paired dataset) or raw runs.
    """
    latencies = []
    successes = []

    for row in data:
        # Try to extract latency
        lat_key = None
        for key in ['3d_latency', 'latency_ms', 'wall_clock_time_ms', 'latency']:
            if key in row:
                lat_key = key
                break
        
        if lat_key:
            try:
                val = float(row[lat_key])
                if not np.isnan(val) and not np.isinf(val):
                    latencies.append(val)
            except (ValueError, TypeError):
                pass

        # Try to extract success
        suc_key = None
        for key in ['3d_success', 'success_flag', 'success']:
            if key in row:
                suc_key = key
                break

        if suc_key:
            try:
                val = float(row[suc_key])
                if not np.isnan(val) and not np.isinf(val):
                    successes.append(val)
            except (ValueError, TypeError):
                pass

    stats = {}
    if latencies:
        stats['latency'] = {
            'mean': float(np.mean(latencies)),
            'std': float(np.std(latencies)),
            'min': float(np.min(latencies)),
            'max': float(np.max(latencies)),
            'count': len(latencies)
        }
    else:
        stats['latency'] = None

    if successes:
        stats['success'] = {
            'mean': float(np.mean(successes)),
            'std': float(np.std(successes)),
            'min': float(np.min(successes)),
            'max': float(np.max(successes)),
            'count': len(successes)
        }
    else:
        stats['success'] = None

    return stats

def generate_plot(
    paired_data: List[Dict[str, Any]],
    baseline_runs: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generate the visualization comparing baseline variance.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('3D Baseline Agent: Latency and Success Variance Analysis', fontsize=16)

    # --- Plot 1: Latency Distribution ---
    ax1 = axes[0]
    ax1.set_title('Latency Distribution (3D Baseline)')
    ax1.set_xlabel('Latency (ms)')
    ax1.set_ylabel('Frequency')

    latencies = []
    for row in paired_data:
        if '3d_latency' in row:
            try:
                val = float(row['3d_latency'])
                if not np.isnan(val):
                    latencies.append(val)
            except ValueError:
                pass

    # If we have raw runs, we might want to show per-task variance if available,
    # but the paired dataset aggregates by task_id.
    # The task requirement is to show distribution across runs or the subset.
    # If paired_data represents the aggregate, we show the distribution of these aggregates.
    # If we have raw runs (T060 subset), we can show those.
    
    if baseline_runs:
        # Flatten latencies from raw runs if available
        raw_latencies = []
        for run in baseline_runs:
            if isinstance(run, dict):
                if 'latency_ms' in run:
                    raw_latencies.append(float(run['latency_ms']))
                elif 'results' in run and isinstance(run['results'], list):
                    for r in run['results']:
                        if 'latency_ms' in r:
                            raw_latencies.append(float(r['latency_ms']))
        if raw_latencies:
            latencies = raw_latencies

    if latencies:
        ax1.hist(latencies, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
        ax1.axvline(np.mean(latencies), color='red', linestyle='dashed', linewidth=2, label=f'Mean: {np.mean(latencies):.2f} ms')
        ax1.axvline(np.mean(latencies) + np.std(latencies), color='green', linestyle='dotted', linewidth=1, label=f'+1 Std: {np.mean(latencies) + np.std(latencies):.2f} ms')
        ax1.axvline(np.mean(latencies) - np.std(latencies), color='green', linestyle='dotted', linewidth=1)
        ax1.legend()
        
        # Add text box with stats
        stats_text = f"Mean: {np.mean(latencies):.2f} ms\nStd Dev: {np.std(latencies):.2f} ms\nN: {len(latencies)}"
        ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        ax1.text(0.5, 0.5, "No latency data found", transform=ax1.transAxes, ha='center', va='center')
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)

    # --- Plot 2: Success Rate Distribution ---
    ax2 = axes[1]
    ax2.set_title('Success Rate Distribution (3D Baseline)')
    ax2.set_xlabel('Success Rate (0-1)')
    ax2.set_ylabel('Frequency')

    successes = []
    for row in paired_data:
        if '3d_success' in row:
            try:
                val = float(row['3d_success'])
                if not np.isnan(val):
                    successes.append(val)
            except ValueError:
                pass

    if baseline_runs:
        raw_successes = []
        for run in baseline_runs:
            if isinstance(run, dict):
                if 'success' in run:
                    raw_successes.append(float(run['success']))
                elif 'results' in run and isinstance(run['results'], list):
                    # Calculate success rate for this run if it has multiple tasks
                    run_successes = []
                    for r in run['results']:
                        if 'success_flag' in r:
                            run_successes.append(float(r['success_flag']))
                    if run_successes:
                        raw_successes.append(np.mean(run_successes))
        if raw_successes:
            successes = raw_successes

    if successes:
        # Since success is often binary (0 or 1) in raw runs, or aggregated (0-1) in paired
        # We use a histogram with enough bins to see the spread if it exists
        ax2.hist(successes, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
        ax2.axvline(np.mean(successes), color='red', linestyle='dashed', linewidth=2, label=f'Mean: {np.mean(successes):.3f}')
        ax2.axvline(np.mean(successes) + np.std(successes), color='green', linestyle='dotted', linewidth=1)
        ax2.axvline(np.mean(successes) - np.std(successes), color='green', linestyle='dotted', linewidth=1)
        ax2.set_xlim(-0.05, 1.05)
        ax2.legend()

        stats_text = f"Mean Success: {np.mean(successes):.3f}\nStd Dev: {np.std(successes):.3f}\nN: {len(successes)}"
        ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        ax2.text(0.5, 0.5, "No success data found", transform=ax2.transAxes, ha='center', va='center')
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Visualization saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate Baseline Variance Visualization (T063)")
    parser.add_argument("--paired-dataset", type=str, default="results/analysis/final_paired_dataset.csv",
                        help="Path to the final paired dataset CSV")
    parser.add_argument("--runs-dir", type=str, default="results/runs",
                        help="Directory containing individual run JSON files")
    parser.add_argument("--output", type=str, default="results/analysis/baseline_variance_plot.png",
                        help="Output path for the plot")
    args = parser.parse_args()

    setup_logging()

    try:
        # Load data
        logger.info(f"Loading paired dataset from {args.paired_dataset}...")
        paired_data = load_paired_dataset(args.paired_dataset)
        logger.info(f"Loaded {len(paired_data)} records.")

        logger.info(f"Scanning for baseline runs in {args.runs_dir}...")
        baseline_runs = load_baseline_runs_json(args.runs_dir)
        logger.info(f"Found {len(baseline_runs)} baseline run files.")

        # Generate plot
        logger.info("Generating visualization...")
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        generate_plot(paired_data, baseline_runs, args.output)

        logger.info("Task T063 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Missing required data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during visualization generation: {e}")
        raise

if __name__ == "__main__":
    main()
