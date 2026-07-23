import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

from ingest import (
    load_data, validate_variables, save_variable_metrics, 
    detect_outliers_iqr, filter_outliers, load_required_variables,
    MissingDataError
)
from analysis import run_correlation_analysis
from diagnostics import run_collinearity_diagnostics, run_sensitivity_analysis, calculate_power
from config import get_config, load_config
from report import generate_report

def setup_paths():
    """Ensure all necessary directories exist."""
    dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/results"),
        Path("data/metadata"),
        Path("state/projects"),
        Path("code"),
        Path("tests")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def estimate_ram_usage(df_shape: tuple) -> float:
    """
    Estimate RAM usage in GB based on dataset shape.
    Formula: Estimate (GB) = (N_subjects * N_taxa * 8 bytes) / (1024^3 * 0.83)
    """
    n_subjects, n_cols = df_shape
    # Assume ~8 bytes per float64 value
    bytes_needed = n_subjects * n_cols * 8
    gb_needed = bytes_needed / (1024**3)
    # Add 20% overhead buffer
    return gb_needed * 1.2

def determine_compute_strategy(ram_estimate_gb: float) -> str:
    """
    Determine compute strategy based on RAM estimate.
    Returns 'OK', 'STREAM', or 'FAIL'.
    """
    if ram_estimate_gb <= 6.0:
        return 'OK'
    elif ram_estimate_gb <= 7.0:
        return 'STREAM'
    else:
        return 'FAIL'

def save_compute_strategy(strategy: str, output_path: Path):
    """Save compute strategy decision to JSON."""
    data = {
        "ram_estimate_gb": strategy.get('ram', 0),
        "strategy": strategy.get('status', 'UNKNOWN'),
        "timestamp": datetime.now().isoformat()
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def run_compute_feasibility_check(df):
    """Run RAM check and determine compute strategy."""
    ram_estimate = estimate_ram_usage(df.shape)
    strategy = determine_compute_strategy(ram_estimate)
    strategy_path = Path("data/metadata/compute_strategy.json")
    save_compute_strategy({"status": strategy, "ram": ram_estimate}, strategy_path)
    
    if strategy == 'FAIL':
        print(f"CRITICAL: Estimated RAM usage ({ram_estimate:.2f} GB) exceeds 7GB limit.")
        print("Please downsample the dataset or use a smaller dataset.")
        sys.exit(1)
    
    print(f"Compute strategy: {strategy} (Est. RAM: {ram_estimate:.2f} GB)")
    return strategy

def run_ingestion_and_validation(input_path: str, output_path: str):
    """Run ingestion, validation, outlier detection, and filtering."""
    print("=== Starting Ingestion and Validation ===")
    
    # Load data
    df = load_data(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")
    
    # Get required variables
    predictors, outcomes = load_required_variables()
    
    # Validate variables
    metrics = validate_variables(df, predictors, outcomes)
    metrics_path = Path("data/results/variable_load_metrics.json")
    save_variable_metrics(metrics, metrics_path)
    
    if metrics['status'] == 'FAIL':
        print(f"Validation FAILED. Missing variables: {metrics['missing_variables']}")
        sys.exit(1)
    
    # Detect outliers
    print("Detecting outliers using IQR method...")
    df_with_flags = detect_outliers_iqr(df)
    
    # Filter outliers
    print("Filtering outliers...")
    filtered_df = filter_outliers(df_with_flags, output_path)
    
    print(f"=== Ingestion Complete. Filtered rows: {len(filtered_df)} ===")
    return filtered_df

def run_analysis(input_path: str):
    """Run correlation analysis on filtered data."""
    print("=== Starting Analysis ===")
    df = load_data(input_path)
    
    # Run correlation analysis
    results = run_correlation_analysis(df)
    
    # Save results
    output_path = Path("data/results/correlation_matrix.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Results saved to {output_path}")
    return results

def run_diagnostics(input_path: str):
    """Run diagnostics (collinearity, sensitivity, power)."""
    print("=== Starting Diagnostics ===")
    df = load_data(input_path)
    
    # Run collinearity diagnostics
    collinearity_report = run_collinearity_diagnostics(df)
    collinearity_path = Path("data/results/collinearity_report.json")
    with open(collinearity_path, 'w') as f:
        json.dump(collinearity_report, f, indent=2)
    
    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis()
    sensitivity_path = Path("data/results/sensitivity_analysis.json")
    with open(sensitivity_path, 'w') as f:
        json.dump(sensitivity_results, f, indent=2)
    
    # Run power analysis
    power_results = calculate_power()
    power_path = Path("data/results/power_analysis.json")
    with open(power_path, 'w') as f:
        json.dump(power_results, f, indent=2)
    
    print("=== Diagnostics Complete ===")
    return {
        "collinearity": collinearity_report,
        "sensitivity": sensitivity_results,
        "power": power_results
    }

def generate_harmonization_report():
    """Generate a report comparing harmonized vs synthetic results."""
    # Placeholder for harmonization logic
    report = {
        "status": "Pipeline Validation Study",
        "note": "Real data harmonization not yet implemented."
    }
    output_path = Path("data/results/harmonized_vs_synthetic_comparison.json")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    return report

def generate_real_data_analysis_report():
    """Generate report for real data analysis."""
    # Placeholder for real data analysis report
    report = {
        "status": "Real Data Analysis Pending",
        "note": "Waiting for real data source."
    }
    output_path = Path("data/results/real_data_analysis_report.json")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    return report

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Gut Microbiome and Sleep Architecture Analysis Pipeline")
    parser.add_argument('--input', type=str, help='Path to input data file')
    parser.add_argument('--output', type=str, default="data/results/", help='Output directory for results')
    parser.add_argument('--mode', type=str, choices=['real', 'synthetic'], default='synthetic', help='Data mode')
    
    args = parser.parse_args()
    
    start_time = time.time()
    setup_paths()
    
    # Determine input path
    if args.mode == 'synthetic' and not args.input:
        args.input = "data/raw/synthetic_data.csv"
        if not Path(args.input).exists():
            # Generate synthetic data first
            from data_generator import generate_synthetic_dataset
            print("Generating synthetic data...")
            generate_synthetic_dataset(output_path=args.input)
    
    if not args.input or not Path(args.input).exists():
        print("Error: Input file not found. Use --input to specify a file or --mode synthetic to generate data.")
        sys.exit(1)
    
    # Run ingestion and validation
    output_path = Path(args.output) / "filtered_data.parquet"
    filtered_df = run_ingestion_and_validation(args.input, str(output_path))
    
    # Run compute feasibility check
    run_compute_feasibility_check(filtered_df)
    
    # Run analysis
    analysis_results = run_analysis(str(output_path))
    
    # Run diagnostics
    diagnostics_results = run_diagnostics(str(output_path))
    
    # Generate timing evidence
    end_time = time.time()
    duration = end_time - start_time
    timing_evidence = {
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "duration_seconds": duration,
        "duration_hours": duration / 3600
    }
    timing_path = Path(args.output) / "timing_evidence.json"
    with open(timing_path, 'w') as f:
        json.dump(timing_evidence, f, indent=2)
    
    print(f"Pipeline completed in {duration:.2f} seconds ({duration/3600:.2f} hours)")
    
    # Check 6-hour constraint
    if duration > 6 * 3600:
        print("WARNING: Pipeline execution exceeded 6 hours.")
    else:
        print("SUCCESS: Pipeline execution within 6-hour constraint.")
    
    # Generate final report
    generate_report(args.output)
    
    print("Pipeline execution complete.")

if __name__ == "__main__":
    main()
