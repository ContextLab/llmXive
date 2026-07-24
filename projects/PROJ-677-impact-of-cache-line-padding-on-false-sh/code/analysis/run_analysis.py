import os
import sys
import glob
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
from scipy import stats

# Ensure matplotlib uses a non-interactive backend before importing pyplot
# This is crucial for CI/CD environments without a display

def load_benchmark_data(data_dir: str) -> pd.DataFrame:
    """
    Load all CSV benchmark results from the specified directory.
    Expects files matching pattern 'results_*.csv' or similar.
    """
    data_path = Path(data_dir)
    csv_files = list(data_path.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    
    dfs = []
    for file in csv_files:
        # Skip statistical comparison file if it exists in the raw folder
        if "statistical_comparison" in file.name:
            continue
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not read {file}: {e}", file=sys.stderr)
    
    if not dfs:
        raise ValueError("No valid CSV data files could be loaded.")
    
    return pd.concat(dfs, ignore_index=True)

def calculate_throughput(df: pd.DataFrame, total_increments: int = 1000000) -> pd.DataFrame:
    """
    Calculate throughput (increments per second) from wall clock time.
    Assumes 'wall_clock_time_ms' column exists.
    """
    if 'wall_clock_time_ms' not in df.columns:
        raise ValueError("Input DataFrame missing 'wall_clock_time_ms' column")
    
    # Convert ms to seconds
    df['throughput'] = (total_increments / (df['wall_clock_time_ms'] / 1000.0))
    return df

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate results by thread_count and configuration.
    Computes mean, std, and count for throughput.
    """
    if 'thread_count' not in df.columns or 'configuration' not in df.columns or 'throughput' not in df.columns:
        raise ValueError("Input DataFrame missing required columns: thread_count, configuration, throughput")
    
    agg_df = df.groupby(['thread_count', 'configuration'])['throughput'].agg(['mean', 'std', 'count']).reset_index()
    return agg_df

def perform_statistical_tests(agg_df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform two-sample t-tests comparing padded vs packed for each thread count.
    Returns a DataFrame with t-statistic and p-value.
    """
    results = []
    thread_counts = sorted(agg_df['thread_count'].unique())
    
    for tc in thread_counts:
        subset = agg_df[agg_df['thread_count'] == tc]
        packed = subset[subset['configuration'] == 'packed']['throughput']
        padded = subset[subset['configuration'] == 'padded']['throughput']
        
        if len(packed) == 0 or len(padded) == 0:
            continue
        
        t_stat, p_val = stats.ttest_ind(padded, packed, equal_var=False) # Welch's t-test
        results.append({
            'thread_count': tc,
            't_stat': t_stat,
            'p_value': p_val
        })
    
    return pd.DataFrame(results)

def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg FDR correction to a series of p-values.
    """
    n = len(p_values)
    if n == 0:
        return pd.Series([], dtype=float)
    
    sorted_indices = p_values.argsort()
    sorted_pvals = p_values.iloc[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * sorted_pvals.iloc[-1] # This is a simplification, usually alpha * i / m
    # Correct BH implementation:
    # sorted_pvals * (n / ranks)
    # We want the adjusted p-values such that p_adj[i] = min(p_adj[j] for j >= i)
    
    adjusted = np.zeros(n)
    current_min = 1.0
    
    # Iterate backwards
    for i in range(n - 1, -1, -1):
        val = sorted_pvals.iloc[i] * (n / (i + 1))
        current_min = min(current_min, val)
        adjusted[i] = current_min
    
    # Ensure values don't exceed 1.0
    adjusted = np.clip(adjusted, 0, 1)
    
    # Map back to original order
    final_adjusted = pd.Series(0.0, index=p_values.index)
    final_adjusted.iloc[sorted_indices] = adjusted
    
    return final_adjusted

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(ddof=1), group2.std(ddof=1)
    
    if std1 == 0 and std2 == 0:
        return 0.0
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def generate_plot(agg_df: pd.DataFrame, output_path: str):
    """
    Generate a line plot with confidence interval error bars comparing packed vs padded throughput.
    FR-009: Visualization of results.
    """
    if 'thread_count' not in agg_df.columns or 'configuration' not in agg_df.columns or 'mean' not in agg_df.columns or 'std' not in agg_df.columns:
        # Re-aggregate if the input is raw data, assuming 'throughput' exists
        if 'throughput' in agg_df.columns:
            agg_df = aggregate_results(agg_df)
        else:
            raise ValueError("Input DataFrame must have 'mean' and 'std' columns for throughput, or 'throughput' for aggregation.")

    # Ensure we have the right columns after aggregation if passed raw
    if 'mean' not in agg_df.columns:
        agg_df = aggregate_results(agg_df)

    thread_counts = sorted(agg_df['thread_count'].unique())
    configs = sorted(agg_df['configuration'].unique())
    
    if len(thread_counts) == 0:
        raise ValueError("No thread counts found in data.")

    plt.figure(figsize=(10, 6))
    
    for config in configs:
        config_data = agg_df[agg_df['configuration'] == config]
        throughput_means = []
        throughput_stds = []
        
        for tc in thread_counts:
            row = config_data[config_data['thread_count'] == tc]
            if not row.empty:
                throughput_means.append(row['mean'].values[0])
                # Use standard error or std for error bars. FR-009 says confidence interval.
                # 95% CI approx = mean +/- 1.96 * (std / sqrt(n))
                n = row['count'].values[0] if 'count' in row.columns else 1
                std_err = row['std'].values[0] / np.sqrt(n)
                throughput_stds.append(std_err)
            else:
                throughput_means.append(np.nan)
                throughput_stds.append(np.nan)
        
        # Plot
        plt.errorbar(thread_counts, throughput_means, yerr=throughput_stds, 
                     label=config.capitalize(), marker='o', capsize=5, linewidth=2)

    plt.xlabel('Thread Count')
    plt.ylabel('Throughput (increments/sec)')
    plt.title('Impact of Cache Line Padding on Counter Throughput')
    plt.xticks(thread_counts)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot saved to {output_path}")

def main():
    """
    Main entry point for the analysis pipeline.
    """
    # Default paths
    data_dir = "data/raw"
    output_plot = "figures/throughput_comparison.png"
    output_stats = "data/processed/statistical_comparison.csv"
    
    # Check for command line args
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_plot = sys.argv[2]
    if len(sys.argv) > 3:
        output_stats = sys.argv[3]

    try:
        print(f"Loading data from {data_dir}...")
        df = load_benchmark_data(data_dir)
        
        print("Calculating throughput...")
        df = calculate_throughput(df)
        
        print("Aggregating results...")
        agg_df = aggregate_results(df)
        
        print("Performing statistical tests...")
        stats_df = perform_statistical_tests(agg_df)
        
        # Calculate Cohen's d
        cohens_d_list = []
        for tc in stats_df['thread_count']:
            subset = agg_df[agg_df['thread_count'] == tc]
            packed = subset[subset['configuration'] == 'packed']['throughput']
            padded = subset[subset['configuration'] == 'padded']['throughput']
            if len(packed) > 0 and len(padded) > 0:
                d = calculate_cohens_d(padded, packed)
                cohens_d_list.append(d)
            else:
                cohens_d_list.append(np.nan)
        stats_df['cohens_d'] = cohens_d_list

        # Apply BH correction
        if len(stats_df) > 0:
            stats_df['fdr_adjusted_p'] = benjamini_hochberg(stats_df['p_value'])
        else:
            stats_df['fdr_adjusted_p'] = []

        # Save statistical results
        Path(output_stats).parent.mkdir(parents=True, exist_ok=True)
        stats_df.to_csv(output_stats, index=False)
        print(f"Statistical results saved to {output_stats}")
        
        print("Generating plot...")
        generate_plot(agg_df, output_plot)
        
        print("Analysis complete.")
        
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()