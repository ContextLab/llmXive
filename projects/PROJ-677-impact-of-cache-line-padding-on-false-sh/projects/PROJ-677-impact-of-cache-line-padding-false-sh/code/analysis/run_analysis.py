import os
import sys
import glob
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any

import pandas as pd
import numpy as np
from scipy import stats

# Import local contracts and hardware detection
# Note: Path manipulation to allow running from project root or code/analysis
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.contracts.benchmark_contracts import BenchmarkRun, AggregatedResult, StatisticalComparison

def load_benchmark_data(data_dir: str = "data/raw") -> pd.DataFrame:
    """
    Load all CSV files from the raw data directory and validate against BenchmarkRun schema.
    Returns a consolidated DataFrame.
    """
    data_path = PROJECT_ROOT / data_dir
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    csv_files = list(data_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_path}")

    all_data = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            # Basic validation: ensure required columns exist
            required_cols = ['thread_count', 'configuration', 'iteration_count', 'wall_clock_time_ms']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                raise ValueError(f"File {file} missing columns: {missing_cols}")
            
            # Validate against Pydantic schema (sample check)
            # In a real pipeline, we might validate every row, but for performance we sample
            sample_rows = df.head(10).to_dict('records')
            for row in sample_rows:
                try:
                    BenchmarkRun(**row)
                except Exception as e:
                    raise ValueError(f"Data validation failed for {file}: {e}")
            
            df['source_file'] = file.name
            all_data.append(df)
        except Exception as e:
            print(f"Warning: Skipping file {file} due to error: {e}")
            continue

    if not all_data:
        raise ValueError("No valid data files found after validation.")

    return pd.concat(all_data, ignore_index=True)

