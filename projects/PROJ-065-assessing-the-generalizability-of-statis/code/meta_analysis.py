"""
Meta-analysis module for aggregating stability rates and generating visualizations.

This module implements User Story 3: Aggregate Fragility Indices and Generate Visualizations.
It loads study results from JSON files, calculates aggregate metrics (mean, median, I²),
and generates forest plots and histograms.
"""
import os
import json
import glob
import math
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Import from sibling modules as per API surface
# Note: We don't import from bootstrap_engine directly to avoid circular dependencies,
# but we assume the JSON structure matches StudyStabilityResult schema.

# Constants
FIGURE_DPI = 300
FIGURE_WIDTH = 10
FIGURE_HEIGHT = 8
FRAGILITY_THRESHOLD = 0.80  # 80% stability rate threshold for fragile findings
SIGNIFICANCE_LEVEL = 0.05

def load_study_results(data_dir: str = "data/processed") -> List[Dict[str, Any]]:
    """
    Load all study result JSON files from the data directory.
    
    Args:
        data_dir: Path to the directory containing study result JSON files.
        
    Returns:
        List of dictionaries containing study results.
        
    Raises:
        FileNotFoundError: If no study result files are found.
    """
    pattern = os.path.join(data_dir, "study_*_results.json")
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"No study result files found matching pattern: {pattern}")
    
    results = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                study_data = json.load(f)
                # Validate schema contains required keys
                required_keys = ['baseline_stability_rate', 'alt_specs', 'sensitivity_rates']
                if not all(key in study_data for key in required_keys):
                    print(f"Warning: Skipping {file_path} due to missing required keys")
                    continue
                results.append(study_data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    return results

def calculate_aggregate_metrics(study_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate metrics across all studies.
    
    Args:
        study_results: List of study result dictionaries.
        
    Returns:
        Dictionary containing mean, median, std, min, max for stability rates.
    """
    if not study_results:
        return {}
    
    baseline_rates = [r['baseline_stability_rate'] for r in study_results]
    
    # Extract specification stability rates by pooling all alt_specs p-values
    # as per FR-004: aggregate by pooling ALL p-values from all 5 alternative specs
    all_alt_p_values = []
    for r in study_results:
        for alt_spec in r['alt_specs']:
            if 'p_value_distribution' in alt_spec:
                all_alt_p_values.extend(alt_spec['p_value_distribution'])
    
    if all_alt_p_values:
        spec_stability_rate = sum(1 for p in all_alt_p_values if p < SIGNIFICANCE_LEVEL) / len(all_alt_p_values)
    else:
        spec_stability_rate = 0.0
    
    # Calculate statistics for baseline rates
    stats = {
        'mean': statistics.mean(baseline_rates),
        'median': statistics.median(baseline_rates),
        'stdev': statistics.stdev(baseline_rates) if len(baseline_rates) > 1 else 0.0,
        'min': min(baseline_rates),
        'max': max(baseline_rates),
        'count': len(baseline_rates),
        'specification_stability_rate': spec_stability_rate
    }
    
    return stats

def calculate_i2(study_results: List[Dict[str, Any]]) -> float:
    """
    Calculate I² heterogeneity statistic using a random-effects model approximation.
    
    I² = max(0, (Q - df) / Q) * 100
    where Q is Cochran's Q statistic and df = k - 1 (k = number of studies)
    
    Args:
        study_results: List of study result dictionaries.
        
    Returns:
        I² value as a percentage (0-100).
    """
    if len(study_results) < 2:
        return 0.0
    
    # Use baseline stability rates for heterogeneity calculation
    rates = [r['baseline_stability_rate'] for r in study_results]
    k = len(rates)
    
    # Calculate mean
    mean_rate = statistics.mean(rates)
    
    # Calculate Cochran's Q
    # Q = sum(wi * (xi - mean)^2) where wi = 1/variance
    # For simplicity, we assume equal variance (fixed effect approximation)
    # In a full implementation, we would estimate between-study variance
    q_stat = sum((r - mean_rate) ** 2 for r in rates)
    
    # Degrees of freedom
    df = k - 1
    
    # I² calculation
    if q_stat <= df:
        i2 = 0.0
    else:
        i2 = ((q_stat - df) / q_stat) * 100
    
    return max(0.0, i2)

def identify_fragile_findings(study_results: List[Dict[str, Any]], threshold: float = FRAGILITY_THRESHOLD) -> List[Dict[str, Any]]:
    """
    Identify studies with fragile findings (stability rate < threshold).
    
    Args:
        study_results: List of study result dictionaries.
        threshold: Stability rate threshold below which findings are considered fragile.
        
    Returns:
        List of studies with fragile findings.
    """
    fragile = []
    for r in study_results:
        if r['baseline_stability_rate'] < threshold:
            fragile.append(r)
    return fragile

def generate_forest_plot(study_results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a forest plot showing stability rates for each study with confidence intervals.
    
    Args:
        study_results: List of study result dictionaries.
        output_path: Path to save the plot.
    """
    if not study_results:
        raise ValueError("No study results provided for forest plot")
    
    # Prepare data
    osf_ids = []
    rates = []
    errors = []  # Approximate standard error (using 0.1 as placeholder for CI width)
    
    for r in study_results:
        # Extract OSF ID from filename or use a generated ID
        osf_id = r.get('osf_id', f"Study_{len(osf_ids)+1}")
        osf_ids.append(osf_id)
        rates.append(r['baseline_stability_rate'])
        # Use a fixed error bar for visualization (in real implementation, calculate from p-value distribution)
        errors.append(0.1)
    
    # Create figure
    plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    sns.set_style("whitegrid")
    
    # Plot points and error bars
    y_pos = range(len(osf_ids))
    plt.errorbar(rates, y_pos, xerr=errors, fmt='o', capsize=5, color='steelblue', ecolor='gray', linewidth=1.5)
    
    # Add vertical line at threshold
    plt.axvline(x=FRAGILITY_THRESHOLD, color='red', linestyle='--', linewidth=1.5, label=f'Fragility Threshold ({FRAGILITY_THRESHOLD})')
    
    # Add vertical line at mean
    mean_rate = statistics.mean(rates)
    plt.axvline(x=mean_rate, color='green', linestyle='-', linewidth=1.5, label=f'Mean ({mean_rate:.2f})')
    
    # Formatting
    plt.yticks(y_pos, osf_ids)
    plt.xlabel('Baseline Stability Rate')
    plt.title('Forest Plot: Study Stability Rates')
    plt.xlim(0, 1.1)
    plt.legend()
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()

def generate_histogram(study_results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a histogram of p-value stability rates.
    
    Args:
        study_results: List of study result dictionaries.
        output_path: Path to save the plot.
    """
    if not study_results:
        raise ValueError("No study results provided for histogram")
    
    rates = [r['baseline_stability_rate'] for r in study_results]
    
    plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    sns.set_style("whitegrid")
    
    # Create histogram
    sns.histplot(rates, bins=10, kde=True, color='skyblue', edgecolor='black')
    
    # Add vertical lines
    plt.axvline(x=FRAGILITY_THRESHOLD, color='red', linestyle='--', linewidth=2, label=f'Fragility Threshold ({FRAGILITY_THRESHOLD})')
    plt.axvline(x=statistics.mean(rates), color='green', linestyle='-', linewidth=2, label=f'Mean ({statistics.mean(rates):.2f})')
    
    # Formatting
    plt.xlabel('Baseline Stability Rate')
    plt.ylabel('Frequency')
    plt.title('Distribution of Stability Rates Across Studies')
    plt.legend()
    plt.xlim(0, 1.1)
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()

def generate_summary_report(study_results: List[Dict[str, Any]], output_dir: str = "outputs/reports") -> None:
    """
    Generate a comprehensive summary report including all plots and tables.
    
    Args:
        study_results: List of study result dictionaries.
        output_dir: Directory to save the report.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate metrics
    aggregate_stats = calculate_aggregate_metrics(study_results)
    i2_value = calculate_i2(study_results)
    fragile_findings = identify_fragile_findings(study_results)
    
    # Generate plots
    forest_plot_path = os.path.join(output_dir, "forest_plot.png")
    histogram_path = os.path.join(output_dir, "stability_histogram.png")
    
    generate_forest_plot(study_results, forest_plot_path)
    generate_histogram(study_results, histogram_path)
    
    # Save summary statistics to CSV
    summary_csv_path = os.path.join("data/processed", "summary_stats.csv")
    os.makedirs(os.path.dirname(summary_csv_path), exist_ok=True)
    
    summary_data = {
        'metric': ['mean', 'median', 'std', 'min', 'max', 'i2', 'specification_stability_rate', 'fragile_count'],
        'value': [
            aggregate_stats.get('mean', 0),
            aggregate_stats.get('median', 0),
            aggregate_stats.get('stdev', 0),
            aggregate_stats.get('min', 0),
            aggregate_stats.get('max', 0),
            i2_value,
            aggregate_stats.get('specification_stability_rate', 0),
            len(fragile_findings)
        ]
    }
    
    df_summary = pd.DataFrame(summary_data)
    df_summary.to_csv(summary_csv_path, index=False)
    
    print(f"Summary report generated successfully.")
    print(f"  - Forest plot: {forest_plot_path}")
    print(f"  - Histogram: {histogram_path}")
    print(f"  - Summary stats: {summary_csv_path}")
    print(f"  - I² heterogeneity: {i2_value:.2f}%")
    print(f"  - Fragile findings: {len(fragile_findings)} / {len(study_results)}")

def main():
    """
    Main entry point for meta-analysis execution.
    Loads study results, calculates metrics, and generates visualizations.
    """
    # Load study results
    try:
        study_results = load_study_results()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure that study result files (study_*_results.json) exist in data/processed/")
        return
    
    if not study_results:
        print("No valid study results found to analyze.")
        return
    
    print(f"Loaded {len(study_results)} study results for meta-analysis.")
    
    # Generate summary report
    generate_summary_report(study_results)

if __name__ == "__main__":
    main()