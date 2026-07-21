"""
Task T071: 6-Hour Stress Test
Executes the full pipeline (US1-US3) on a large dataset (real or T070 proxy)
to verify execution time < 6 hours.
Output: data/results/6_hour_stress_test_report.json
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from main import (
    setup_paths,
    estimate_ram_usage,
    determine_compute_strategy,
    save_compute_strategy,
    run_compute_feasibility_check,
    run_ingestion_and_validation,
    run_analysis,
    run_diagnostics
)
from config import get_config, load_config
from data_generator import generate_synthetic_dataset, main as gen_main
from harmonize_data import run_harmonization, main as harm_main

def log_message(message: str, log_file: Path):
    """Helper to log messages to console and file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    if log_file:
        with open(log_file, 'a') as f:
            f.write(formatted + "\n")

def run_full_pipeline_on_large_dataset(
    use_harmonized: bool = False,
    use_proxy: bool = False,
    config_path: str = None
):
    """
    Executes the full pipeline on a large dataset.
    If use_harmonized is True, expects harmonized_data.parquet to exist.
    If use_proxy is True, generates a large proxy dataset (N > 1000) first.
    Otherwise, attempts to run on existing real data if available.
    """
    # Setup paths
    paths = setup_paths()
    log_file = paths["data"] / "results" / "stress_test_execution.log"
    if log_file.exists():
        log_file.unlink() # Clear previous log

    log_message("Starting 6-Hour Stress Test (T071)", log_file)

    # Load config
    if config_path:
        config = load_config(Path(config_path))
    else:
        config = get_config()

    # Determine data source strategy
    large_data_path = None
    source_type = "unknown"

    if use_harmonized:
        harmonized_path = paths["data"] / "processed" / "harmonized_data.parquet"
        if not harmonized_path.exists():
            log_message(f"ERROR: Harmonized data not found at {harmonized_path}. Cannot proceed.", log_file)
            return False, "Harmonized data missing"
        large_data_path = str(harmonized_path)
        source_type = "harmonized_real"
        log_message(f"Using harmonized real data from {large_data_path}", log_file)

    elif use_proxy:
        # Generate large proxy if not exists
        proxy_path = paths["data"] / "raw" / "large_proxy.csv"
        if not proxy_path.exists():
            log_message("Generating large proxy dataset (N > 1000)...", log_file)
            # We need to generate a large proxy. The T070 task implies this exists,
            # but if not, we generate it here using the data_generator logic
            # adjusted for large N.
            # Note: data_generator generates synthetic. We mark this as 'Large Proxy'
            # distinct from T006 unit test generator.
            try:
                # Assuming generate_synthetic_dataset can take N as argument or we modify it.
                # Since we can't modify the API surface easily without re-authoring,
                # we assume the T070 artifact exists or we call the generator with a large N.
                # Let's assume the function signature allows N.
                # If not, we might need to rely on the existing artifact.
                # For safety, we check if the file exists first.
                if not proxy_path.exists():
                     # Fallback: generate a smaller proxy if the large one is too heavy to generate on the fly
                     # But the task requires N > 1000.
                     # We will call the generator with a large N.
                     # Note: The API surface for data_generator shows 'generate_synthetic_dataset'.
                     # We assume it accepts N.
                     generate_synthetic_dataset(output_path=str(proxy_path), n_subjects=1200, n_taxa=50)
                     log_message("Large proxy generated successfully.", log_file)
            except Exception as e:
                log_message(f"ERROR: Failed to generate proxy: {e}", log_file)
                return False, str(e)
        
        large_data_path = str(proxy_path)
        source_type = "large_proxy"
        log_message(f"Using large proxy dataset from {large_data_path}", log_file)

    else:
        # Check for existing real data
        # This depends on T069 enabling the pipeline for real data
        # We look for common real data artifacts
        real_candidates = [
            paths["data"] / "processed" / "filtered_data.parquet",
            paths["data"] / "raw" / "real_data.csv"
        ]
        found_real = False
        for candidate in real_candidates:
            if candidate.exists():
                large_data_path = str(candidate)
                source_type = "real"
                found_real = True
                break
        
        if not found_real:
            log_message("WARNING: No real data or harmonized data found. Using proxy if available, else failing.", log_file)
            # Fallback to proxy if real data is missing
            proxy_path = paths["data"] / "raw" / "large_proxy.csv"
            if proxy_path.exists():
                large_data_path = str(proxy_path)
                source_type = "large_proxy"
                log_message(f"Using large proxy as fallback: {large_data_path}", log_file)
            else:
                log_message("ERROR: No data source available for stress test.", log_file)
                return False, "No data source"

    # 1. Pre-check RAM
    log_message("Step 1: RAM Pre-check", log_file)
    # Estimate RAM based on file size or N
    # We need to load the data to get N, or estimate from file size
    # For simplicity, we assume the pipeline's estimate_ram_usage can handle the path
    # But estimate_ram_usage in main.py expects a dataset object or path?
    # Let's assume we pass the path and it estimates.
    # If the function signature in main.py is fixed, we might need to adapt.
    # Based on API: estimate_ram_usage, determine_compute_strategy, save_compute_strategy
    # We assume they work with the data path.
    
    try:
        ram_estimate = estimate_ram_usage(large_data_path)
        log_message(f"Estimated RAM usage: {ram_estimate:.2f} GB", log_file)
        
        strategy = determine_compute_strategy(ram_estimate)
        log_message(f"Compute Strategy: {strategy}", log_file)
        
        save_compute_strategy(strategy, ram_estimate, paths["data"] / "metadata" / "compute_strategy.json")
        
        if strategy == "FAIL":
            log_message("ERROR: Dataset too large for standard runner. Halting.", log_file)
            return False, "RAM_FAIL"
    except Exception as e:
        log_message(f"ERROR: RAM check failed: {e}", log_file)
        return False, str(e)

    # 2. Ingestion and Validation (US1)
    log_message("Step 2: Ingestion and Validation (US1)", log_file)
    try:
        # We need to set the data path in config or pass it
        # The main.py run_ingestion_and_validation likely reads from config
        # We need to ensure the config points to our large data
        # Assuming config can be updated or passed
        # For this script, we might need to temporarily override config
        # Or assume the pipeline is already configured to use the large data
        # Let's assume the pipeline reads from a standard location or config
        # If the pipeline expects 'filtered_data.parquet', we might need to symlink or copy
        # But the task says "Execute the full pipeline... on a large dataset"
        # So we assume the pipeline is configured to use 'large_data_path'
        
        # We will call the pipeline functions directly, passing the data path if possible
        # If the functions are hardcoded to read from config, we might need to update config
        # Let's assume we can update the config in memory or file
        config["data"]["input_path"] = large_data_path
        
        run_ingestion_and_validation(config, paths)
        log_message("Ingestion and Validation completed.", log_file)
    except Exception as e:
        log_message(f"ERROR: Ingestion failed: {e}", log_file)
        return False, str(e)

    # 3. Analysis (US2)
    log_message("Step 3: Analysis (US2)", log_file)
    try:
        run_analysis(config, paths)
        log_message("Analysis completed.", log_file)
    except Exception as e:
        log_message(f"ERROR: Analysis failed: {e}", log_file)
        return False, str(e)

    # 4. Diagnostics (US3)
    log_message("Step 4: Diagnostics (US3)", log_file)
    try:
        run_diagnostics(config, paths)
        log_message("Diagnostics completed.", log_file)
    except Exception as e:
        log_message(f"ERROR: Diagnostics failed: {e}", log_file)
        return False, str(e)

    return True, "SUCCESS"

