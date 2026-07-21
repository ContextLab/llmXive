"""
Streaming Execution Test Runner (Task T064)

This script verifies that the pipeline can process large datasets using
chunked/streamed loading, ensuring memory usage stays within the 7GB limit
and that the filtered output is correctly generated via accumulation.

Dependencies:
- T058 (RAM Pre-check)
- T059 (Streaming Enablement)
- T070 (Large Proxy Generator)
"""

import os
import sys
import json
import time
import argparse
import tracemalloc
import pandas as pd
import numpy as np
from pathlib import Path

# Import local project modules
from config import get_config, load_config
from ingest import load_streamed_dataset, detect_outliers_iqr, filter_outliers, save_variable_metrics
from main import estimate_ram_usage, determine_compute_strategy

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
METADATA_DIR = DATA_DIR / "metadata"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

def get_memory_peak_gb():
    """Return the peak memory usage in GB."""
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 ** 3)

def run_streaming_execution_test(proxy_path=None, chunk_size=1000, max_memory_gb=7.0):
    """
    Executes the streaming test logic.

    Args:
        proxy_path: Path to the large proxy dataset (from T070). If None,
                    attempts to find 'large_proxy.csv' in data/raw.
        chunk_size: Number of rows to process per chunk.
        max_memory_gb: Maximum allowed memory in GB.

    Returns:
        dict: Report containing status, memory peaks, and chunk counts.
    """
    report = {
        "task_id": "T064",
        "status": "PENDING",
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "memory_peak_gb": 0.0,
        "chunks_processed": 0,
        "total_rows_processed": 0,
        "output_file": None,
        "error": None
    }

    # 1. Locate Input Data
    if proxy_path is None:
        proxy_path = DATA_DIR / "raw" / "large_proxy.csv"

    if not os.path.exists(proxy_path):
        report["status"] = "FAILED"
        report["error"] = f"Input file not found: {proxy_path}. Run T070 first."
        return report

    print(f"[*] Starting Streaming Execution Test with: {proxy_path}")
    print(f"[*] Chunk size: {chunk_size}, Max Memory Limit: {max_memory_gb} GB")

    # 2. Start Memory Tracing
    tracemalloc.start()
    start_time = time.time()

    try:
        # 3. Load and Stream Data
        # We use pandas read_csv with chunksize to simulate streaming
        # This ensures we don't load the whole file into RAM at once
        reader = pd.read_csv(proxy_path, chunksize=chunk_size)

        all_filtered_chunks = []
        chunk_count = 0
        total_rows = 0

        for chunk_num, chunk_df in enumerate(reader):
            chunk_count += 1
            current_mem = get_memory_peak_gb()

            # Safety check during processing
            if current_mem > max_memory_gb:
                raise MemoryError(f"Memory limit exceeded at chunk {chunk_num}: {current_mem:.2f} GB > {max_memory_gb} GB")

            # 4. Process Chunk: Detect and Filter Outliers
            # Assuming 'value' or specific columns exist; generic approach for schema
            # We assume the schema defines numeric columns for outliers
            # For this test, we assume the proxy has 'subject_id', 'taxa_1', 'sleep_duration', etc.
            # We filter based on numeric columns (excluding ID)
            numeric_cols = chunk_df.select_dtypes(include=[np.number]).columns.tolist()
            id_cols = [c for c in chunk_df.columns if 'id' in c.lower() or 'subject' in c.lower()]
            filter_cols = [c for c in numeric_cols if c not in id_cols]

            if filter_cols:
                # Apply outlier detection (IQR)
                mask = pd.Series([True] * len(chunk_df), index=chunk_df.index)
                for col in filter_cols:
                    Q1 = chunk_df[col].quantile(0.25)
                    Q3 = chunk_df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower = Q1 - 1.5 * IQR
                    upper = Q3 + 1.5 * IQR
                    col_mask = (chunk_df[col] >= lower) & (chunk_df[col] <= upper)
                    mask &= col_mask

                filtered_chunk = chunk_df[mask]
            else:
                filtered_chunk = chunk_df

            all_filtered_chunks.append(filtered_chunk)
            total_rows += len(filtered_chunk)

            # Log progress
            if chunk_count % 100 == 0:
                print(f"    Processed {chunk_count} chunks, {total_rows} rows. Mem: {current_mem:.2f} GB")

        # 5. Accumulate and Save
        if all_filtered_chunks:
            final_df = pd.concat(all_filtered_chunks, ignore_index=True)
        else:
            # If all rows were outliers (unlikely), create empty DF with schema
            final_df = pd.DataFrame(columns=pd.read_csv(proxy_path, nrows=0).columns)

        output_path = PROCESSED_DIR / "filtered_data.parquet"
        final_df.to_parquet(output_path, index=False)
        report["output_file"] = str(output_path)
        report["total_rows_processed"] = total_rows

        # 6. Calculate Metrics
        end_time = time.time()
        report["duration_seconds"] = end_time - start_time
        report["chunks_processed"] = chunk_count

        current, peak = tracemalloc.get_traced_memory()
        report["memory_peak_gb"] = round(peak / (1024 ** 3), 4)

        # 7. Verify Constraints
        if report["memory_peak_gb"] <= max_memory_gb:
            report["status"] = "PASSED"
            print(f"[OK] Memory peak: {report['memory_peak_gb']:.2f} GB (Limit: {max_memory_gb} GB)")
        else:
            report["status"] = "FAILED"
            report["error"] = f"Memory limit exceeded: {report['memory_peak_gb']:.2f} GB"

    except Exception as e:
        report["status"] = "FAILED"
        report["error"] = str(e)
        print(f"[ERROR] Streaming test failed: {e}")
        raise
    finally:
        tracemalloc.stop()

    report["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return report

def main():
    parser = argparse.ArgumentParser(description="T064: Streaming Execution Test")
    parser.add_argument("--proxy", type=str, default=None, help="Path to large proxy CSV (T070 output)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Rows per chunk")
    parser.add_argument("--max-mem", type=float, default=7.0, help="Max memory GB")
    args = parser.parse_args()

    print("=" * 60)
    print("Running T064: Streaming Execution Test")
    print("=" * 60)

    try:
        report = run_streaming_execution_test(
            proxy_path=args.proxy,
            chunk_size=args.chunk_size,
            max_memory_gb=args.max_mem
        )

        # Save Report
        report_path = RESULTS_DIR / "streaming_execution_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"[INFO] Report saved to: {report_path}")
        print(f"[INFO] Output saved to: {report['output_file']}")
        print(f"[RESULT] Status: {report['status']}")

        if report["status"] != "PASSED":
            sys.exit(1)

    except Exception as e:
        print(f"[FATAL] Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
