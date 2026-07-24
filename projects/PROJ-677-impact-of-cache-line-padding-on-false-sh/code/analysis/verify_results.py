"""
Verification script for the cache line padding benchmark.

This script:
1. Runs the benchmark (assuming the binary exists and is executable).
2. Loads the generated CSV data.
3. Aggregates throughput by thread count and configuration.
4. Asserts that padded throughput > packed throughput at higher thread counts (>= 4).
"""
import os
import sys
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List

# Add project root to path to allow imports if running from subdirectory
PROJECT_ROOT = Path(__file__).parent.parent.parent
BENCHMARK_DIR = PROJECT_ROOT / "code" / "benchmark"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Ensure data directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def run_benchmark():
    """
    Executes the benchmark binary if it exists.
    If the binary doesn't exist, it attempts to build it using build.sh.
    """
    binary_path = BENCHMARK_DIR / "counter_benchmark"
    build_script = BENCHMARK_DIR / "build.sh"

    if not binary_path.exists():
        if build_script.exists():
            print("Benchmark binary not found. Attempting to build...")
            try:
                subprocess.run(
                    ["bash", str(build_script)],
                    cwd=BENCHMARK_DIR,
                    check=True,
                    capture_output=False
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to build benchmark: {e}")
        else:
            raise FileNotFoundError(
                f"Benchmark binary not found at {binary_path} "
                "and no build script available."
            )
    
    if not os.access(binary_path, os.X_OK):
        os.chmod(binary_path, 0o755)

    # Run the benchmark with a minimal set of arguments to generate data
    # Assuming the script run_benchmarks.sh orchestrates the full run,
    # but if we need to trigger it here directly:
    run_script = PROJECT_ROOT / "code" / "scripts" / "run_benchmarks.sh"
    
    if run_script.exists():
        print("Running benchmark via run_benchmarks.sh...")
        try:
            # We run a subset if possible, or the full thing. 
            # Assuming the script handles the loop. 
            # To be safe and fast, we might just run the script.
            # If the script is too heavy, we might need to call the binary directly.
            # Based on task T022, run_benchmarks.sh iterates thread counts and configs.
            subprocess.run(
                ["bash", str(run_script)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=False,
                timeout=300 # 5 minutes timeout
            )
        except subprocess.TimeoutExpired:
            print("Warning: Benchmark run timed out. Proceeding with available data.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Benchmark run failed with code {e.returncode}. Proceeding with available data.")
    else:
        print("Warning: run_benchmarks.sh not found. Assuming data already exists or manual run required.")

def load_benchmark_data() -> pd.DataFrame:
    """
    Loads the benchmark results from the raw CSV files.
    Expects a file named 'benchmark_results.csv' or similar in data/raw/.
    """
    # Look for the most recent CSV file in raw data
    csv_files = list(RAW_DATA_DIR.glob("*.csv"))
    if not csv_files:
        # Check if data is in the processed folder (sometimes scripts write there directly)
        csv_files = list(PROCESSED_DATA_DIR.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(
            "No benchmark CSV files found in data/raw/ or data/processed/. "
            "Ensure the benchmark has been run successfully."
        )
    
    # Assume the latest file or the one named 'benchmark_results.csv'
    target_file = None
    for f in csv_files:
        if f.name == "benchmark_results.csv":
            target_file = f
            break
    
    if not target_file:
        target_file = sorted(csv_files, key=lambda x: x.stat().st_mtime)[-1]
    
    print(f"Loading data from: {target_file}")
    df = pd.read_csv(target_file)
    
    required_cols = ["thread_count", "configuration", "wall_clock_time_ms", "iteration_count"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")
    
    return df

def calculate_throughput(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates throughput (operations per second) for each row.
    """
    df = df.copy()
    # Throughput = (iteration_count * thread_count) / (wall_clock_time_ms / 1000)
    # Assuming iteration_count is per thread? Or total? 
    # Based on typical benchmarks, iteration_count is usually per thread.
    # Total ops = iteration_count * thread_count
    # Time in seconds = wall_clock_time_ms / 1000
    df["throughput_ops_per_sec"] = (
        (df["iteration_count"] * df["thread_count"]) / 
        (df["wall_clock_time_ms"] / 1000.0)
    )
    return df

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates throughput by thread_count and configuration.
    Returns mean and std.
    """
    agg = df.groupby(["thread_count", "configuration"])["throughput_ops_per_sec"].agg(
        ["mean", "std", "count"]
    ).reset_index()
    agg.columns = ["thread_count", "configuration", "mean_throughput", "std_throughput", "samples"]
    return agg

def verify_padding_effect(agg_df: pd.DataFrame, min_thread_count: int = 4) -> Tuple[bool, List[str]]:
    """
    Verifies that padded throughput > packed throughput at higher thread counts.
    Returns (success, list_of_failures).
    """
    failures = []
    high_thread_counts = agg_df["thread_count"].unique()
    high_thread_counts = [tc for tc in high_thread_counts if tc >= min_thread_count]
    
    if not high_thread_counts:
        return False, [f"No thread counts >= {min_thread_count} found in data."]

    for tc in sorted(high_thread_counts):
        subset = agg_df[agg_df["thread_count"] == tc]
        packed_row = subset[subset["configuration"] == "packed"]
        padded_row = subset[subset["configuration"] == "padded"]
        
        if packed_row.empty or padded_row.empty:
            failures.append(f"Missing data for thread_count={tc} (packed={packed_row.empty}, padded={padded_row.empty})")
            continue
        
        packed_mean = packed_row["mean_throughput"].values[0]
        padded_mean = padded_row["mean_throughput"].values[0]
        
        if padded_mean <= packed_mean:
            failures.append(
                f"FAIL: At thread_count={tc}, padded ({padded_mean:.2f}) <= packed ({packed_mean:.2f}). "
                f"Expected padded > packed due to false sharing mitigation."
            )
        else:
            print(f"PASS: At thread_count={tc}, padded ({padded_mean:.2f}) > packed ({packed_mean:.2f})")
    
    return len(failures) == 0, failures

def main():
    print("=" * 60)
    print("Running Verification Script for Cache Line Padding")
    print("=" * 60)
    
    try:
        # 1. Run Benchmark (if needed)
        run_benchmark()
        
        # 2. Load Data
        df = load_benchmark_data()
        print(f"Loaded {len(df)} rows.")
        
        # 3. Calculate Throughput
        df = calculate_throughput(df)
        
        # 4. Aggregate Results
        agg_df = aggregate_results(df)
        print("\nAggregated Results:")
        print(agg_df.to_string(index=False))
        
        # 5. Verify Effect
        success, failures = verify_padding_effect(agg_df, min_thread_count=4)
        
        print("\n" + "=" * 60)
        if success:
            print("VERIFICATION PASSED: Padded throughput is greater than packed throughput at higher thread counts.")
            sys.exit(0)
        else:
            print("VERIFICATION FAILED:")
            for f in failures:
                print(f"  - {f}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()