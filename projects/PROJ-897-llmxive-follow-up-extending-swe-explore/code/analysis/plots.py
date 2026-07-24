"""
Visualization module for llmXive analysis.
Generates plots for coverage distributions and survival curves.
"""
import json
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np

from config import get_path, get_config_summary
from utils.hash_artifacts import compute_sha256

# Ensure output directory exists
FIGURES_DIR = get_path("data/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_metrics_for_plotting(input_path: str) -> Dict[str, Any]:
    """
    Load the final metrics JSON containing coverage and ranking data.
    Expects a structure with 'coverage' and 'ranking' keys.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {input_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

def plot_coverage_histogram(data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot a histogram of coverage scores for Baseline vs Iterative agents.
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

    baseline_coverage = data.get('coverage', {}).get('baseline_scores', [])
    iterative_coverage = data.get('coverage', {}).get('iterative_scores', [])

    if not baseline_coverage and not iterative_coverage:
        plt.text(0.5, 0.5, "No coverage data available", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("Coverage Distribution (No Data)")
    else:
        bins = np.linspace(0, 1.1, 12)
        if baseline_coverage:
            plt.hist(baseline_coverage, bins=bins, alpha=0.5, label='Baseline', color='blue', edgecolor='black')
        if iterative_coverage:
            plt.hist(iterative_coverage, bins=bins, alpha=0.5, label='Iterative', color='orange', edgecolor='black')

        plt.xlabel('Coverage Score')
        plt.ylabel('Frequency')
        plt.title('Distribution of Line Coverage Scores')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_boxplot_coverage(data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot a boxplot comparing coverage distributions.
    """
    plt.figure(figsize=(8, 6))

    baseline_coverage = data.get('coverage', {}).get('baseline_scores', [])
    iterative_coverage = data.get('coverage', {}).get('iterative_scores', [])

    if not baseline_coverage and not iterative_coverage:
        plt.text(0.5, 0.5, "No coverage data available", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("Coverage Comparison (No Data)")
    else:
        plt.boxplot([baseline_coverage, iterative_coverage], labels=['Baseline', 'Iterative'], patch_artist=True,
                    boxprops=dict(facecolor='lightblue'), medianprops=dict(color='red'))
        plt.ylabel('Coverage Score')
        plt.title('Coverage Score Comparison')
        plt.grid(axis='y', alpha=0.3)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_survival_curve(data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot the Kaplan-Meier survival curves for Ranking Efficiency.
    Handles censored data (where coverage was 0).
    """
    plt.figure(figsize=(10, 6))

    # Expecting data structure:
    # 'ranking': {
    #   'baseline': {'times': [...], 'events': [...]},
    #   'iterative': {'times': [...], 'events': [...]}
    # }
    # events: 1 = event observed (found line), 0 = censored (not found)

    ranking_data = data.get('ranking', {})
    baseline = ranking_data.get('baseline', {})
    iterative = ranking_data.get('iterative', {})

    baseline_times = baseline.get('times', [])
    baseline_events = baseline.get('events', [])
    iterative_times = iterative.get('times', [])
    iterative_events = iterative.get('events', [])

    if not baseline_times and not iterative_times:
        plt.text(0.5, 0.5, "No ranking data available", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("Survival Curves (No Data)")
    else:
        # Sort by time to ensure correct plotting order if needed, though KM usually handles it
        # We assume the input data is already sorted or handled by the stats module.
        
        # Plot Baseline
        if baseline_times:
            # Simple step plot approximation for visualization
            # In a real KM plot, we'd calculate survival probability S(t)
            # For this visualization, we plot the raw times with markers for events
            # To make it look like a survival curve, we sort and compute cumulative survival
            
            # Sort by time
            sorted_indices = np.argsort(baseline_times)
            times = np.array(baseline_times)[sorted_indices]
            events = np.array(baseline_events)[sorted_indices]
            
            # Calculate survival probability (Kaplan-Meier estimator simplified)
            n = len(times)
            survival_probs = np.ones(n + 1)
            for i in range(n):
                if events[i] == 1:
                    # Event occurred
                    survival_probs[i+1] = survival_probs[i] * (1 - 1.0 / (n - i))
                else:
                    # Censored
                    survival_probs[i+1] = survival_probs[i]
            
            # Plot steps
            times_plot = np.concatenate([[0], times])
            probs_plot = survival_probs
            
            plt.step(times_plot, probs_plot, where='post', label='Baseline', color='blue', linewidth=2)
            # Mark events
            event_times = times[events == 1]
            if len(event_times) > 0:
                # Find corresponding probabilities for events
                # This is a rough approximation for visual markers
                plt.scatter(event_times, survival_probs[:-1][events == 1], color='blue', s=20, marker='o')

        # Plot Iterative
        if iterative_times:
            sorted_indices = np.argsort(iterative_times)
            times = np.array(iterative_times)[sorted_indices]
            events = np.array(iterative_events)[sorted_indices]
            
            n = len(times)
            survival_probs = np.ones(n + 1)
            for i in range(n):
                if events[i] == 1:
                    survival_probs[i+1] = survival_probs[i] * (1 - 1.0 / (n - i))
                else:
                    survival_probs[i+1] = survival_probs[i]
            
            times_plot = np.concatenate([[0], times])
            probs_plot = survival_probs
            
            plt.step(times_plot, probs_plot, where='post', label='Iterative', color='orange', linewidth=2)
            event_times = times[events == 1]
            if len(event_times) > 0:
                plt.scatter(event_times, survival_probs[:-1][events == 1], color='orange', s=20, marker='o')

        plt.xlabel('Rank (Position of First Relevant Line)')
        plt.ylabel('Survival Probability (Not yet found)')
        plt.title('Ranking Efficiency: Survival Curves')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.xlim(left=0)
        plt.ylim(bottom=0, top=1.05)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_correlation_scatter(data: Dict[str, Any], output_path: Path) -> None:
    """
    Plot correlation between coverage and ranking metrics if available.
    """
    # This is optional and depends on specific data structure availability
    # For now, creating a placeholder or simple scatter if data exists
    plt.figure(figsize=(8, 6))
    
    # Check if we have paired data
    # Assuming 'coverage' and 'ranking' lists are aligned by issue_id
    # This requires the input data to be structured specifically
    
    # If data has 'issues' list with both metrics
    issues = data.get('issues', [])
    if issues:
        coverages = [i.get('coverage_score') for i in issues if i.get('coverage_score') is not None]
        rankings = [i.get('ranking_score') for i in issues if i.get('ranking_score') is not None]
        
        if coverages and rankings and len(coverages) == len(rankings):
            plt.scatter(coverages, rankings, alpha=0.6, edgecolor='k')
            plt.xlabel('Coverage Score')
            plt.ylabel('Ranking Score (Lower is better)')
            plt.title('Coverage vs Ranking Efficiency')
            plt.grid(True, alpha=0.3)
        else:
            plt.text(0.5, 0.5, "Insufficient paired data", ha='center', va='center', transform=plt.gca().transAxes)
    else:
        plt.text(0.5, 0.5, "No paired issue data found", ha='center', va='center', transform=plt.gca().transAxes)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def generate_all_plots(input_path: str, output_dir: Optional[Path] = None) -> List[Path]:
    """
    Generate all standard plots and save them to the output directory.
    Returns a list of generated file paths.
    """
    if output_dir is None:
        output_dir = FIGURES_DIR
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    data = load_metrics_for_plotting(input_path)
    generated_files = []

    # 1. Coverage Histogram
    hist_path = output_dir / "coverage_histogram.png"
    plot_coverage_histogram(data, hist_path)
    generated_files.append(hist_path)

    # 2. Coverage Boxplot
    box_path = output_dir / "coverage_boxplot.png"
    plot_boxplot_coverage(data, box_path)
    generated_files.append(box_path)

    # 3. Survival Curve (Ranking)
    surv_path = output_dir / "ranking_survival_curve.png"
    plot_survival_curve(data, surv_path)
    generated_files.append(surv_path)

    # 4. Correlation Scatter
    corr_path = output_dir / "coverage_ranking_scatter.png"
    plot_correlation_scatter(data, corr_path)
    generated_files.append(corr_path)

    return generated_files

def main():
    parser = argparse.ArgumentParser(description="Generate analysis plots for llmXive.")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to the final_metrics.json file (e.g., data/results/final_metrics.json)")
    parser.add_argument("--output", type=str, default=str(FIGURES_DIR),
                        help="Directory to save generated plots (default: data/figures)")
    
    args = parser.parse_args()

    try:
        output_dir = Path(args.output)
        files = generate_all_plots(args.input, output_dir)
        
        # Hash artifacts
        for f in files:
            sha = compute_sha256(f)
            print(f"Generated: {f} (SHA256: {sha[:16]}...)")
        
        print(f"Successfully generated {len(files)} plots.")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error generating plots: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
