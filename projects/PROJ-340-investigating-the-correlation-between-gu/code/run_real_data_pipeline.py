import os
import sys
import json
import time
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Import from project modules
from ingest import load_data, validate_variables, save_variable_metrics
from analysis import run_correlation_analysis, select_correlation_method, set_analysis_seed
from diagnostics import generate_diagnostics_report, calculate_power, set_diagnostics_seed
from report import generate_report

def setup_paths():
    """Ensure required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "data/metadata"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def run_real_data_pipeline(input_file: str, output_dir: str = "data/results"):
    """
    Run the full pipeline on real data with power analysis reporting.
    
    This function implements T084 by ensuring power analysis is performed
    and reported in the diagnostics output.
    
    Args:
        input_file: Path to the real data CSV file.
        output_dir: Directory to write results.
    """
    set_diagnostics_seed()
    set_analysis_seed()
    
    print(f"Starting real data pipeline with input: {input_file}")
    
    # Step 1: Load and validate data
    print("Step 1: Loading and validating data...")
    try:
        data = load_data(input_file)
        if data is None or data.empty:
            print("ERROR: Data loading failed or resulted in empty dataset.")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Data loading failed: {e}")
        sys.exit(1)
        
    # Step 2: Validate variables
    print("Step 2: Validating variables...")
    try:
        validation_result = validate_variables(data)
        save_variable_metrics(validation_result, "data/results/variable_load_metrics.json")
        
        if validation_result.get("status") == "FAIL":
            missing = validation_result.get("missing_variables", [])
            print(f"ERROR: Missing required variables: {missing}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Variable validation failed: {e}")
        sys.exit(1)
        
    # Step 3: Detect and remove outliers
    print("Step 3: Detecting outliers...")
    try:
        from ingest import detect_outliers_iqr, filter_outliers, save_outlier_report, save_filtered_data
        outliers = detect_outliers_iqr(data)
        save_outlier_report(outliers, "data/results/outlier_report.json")
        
        filtered_data = filter_outliers(data, outliers)
        save_filtered_data(filtered_data, "data/processed/filtered_data.parquet")
    except Exception as e:
        print(f"ERROR: Outlier detection failed: {e}")
        sys.exit(1)
        
    # Step 4: Run correlation analysis
    print("Step 4: Running correlation analysis...")
    try:
        predictors = [col for col in filtered_data.columns if col.startswith('taxon_') or col in ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria', 'Fusobacteria']]
        outcomes = [col for col in filtered_data.columns if col in ['REM_duration', 'SWS_duration', 'Wake_after_sleep_onset', 'Total_sleep_time']]
        
        if not predictors or not outcomes:
            print("ERROR: No valid predictors or outcomes found.")
            sys.exit(1)
            
        correlation_results = run_correlation_analysis(filtered_data, predictors, outcomes)
        
        # Save correlation results
        with open("data/results/correlation_matrix.json", 'w') as f:
            json.dump(correlation_results, f, indent=2)
    except Exception as e:
        print(f"ERROR: Correlation analysis failed: {e}")
        sys.exit(1)
        
    # Step 5: Run diagnostics including power analysis (T084)
    print("Step 5: Running diagnostics and power analysis...")
    try:
        observed_n = len(filtered_data)
        power_result = calculate_power(observed_n)
        
        # Generate full diagnostics report
        diagnostics_report = generate_diagnostics_report(
            filtered_data, 
            predictors, 
            correlation_results
        )
        
        # Ensure power analysis is explicitly included
        diagnostics_report["power"]["observed_n"] = observed_n
        diagnostics_report["power"]["message"] = "Underpowered" if power_result["underpowered"] else "Adequately powered"
        
        # Save diagnostics report
        with open("data/results/diagnostics_report.json", 'w') as f:
            json.dump(diagnostics_report, f, indent=2)
            
        # Save specific power analysis file for T084
        with open("data/results/power_analysis.json", 'w') as f:
            json.dump(power_result, f, indent=2)
            
        print(f"Power Analysis Results: N={observed_n}, Required N={power_result['required_n']}, Status={power_result['message']}")
    except Exception as e:
        print(f"ERROR: Diagnostics/Power analysis failed: {e}")
        sys.exit(1)
        
    # Step 6: Generate report
    print("Step 6: Generating final report...")
    try:
        generate_report()
    except Exception as e:
        print(f"ERROR: Report generation failed: {e}")
        sys.exit(1)
        
    print("Pipeline completed successfully.")
    return True

def main():
    """Main entry point for real data pipeline."""
    parser = argparse.ArgumentParser(description="Run analysis pipeline on real data.")
    parser.add_argument("--input", type=str, required=True, help="Path to input real data CSV")
    parser.add_argument("--output", type=str, default="data/results", help="Output directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)
        
    setup_paths()
    success = run_real_data_pipeline(args.input, args.output)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()