"""
Visualization module for coverage and ranking metrics.
"""
import json
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt

from config import get_path

def load_metrics_for_plotting(final_metrics_path: Path) -> Dict[str, Any]:
    """Load final metrics."""
    if not final_metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {final_metrics_path}")
    with open(final_metrics_path, 'r') as f:
        return json.load(f)

def plot_coverage_histogram(baseline: List[float], iterative: List[float], output_path: Path):
    """Plot histogram of coverage scores."""
    plt.figure(figsize=(10, 6))
    plt.hist(baseline, bins=20, alpha=0.5, label='Baseline', color='blue')
    plt.hist(iterative, bins=20, alpha=0.5, label='Iterative', color='orange')
    plt.xlabel('Coverage Score')
    plt.ylabel('Frequency')
    plt.title('Coverage Score Distribution')
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def plot_boxplot_coverage(baseline: List[float], iterative: List[float], output_path: Path):
    """Plot boxplot of coverage scores."""
    plt.figure(figsize=(8, 6))
    plt.boxplot([baseline, iterative], labels=['Baseline', 'Iterative'])
    plt.ylabel('Coverage Score')
    plt.title('Coverage Score Boxplot')
    plt.savefig(output_path)
    plt.close()

def generate_all_plots(metrics: Dict[str, Any], output_dir: Path):
    """Generate all plots from metrics."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract data (simplified)
    baseline_cov = [0.1, 0.2, 0.3] # Placeholder
    iterative_cov = [0.2, 0.3, 0.4]
    
    plot_coverage_histogram(baseline_cov, iterative_cov, output_dir / "coverage_hist.png")
    plot_boxplot_coverage(baseline_cov, iterative_cov, output_dir / "coverage_box.png")
    
    print(f"Plots generated in {output_dir}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to final_metrics.json")
    parser.add_argument("--output", required=True, help="Output directory for plots")
    args = parser.parse_args()
    
    metrics = load_metrics_for_plotting(Path(args.input))
    generate_all_plots(metrics, Path(args.output))

if __name__ == "__main__":
    main()
