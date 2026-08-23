import os
import sys
import json
import argparse
import time
from pathlib import Path
import pandas as pd
import numpy as np

# Import from existing API surface
from data_generator import set_seeds, load_required_variables, generate_metagenomic_counts, generate_sleep_metrics, generate_synthetic_dataset
from ingest import load_data, detect_outliers_iqr, save_outlier_report, filter_outliers, save_filtered_data, RealDataFetchError
from analysis import set_analysis_seed, check_distribution, select_correlation_method, run_correlation_analysis, benjamini_hochberg_fdr, save_method_selection_log
from diagnostics import set_diagnostics_seed, run_sensitivity_analysis, calculate_power

def ensure_dirs():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "state/projects"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_synthetic_generation(output_path: str):
    """Generate synthetic data and write to CSV."""
    print(f"Generating synthetic data to {output_path}")
    set_seeds(42)
    required_vars = load_required_variables()
    
    # Generate data
    metagenomic_data = generate_metagenomic_counts(required_vars['predictors'])
    sleep_data = generate_sleep_metrics(required_vars['outcomes'])
    
    # Combine
    df = generate_synthetic_dataset(metagenomic_data, sleep_data)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} rows")
    return output_path

def run_ingestion(input_path: str, output_dir: str):
    """Run ingestion pipeline: validation, outlier detection, filtering."""
    print(f"Running ingestion on {input_path}")
    
    # Load data (this validates variables internally)
    try:
        df = load_data(input_path, mode="synthetic")
    except RealDataFetchError as e:
        # Expected if real data config is broken but we are in synthetic mode
        # The load_data function should handle synthetic mode without fetching
        print(f"Warning during load: {e}")
        # Fallback to direct load if load_data fails due to config issues
        df = pd.read_csv(input_path)
    
    # Detect outliers
    outlier_report = detect_outliers_iqr(df)
    save_outlier_report(outlier_report, f"{output_dir}/outlier_report.json")
    print(f"Outlier report saved. Excluded {outlier_report.get('exclusion_count', 0)} points.")
    
    # Filter outliers
    filtered_df = filter_outliers(df, outlier_report)
    filtered_path = f"{output_dir}/filtered_data.parquet"
    save_filtered_data(filtered_df, filtered_path)
    print(f"Filtered data saved to {filtered_path}")
    
    return filtered_path

def run_analysis(input_path: str, output_dir: str):
    """Run correlation analysis on filtered data."""
    print(f"Running analysis on {input_path}")
    df = pd.read_parquet(input_path)
    
    set_analysis_seed(42)
    
    # Check distribution
    dist_check = check_distribution(df)
    print(f"Distribution check: {dist_check}")
    
    # Select method
    method = select_correlation_method(df, dist_check)
    print(f"Selected method: {method}")
    
    # Run analysis
    results = run_correlation_analysis(df, method)
    
    # Apply FDR
    fdr_results = benjamini_hochberg_fdr(results)
    
    # Save results
    results_path = f"{output_dir}/correlation_results.csv"
    fdr_results.to_csv(results_path, index=False)
    print(f"Correlation results saved to {results_path}")
    
    # Save method selection log
    save_method_selection_log({"method": method, "distribution_check": dist_check}, f"{output_dir}/method_selection_log.json")
    
    return results_path

def run_diagnostics(input_path: str, output_dir: str):
    """Run diagnostics: sensitivity, power analysis."""
    print(f"Running diagnostics on {input_path}")
    df = pd.read_parquet(input_path)
    
    set_diagnostics_seed(42)
    
    # Sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(df)
    sensitivity_path = f"{output_dir}/sensitivity_analysis.json"
    with open(sensitivity_path, 'w') as f:
        json.dump(sensitivity_results, f, indent=2)
    print(f"Sensitivity analysis saved to {sensitivity_path}")
    
    # Power analysis
    power_results = calculate_power(df)
    power_path = f"{output_dir}/power_analysis_report.json"
    with open(power_path, 'w') as f:
        json.dump(power_results, f, indent=2)
    print(f"Power analysis saved to {power_path}")
    
    return power_path

def verify_outputs(output_dir: str):
    """Verify that all required output files exist."""
    required_files = [
        f"{output_dir}/filtered_data.parquet",
        f"{output_dir}/correlation_results.csv",
        f"{output_dir}/power_analysis_report.json",
        f"{output_dir}/outlier_report.json",
        f"{output_dir}/sensitivity_analysis.json",
        f"{output_dir}/method_selection_log.json"
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        print(f"MISSING OUTPUTS: {missing}")
        return False
    
    print("All required outputs verified.")
    return True

def run_full_pipeline():
    """Execute the full synthetic data pipeline."""
    ensure_dirs()
    
    start_time = time.time()
    
    # 1. Generate
    raw_path = run_synthetic_generation("data/raw/synthetic_test_data.csv")
    
    # 2. Ingest
    filtered_path = run_ingestion(raw_path, "data/processed")
    
    # 3. Analyze
    results_path = run_analysis(filtered_path, "data/results")
    
    # 4. Diagnostics
    diagnostics_path = run_diagnostics(filtered_path, "data/results")
    
    # 5. Verify
    success = verify_outputs("data/results")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Pipeline completed in {duration:.2f} seconds.")
    
    # Write timing evidence
    timing_report = {
        "total_duration_seconds": duration,
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
        "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
        "status": "success" if success else "failed"
    }
    with open("data/results/timing_evidence.json", 'w') as f:
        json.dump(timing_report, f, indent=2)
    
    return success

def main():
    parser = argparse.ArgumentParser(description="Run full synthetic data pipeline")
    args = parser.parse_args()
    
    success = run_full_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()