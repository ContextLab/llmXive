#!/usr/bin/env python3
"""
Analysis script for benchmark results.
Loads CSV data, performs statistical tests, and generates visualizations.
"""
import os
import sys
import glob
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def load_benchmark_data(csv_path: str) -> pd.DataFrame:
    """Load benchmark results from CSV file."""
    df = pd.read_csv(csv_path)
    return df

def calculate_throughput(df: pd.DataFrame, iterations: int) -> pd.DataFrame:
    """Calculate throughput (operations per second) from time data."""
    df['throughput'] = (iterations * df['thread_count']) / (df['wall_clock_time_ms'] / 1000.0)
    return df

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate results by thread_count and configuration."""
    return df.groupby(['thread_count', 'configuration']).agg({
        'throughput': ['mean', 'std', 'count']
    }).reset_index()

def perform_statistical_tests(packed_times, padded_times):
    """Perform two-sample t-test between packed and padded configurations."""
    t_stat, p_value = stats.ttest_ind(packed_times, padded_times)
    return t_stat, p_value

def benjamini_hochberg(p_values):
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    corrected_p_values = sorted_p_values * n / ranks
    corrected_p_values = np.minimum(corrected_p_values, 1.0)
    
    # Restore original order
    result = np.zeros(n)
    result[sorted_indices] = corrected_p_values
    return result

def calculate_cohens_d(group1, group2):
    """Calculate Cohen's d effect size."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1), np.std(group2)
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    return (mean1 - mean2) / pooled_std

def generate_plot(df: pd.DataFrame, output_path: str):
    """Generate line plot with confidence intervals."""
    plt.figure(figsize=(10, 6))
    
    for config in df['configuration'].unique():
        subset = df[df['configuration'] == config]
        plt.errorbar(
            subset['thread_count'], 
            subset['throughput_mean'], 
            yerr=subset['throughput_std'], 
            label=config.capitalize(),
            capsize=5
        )
    
    plt.xlabel('Thread Count')
    plt.ylabel('Throughput (operations/sec)')
    plt.title('Impact of Cache Line Padding on False Sharing')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    """Main entry point for analysis."""
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / 'data' / 'benchmark_results.csv'
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)

    # Load and process data
    df = load_benchmark_data(str(csv_path))
    df = calculate_throughput(df, iterations=1000000)
    aggregated = aggregate_results(df)

    # Perform statistical tests
    results = []
    p_values = []
    
    for thread_count in df['thread_count'].unique():
        packed = df[(df['thread_count'] == thread_count) & (df['configuration'] == 'packed')]['throughput']
        padded = df[(df['thread_count'] == thread_count) & (df['configuration'] == 'padded')]['throughput']
        
        t_stat, p_val = perform_statistical_tests(packed, padded)
        cohens_d = calculate_cohens_d(packed, padded)
        
        results.append({
            'thread_count': thread_count,
            't_stat': t_stat,
            'p_value': p_val,
            'cohens_d': cohens_d
        })
        p_values.append(p_val)

    # Apply FDR correction
    fdr_corrected = benjamini_hochberg(p_values)
    for i, row in enumerate(results):
        row['fdr_adjusted_p'] = fdr_corrected[i]

    # Write results
    results_df = pd.DataFrame(results)
    output_csv = project_root / 'data' / 'processed' / 'statistical_comparison.csv'
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_csv, index=False)
    print(f"Statistical results written to {output_csv}")

    # Generate plot
    plot_path = project_root / 'figures' / 'comparison_plot.png'
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    generate_plot(aggregated, str(plot_path))
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    main()
