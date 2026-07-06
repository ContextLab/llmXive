"""
Calibration plots for uncertainty quantification methods.

Generates Interval Width vs. Coverage plots for OLS, Bootstrap, and Bayesian methods.
"""
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

# Ensure consistent styling
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

RESULTS_DIR = Path("data/results")
OUTPUT_FILE = RESULTS_DIR / "calibration_plot.png"
DATA_FILE = RESULTS_DIR / "coverage_metrics.json"

def load_coverage_data() -> List[Dict[str, Any]]:
    """Load coverage metrics from the simulation results."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Coverage metrics file not found: {DATA_FILE}. "
            "Please run the simulation pipeline first to generate data/results/coverage_metrics.json."
        )
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats (depending on how main.py saves it)
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {DATA_FILE}")

def aggregate_by_method(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[float]]]:
    """
    Aggregate coverage and interval width by method.
    
    Returns:
        Dict mapping method_id -> {'coverage': [bool], 'width': [float]}
    """
    aggregated: Dict[str, Dict[str, List[float]]] = {
        'OLS': {'coverage': [], 'width': []},
        'Bootstrap': {'coverage': [], 'width': []},
        'Bayesian': {'coverage': [], 'width': []}
    }
    
    method_map = {
        'ols': 'OLS',
        'bootstrap': 'Bootstrap',
        'bca': 'Bootstrap',
        'bayesian': 'Bayesian',
        'stan': 'Bayesian'
    }
    
    for entry in data:
        method_raw = entry.get('method_id', '').lower()
        method_clean = method_map.get(method_raw, method_raw.capitalize())
        
        if method_clean not in aggregated:
            continue
        
        # Extract width (handle different key names)
        width = entry.get('interval_width', entry.get('width', 0.0))
        if isinstance(width, (int, float)) and width > 0:
            aggregated[method_clean]['width'].append(float(width))
        
        # Extract coverage (handle different key names)
        covered = entry.get('covered', entry.get('coverage', False))
        if isinstance(covered, bool):
            aggregated[method_clean]['coverage'].append(covered)
        elif isinstance(covered, (int, float)):
            aggregated[method_clean]['coverage'].append(bool(covered))
    
    return aggregated

def calculate_binned_metrics(
    widths: List[float], 
    coverages: List[bool], 
    n_bins: int = 10
) -> tuple:
    """
    Bin data by interval width and calculate mean coverage per bin.
    
    Returns:
        tuple: (bin_centers, mean_coverages, bin_counts)
    """
    if len(widths) != len(coverages):
        raise ValueError("Widths and coverages must have the same length")
    
    if len(widths) == 0:
        return np.array([]), np.array([]), np.array([])
    
    # Sort by width
    sorted_indices = np.argsort(widths)
    sorted_widths = np.array(widths)[sorted_indices]
    sorted_coverages = np.array(coverages)[sorted_indices]
    
    # Create bins
    bin_edges = np.linspace(sorted_widths.min(), sorted_widths.max(), n_bins + 1)
    
    bin_centers = []
    mean_coverages = []
    bin_counts = []
    
    for i in range(n_bins):
        lower = bin_edges[i]
        upper = bin_edges[i + 1]
        
        # Handle edge case for last bin
        if i == n_bins - 1:
            mask = (sorted_widths >= lower) & (sorted_widths <= upper)
        else:
            mask = (sorted_widths >= lower) & (sorted_widths < upper)
        
        bin_data = sorted_coverages[mask]
        bin_width_data = sorted_widths[mask]
        
        if len(bin_data) > 0:
            bin_centers.append(np.mean(bin_width_data))
            mean_coverages.append(np.mean(bin_data))
            bin_counts.append(len(bin_data))
        else:
            # Skip empty bins
            continue
    
    return (
        np.array(bin_centers),
        np.array(mean_coverages),
        np.array(bin_counts)
    )

def plot_calibration_curves(
    aggregated: Dict[str, Dict[str, List[float]]],
    nominal_coverage: float = 0.95,
    output_path: Optional[Path] = None
) -> None:
    """
    Generate calibration plot: Interval Width vs. Coverage.
    
    Args:
        aggregated: Data aggregated by method
        nominal_coverage: Target coverage rate (default 0.95)
        output_path: Where to save the plot
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    colors = {
        'OLS': '#1f77b4',      # Blue
        'Bootstrap': '#ff7f0e', # Orange
        'Bayesian': '#2ca02c'   # Green
    }
    
    markers = {
        'OLS': 'o',
        'Bootstrap': 's',
        'Bayesian': '^'
    }
    
    for method_name, method_data in aggregated.items():
        if not method_data['width'] or not method_data['coverage']:
            continue
        
        widths = method_data['width']
        coverages = method_data['coverage']
        
        bin_centers, mean_covs, counts = calculate_binned_metrics(widths, coverages)
        
        if len(bin_centers) > 0:
            ax.scatter(
                bin_centers,
                mean_covs,
                s=np.sqrt(counts) * 50,  # Size proportional to count
                alpha=0.7,
                label=method_name,
                color=colors.get(method_name, 'gray'),
                marker=markers.get(method_name, 'o'),
                edgecolors='black',
                linewidths=0.5
            )
            # Connect points for visual trend
            ax.plot(bin_centers, mean_covs, linestyle='--', alpha=0.5, 
                   color=colors.get(method_name, 'gray'), linewidth=1)
    
    # Add nominal coverage line
    ax.axhline(y=nominal_coverage, color='red', linestyle='-', 
              linewidth=2, label=f'Nominal Coverage ({nominal_coverage*100:.0f}%)', alpha=0.8)
    
    # Add ideal calibration line (Width vs Coverage should ideally be flat at nominal)
    # But we plot width on x-axis, so we just show the target coverage line
    
    ax.set_xlabel('Mean Interval Width', fontsize=14, fontweight='bold')
    ax.set_ylabel('Empirical Coverage Rate', fontsize=14, fontweight='bold')
    ax.set_title('Calibration Plot: Interval Width vs. Coverage', fontsize=16, fontweight='bold')
    ax.legend(loc='lower right', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.0, 1.05)
    
    # Add annotation for total samples per method
    for method_name, method_data in aggregated.items():
        total = len(method_data['width'])
        if total > 0:
            ax.text(0.05, 0.95 - (list(aggregated.keys()).index(method_name) * 0.05),
                   f'{method_name}: n={total}',
                   transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    save_path = output_path if output_path else OUTPUT_FILE
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Calibration plot saved to: {save_path}")

def main():
    """Main entry point for generating calibration plots."""
    print("Loading coverage metrics...")
    try:
        data = load_coverage_data()
        print(f"Loaded {len(data)} records from {DATA_FILE}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the simulation pipeline has been run to generate data/results/coverage_metrics.json")
        return 1
    
    print("Aggregating data by method...")
    aggregated = aggregate_by_method(data)
    
    # Check if we have data for all methods
    methods_with_data = [m for m, d in aggregated.items() if d['width']]
    if not methods_with_data:
        print("Error: No valid data found for any method in coverage_metrics.json")
        return 1
    
    print(f"Found data for methods: {', '.join(methods_with_data)}")
    
    print("Generating calibration plot...")
    try:
        plot_calibration_curves(aggregated)
        print("Success!")
    except Exception as e:
        print(f"Error generating plot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