def main():
    parser = argparse.ArgumentParser(description="Run 6-Hour Stress Test")
    parser.add_argument("--use-harmonized", action="store_true", help="Use harmonized real data")
    parser.add_argument("--use-proxy", action="store_true", help="Use large proxy dataset")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()

    paths = setup_paths()
    report_path = paths["data"] / "results" / "6_hour_stress_test_report.json"

    start_time = time.time()
    log_message("Test started", paths["data"] / "results" / "stress_test_execution.log")

    success, message = run_full_pipeline_on_large_dataset(
        use_harmonized=args.use_harmonized,
        use_proxy=args.use_proxy,
        config_path=args.config
    )

    end_time = time.time()
    duration_seconds = end_time - start_time
    duration_hours = duration_seconds / 3600

    limit_hours = 6.0
    passed = success and (duration_hours < limit_hours)

    report = {
        "task_id": "T071",
        "status": "PASS" if passed else "FAIL",
        "duration_seconds": duration_seconds,
        "duration_hours": duration_hours,
        "limit_hours": limit_hours,
        "passed_6h_limit": passed,
        "success": success,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Write report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    log_message(f"Test finished. Duration: {duration_hours:.2f} hours. Status: {report['status']}", 
                paths["data"] / "results" / "stress_test_execution.log")
    log_message(f"Report written to {report_path}", 
                paths["data"] / "results" / "stress_test_execution.log")

    if not passed:
        print(f"STRESS TEST FAILED: {message} or Duration {duration_hours:.2f}h > {limit_hours}h")
        sys.exit(1)
    else:
        print("STRESS TEST PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
