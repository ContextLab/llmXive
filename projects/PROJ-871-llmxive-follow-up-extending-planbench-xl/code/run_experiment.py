import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.config import get_path, ensure_dirs_exist, set_deterministic_seed
from dataset.loader import download_planbench_xl
from dataset.injector import load_raw_planbench_xl, inject_failures, save_injected_data
from dataset.indexer import load_injected_data, extract_failure_signatures, save_index
from run_baseline import run_baseline_experiment
from run_augmented import run_augmented_experiment
from analysis.log_parser import get_aggregated_counts
from analysis.stats import calculate_statistical_significance
from analysis.report import generate_report, save_report

def main():
    """Main entry point for the full experiment pipeline."""
    set_deterministic_seed(42)
    start_time = time.time()
    
    # Step 1: Download dataset
    print("Step 1: Downloading PlanBench-XL...")
    try:
        raw_file = download_planbench_xl()
        print(f"Dataset downloaded to: {raw_file}")
    except Exception as e:
        print(f"Failed to download dataset: {e}")
        return
    
    # Step 2: Inject failures
    print("Step 2: Injecting synthetic failures...")
    raw_data = load_raw_planbench_xl()
    injected_data = inject_failures(raw_data, num_failures=50, seed=42)
    injected_file = save_injected_data(injected_data)
    print(f"Injected data saved to: {injected_file}")
    
    # Step 3: Build failure index
    print("Step 3: Building failure signature index...")
    injected_for_index = load_injected_data()
    signatures = extract_failure_signatures(injected_for_index)
    index_file = save_index(signatures)
    print(f"Failure index saved to: {index_file}")
    
    # Step 4: Run baseline
    print("Step 4: Running baseline agent...")
    baseline_log = run_baseline_experiment(injected_data)
    print(f"Baseline log saved to: {baseline_log}")
    
    # Step 5: Run augmented
    print("Step 5: Running augmented agent...")
    augmented_log = run_augmented_experiment(injected_data)
    print(f"Augmented log saved to: {augmented_log}")
    
    # Step 6: Analyze
    print("Step 6: Performing statistical analysis...")
    report = generate_report(baseline_log, augmented_log)
    report_file = save_report(report)
    print(f"Final report saved to: {report_file}")
    
    # Step 7: Measure time
    total_time = time.time() - start_time
    print(f"Total experiment time: {total_time:.2f} seconds")
    
    # Check against 6-hour limit
    limit_seconds = 6 * 3600
    if total_time > limit_seconds:
        print(f"WARNING: Experiment exceeded 6-hour limit!")
    else:
        print("Experiment completed within time limit.")

if __name__ == "__main__":
    main()
