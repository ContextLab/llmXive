import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/headless environments

from code.visualization.plotter import load_error_rates

def load_low_sample_data(
    input_path: str = "data/simulation/error_rates_summary.csv",
    max_n: int = 30
) -> Dict[str, Dict[str, List[Tuple[int, float, float, float]]]]:
    """
    Load error rates from the summary CSV and filter for sample sizes <= max_n.
    
    Returns a nested dict: {test_type: {effect_size: [(n, type1_rate, type2_rate, power), ...]}}
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Run US1 simulation first.")
    
    data: Dict[str, Dict[str, List[Tuple[int, float, float, float]]]] = {}
    
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['sample_size'])
            if n > max_n:
                continue
            
            test_type = row['test_type']
            effect_size = row['effect_size']
            
            # Parse rates
            type1_rate = float(row['type1_error_rate'])
            type2_rate = float(row['type2_error_rate'])
            power = float(row['power'])
            
            if test_type not in data:
                data[test_type] = {}
            if effect_size not in data[test_type]:
                data[test_type][effect_size] = []
            
            data[test_type][effect_size].append((n, type1_rate, type2_rate, power))
    
    return data

def plot_test_divergence(
    data: Dict[str, Dict[str, List[Tuple[int, float, float, float]]]],
    output_path: str,
    metric: str = 'type1_error_rate',
    alpha_level: float = 0.05
):
    """
    Plot divergence of error rates for different tests at low sample sizes.
    
    Args:
        data: Filtered data from load_low_sample_data
        output_path: Where to save the plot
        metric: 'type1_error_rate' or 'power' (for type2, we plot 1-type2 = power usually, but here we might want raw type2)
        alpha_level: Nominal alpha for Type I reference line
    """
    plt.figure(figsize=(12, 8))
    
    colors = {'t-test': '#1f77b4', 'anova': '#ff7f0e', 'chi-squared': '#2ca02c'}
    markers = {'t-test': 'o', 'anova': 's', 'chi-squared': '^'}
    
    # We focus on Type I error for n < 30 to see inflation/deflation from nominal alpha
    # Or Power if we are looking at sensitivity
    # The task asks for "divergence", implying how they deviate from expected behavior (alpha=0.05 for null, power=1 for alt)
    # Let's plot Type I error rates (where null is true) to see inflation at small n.
    
    plot_metric = 'type1_error_rate' if metric == 'type1_error_rate' else None
    
    # We will plot for a representative effect size (usually 0 for Type I, or small for power)
    # The CSV has effect_size. For Type I, effect_size is usually 0.
    # Let's filter for effect_size == '0' or '0.0' if available, otherwise just plot all or pick one.
    # To make it clear, let's plot the 0 effect size (Type I) specifically.
    
    target_effect_size = '0'
    
    for test_type, effect_data in data.items():
        if target_effect_size in effect_data:
            points = effect_data[target_effect_size]
            # Sort by n
            points.sort(key=lambda x: x[0])
            ns = [p[0] for p in points]
            
            if plot_metric == 'type1_error_rate':
                rates = [p[1] for p in points]
                label = f"{test_type} (Type I, eff=0)"
            else:
                # Fallback or power plot
                rates = [p[3] for p in points] # Power
                label = f"{test_type} (Power)"
            
            plt.plot(ns, rates, marker=markers.get(test_type, 'o'), label=label, color=colors.get(test_type, 'gray'))
    
    plt.axhline(y=alpha_level, color='red', linestyle='--', label=f'Nominal Alpha ({alpha_level})')
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Type I Error Rate')
    plt.title('Divergence of Type I Error Rates at Low Sample Sizes (n < 30)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 35)
    plt.ylim(0, 0.2) # Focus on the region around 0.05
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_test_pairwise_divergence(
    data: Dict[str, Dict[str, List[Tuple[int, float, float, float]]]],
    output_path: str
):
    """
    Plot pairwise differences or overlay all tests to show divergence patterns clearly.
    Specifically focusing on the spread between tests at the lowest sample sizes.
    """
    plt.figure(figsize=(12, 8))
    
    colors = {'t-test': '#1f77b4', 'anova': '#ff7f0e', 'chi-squared': '#2ca02c'}
    markers = {'t-test': 'o', 'anova': 's', 'chi-squared': '^'}
    
    target_effect_size = '0'
    
    all_ns = set()
    test_series = {}
    
    for test_type, effect_data in data.items():
        if target_effect_size in effect_data:
            points = effect_data[target_effect_size]
            points.sort(key=lambda x: x[0])
            ns = [p[0] for p in points]
            rates = [p[1] for p in points] # Type I
            test_series[test_type] = {'n': ns, 'rate': rates}
            all_ns.update(ns)
    
    # Sort all sample sizes
    sorted_ns = sorted(list(all_ns))
    
    for test_type, series in test_series.items():
        # Interpolate or just plot existing points
        # Since we have exact matches from CSV, we can just plot
        plt.plot(series['n'], series['rate'], marker=markers.get(test_type, 'o'), 
                 label=test_type.replace('-', ' ').title(), color=colors.get(test_type, 'gray'), linewidth=2)
    
    plt.axhline(y=0.05, color='black', linestyle=':', label='Nominal Alpha (0.05)')
    
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Type I Error Rate')
    plt.title('Comparative Divergence: t-test vs ANOVA vs Chi-Squared (n < 30)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 35)
    plt.ylim(0, 0.15)
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def generate_comparative_plots(
    input_path: str = "data/simulation/error_rates_summary.csv",
    output_dir: str = "data/visualization"
) -> List[str]:
    """
    Main entry point to generate all comparative plots for T026.
    Returns list of generated file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    # Load and filter data
    try:
        data = load_low_sample_data(input_path, max_n=30)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return []
    
    # Plot 1: Type I Error Divergence (Inflation/Deflation)
    plot1_path = os.path.join(output_dir, "comparative_type1_divergence_n30.png")
    plot_test_divergence(data, plot1_path, metric='type1_error_rate')
    generated_files.append(plot1_path)
    
    # Plot 2: Pairwise Comparison Overlay
    plot2_path = os.path.join(output_dir, "comparative_test_overlay_n30.png")
    plot_test_pairwise_divergence(data, plot2_path)
    generated_files.append(plot2_path)
    
    return generated_files

def main():
    """CLI entry point for T026."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate comparative plots for low sample sizes.")
    parser.add_argument("--input", default="data/simulation/error_rates_summary.csv", help="Input CSV path")
    parser.add_argument("--output", default="data/visualization", help="Output directory")
    args = parser.parse_args()
    
    print(f"Generating comparative plots from {args.input}...")
    files = generate_comparative_plots(args.input, args.output)
    
    if files:
        print(f"Successfully generated {len(files)} plots:")
        for f in files:
            print(f"  - {f}")
    else:
        print("No plots generated. Check input file and data availability.")

if __name__ == "__main__":
    main()