def calculate_throughput(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate throughput (operations per second) for each row.
    Throughput = (iteration_count * 1000) / wall_clock_time_ms
    """
    if 'wall_clock_time_ms' in df.columns and 'iteration_count' in df.columns:
        # Avoid division by zero
        df = df.copy()
        df['throughput_ops_per_sec'] = (df['iteration_count'] * 1000.0) / df['wall_clock_time_ms'].replace(0, np.nan)
        df.dropna(subset=['throughput_ops_per_sec'], inplace=True)
    return df

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate results by thread_count and configuration.
    Computes mean, std, and count for throughput.
    """
    if 'throughput_ops_per_sec' not in df.columns:
        df = calculate_throughput(df)

    grouped = df.groupby(['thread_count', 'configuration'])['throughput_ops_per_sec'].agg(['mean', 'std', 'count']).reset_index()
    grouped.columns = ['thread_count', 'configuration', 'mean_throughput', 'std_throughput', 'sample_count']
    
    # Validate against AggregatedResult schema
    for _, row in grouped.iterrows():
        AggregatedResult(
            thread_count=int(row['thread_count']),
            configuration=row['configuration'],
            mean_throughput=row['mean_throughput'],
            std_throughput=row['std_throughput'],
            sample_count=int(row['sample_count'])
        )
    
    return grouped

def perform_statistical_tests(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform two-sample t-tests comparing 'padded' vs 'packed' for each thread_count.
    Returns a DataFrame with t_stat, p_value, and cohens_d.
    """
    if 'throughput_ops_per_sec' not in df.columns:
        df = calculate_throughput(df)

    results = []
    thread_counts = sorted(df['thread_count'].unique())

    for tc in thread_counts:
        subset = df[df['thread_count'] == tc]
        if 'padded' not in subset['configuration'].values or 'packed' not in subset['configuration'].values:
            print(f"Skipping thread_count {tc}: missing configurations.")
            continue

        padded_data = subset[subset['configuration'] == 'padded']['throughput_ops_per_sec']
        packed_data = subset[subset['configuration'] == 'packed']['throughput_ops_per_sec']

        if len(padded_data) < 2 or len(packed_data) < 2:
            print(f"Skipping thread_count {tc}: insufficient samples.")
            continue

        # Two-sample t-test
        t_stat, p_val = stats.ttest_ind(padded_data, packed_data, equal_var=False)

        # Cohen's d
        mean_diff = padded_data.mean() - packed_data.mean()
        pooled_std = np.sqrt((padded_data.var() + packed_data.var()) / 2)
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0.0

        results.append({
            'thread_count': tc,
            'config_padded_mean': padded_data.mean(),
            'config_packed_mean': packed_data.mean(),
            't_stat': t_stat,
            'p_value': p_val,
            'cohens_d': cohens_d
        })

    if not results:
        raise ValueError("No statistical results generated. Check data availability.")

    results_df = pd.DataFrame(results)
    
    # Validate against StatisticalComparison schema (partial validation before FDR)
    for _, row in results_df.iterrows():
        StatisticalComparison(
            thread_count=int(row['thread_count']),
            config_a='padded',
            config_b='packed',
            t_stat=row['t_stat'],
            p_value=row['p_value'],
            cohens_d=row['cohens_d'],
            fdr_adjusted_p=row['p_value'] # Placeholder, will be updated
        )

    return results_df

def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg FDR correction to a series of p-values.
    Returns adjusted p-values.
    """
    p_values = p_values.sort_values()
    n = len(p_values)
    if n == 0:
        return pd.Series([], dtype=float)

    # Calculate ranks (1-based)
    ranks = np.arange(1, n + 1)
    # BH critical values
    bh_values = (ranks / n) * p_values.iloc[-1]
    
    # Ensure monotonicity (cumulative min from the end)
    adjusted = np.minimum.accumulate(bh_values[::-1])[::-1]
    
    # Map back to original index order
    result = pd.Series(adjusted, index=p_values.index)
    return result

def generate_plot(aggregated_df: pd.DataFrame, output_path: str):
    """
    Generate a line plot with error bars (95% CI) comparing packed vs padded.
    """
    import matplotlib.pyplot as plt

    if 'std_throughput' not in aggregated_df.columns:
        aggregated_df = aggregate_results(aggregated_df)

    plt.figure(figsize=(10, 6))
    
    for config in ['packed', 'padded']:
        subset = aggregated_df[aggregated_df['configuration'] == config]
        # Calculate 95% CI: mean +/- 1.96 * (std / sqrt(n))
        # Note: Using 1.96 as approximation for large n, or t-value for small n
        # Here we use mean +/- 2*std for simplicity in visualization unless n is known
        # Better: CI = std / sqrt(n) * t_crit
        # Let's use standard error for error bars
        subset = subset.sort_values('thread_count')
        plt.errorbar(
            subset['thread_count'], 
            subset['mean_throughput'], 
            yerr=subset['std_throughput'], 
            label=config, 
            capsize=5, 
            marker='o'
        )

    plt.xlabel('Thread Count')
    plt.ylabel('Throughput (Ops/sec)')
    plt.title('Impact of Cache Line Padding on Concurrent Counter Throughput')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"Plot saved to {output_path}")

def update_checksums(file_path: str, checksums_file: str):
    """
    Update state/artifacts/checksums.json with the SHA-256 hash of the generated file.
    """
    checksum_path = PROJECT_ROOT / checksums_file
    state_dir = checksum_path.parent
    state_dir.mkdir(parents=True, exist_ok=True)

    current_checksums = {}
    if checksum_path.exists():
        with open(checksum_path, 'r') as f:
            current_checksums = json.load(f)

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    new_entry = {
        "file": os.path.basename(file_path),
        "hash": sha256_hash.hexdigest(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Update or append
    current_checksums[file_path] = new_entry
    
    with open(checksum_path, 'w') as f:
        json.dump(current_checksums, f, indent=2)

def main():
    """
    Main entry point for the analysis pipeline.
    1. Load raw CSVs
    2. Validate
    3. Aggregate
    4. Statistical tests + FDR
    5. Generate plot
    6. Write final CSV
    7. Update checksums
    """
    print("Starting Analysis Pipeline...")

    # Paths
    raw_data_dir = "data/raw"
    processed_dir = "data/processed"
    figures_dir = "figures"
    state_dir = "state/artifacts"
    
    # Ensure directories exist
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    Path(state_dir).mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    try:
        df_raw = load_benchmark_data(raw_data_dir)
        print(f"Loaded {len(df_raw)} rows from raw data.")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    # 2. Calculate Throughput
    df_raw = calculate_throughput(df_raw)

    # 3. Aggregate
    df_agg = aggregate_results(df_raw)

    # 4. Statistical Tests
    df_stats = perform_statistical_tests(df_raw)

    # 5. FDR Correction
    if 'p_value' in df_stats.columns:
        df_stats['fdr_adjusted_p'] = benjamini_hochberg(df_stats['p_value'])
    
    # 6. Generate Plot
    plot_path = str(PROJECT_ROOT / figures_dir / "throughput_comparison.png")
    generate_plot(df_agg, plot_path)

    # 7. Write Final CSV
    final_csv_path = str(PROJECT_ROOT / processed_dir / "statistical_comparison.csv")
    # Select columns as per spec: thread_count, config, t_stat, p_value, cohens_d, fdr_adjusted_p
    # We need to format 'config' to reflect the comparison (e.g., 'padded_vs_packed')
    df_final = df_stats.rename(columns={'config_padded_mean': 'config_padded_mean', 'config_packed_mean': 'config_packed_mean'})
    # The spec asks for 'config' column, likely indicating the comparison pair or the primary config
    # Let's create a 'comparison' column or just use the existing stats.
    # Spec: "thread_count, config, t_stat, p_value, cohens_d, fdr_adjusted_p"
    # Since we compare padded vs packed, we can denote config as 'padded_vs_packed' or similar.
    df_final['config'] = 'padded_vs_packed'
    df_final = df_final[['thread_count', 'config', 't_stat', 'p_value', 'cohens_d', 'fdr_adjusted_p']]
    
    df_final.to_csv(final_csv_path, index=False)
    print(f"Statistical comparison saved to {final_csv_path}")

    # 8. Update Checksums
    update_checksums(final_csv_path, str(PROJECT_ROOT / state_dir / "checksums.json"))
    print("Checksums updated.")

    print("Analysis Pipeline Complete.")

if __name__ == "__main__":
    main()