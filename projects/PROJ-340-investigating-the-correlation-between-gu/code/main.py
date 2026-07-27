import sys
import os
import json
import time
import argparse
from pathlib import Path

# Import US1 (Ingestion & Validation)
from ingest import (
    MissingDataError,
    load_schema,
    load_required_variables,
    validate_variables,
    save_variable_metrics,
    load_data,
    detect_outliers_iqr,
    filter_outliers,
    save_outlier_report,
    save_filtered_data,
    load_streamed_dataset,
    calculate_checksum,
    register_checksum_in_state
)

# Import US2 (Analysis)
from analysis import (
    set_analysis_seed,
    select_correlation_method,
    run_correlation_analysis,
    benjamini_hochberg_fdr
)

# Import US3 (Diagnostics)
from diagnostics import (
    set_diagnostics_seed,
    calculate_vif,
    detect_perfect_multicollinearity,
    run_sensitivity_analysis,
    calculate_power,
    run_collinearity_diagnostics,
    generate_diagnostics_report
)

# Import Constitution & Config
from constitution_checker import run_constitution_check
from config import get_config, load_config

# Import Report Generation
from report import generate_report

def setup_paths(args):
    """Initialize project paths based on arguments."""
    base_path = Path(args.project_root) if args.project_root else Path.cwd()
    
    # Ensure directories exist
    (base_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (base_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (base_path / "data" / "metadata").mkdir(parents=True, exist_ok=True)
    (base_path / "data" / "results").mkdir(parents=True, exist_ok=True)
    (base_path / "state" / "projects").mkdir(parents=True, exist_ok=True)
    
    return base_path

def estimate_ram_usage(n_subjects, n_taxa):
    """
    Estimate RAM usage in GB.
    Formula: (N_subjects * N_taxa * 8 bytes) / 1e9
    Assumes float64 data.
    """
    # 8 bytes per float64
    bytes_needed = n_subjects * n_taxa * 8
    gb_needed = bytes_needed / 1e9
    return gb_needed

def determine_compute_strategy(n_subjects, n_taxa):
    """
    Determine compute strategy based on estimated RAM.
    Returns: 'OK', 'STREAM', or 'FAIL'
    """
    est_gb = estimate_ram_usage(n_subjects, n_taxa)
    
    if est_gb <= 6.0:
        return 'OK'
    elif est_gb <= 7.0:
        return 'STREAM'
    else:
        return 'FAIL'

def save_compute_strategy(strategy, n_subjects, n_taxa, est_gb, output_dir):
    """Save compute strategy decision to disk."""
    data = {
        "status": strategy,
        "n_subjects": n_subjects,
        "n_taxa": n_taxa,
        "estimated_ram_gb": est_gb,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    path = Path(output_dir) / "metadata" / "compute_strategy.json"
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    return path

def run_compute_feasibility_check(args, base_path):
    """
    Run RAM pre-check. If 'FAIL', exit. If 'STREAM', enable streaming.
    """
    # For initial check, we need to know dimensions. 
    # If synthetic mode, we generate dimensions from config.
    # If real mode, we might need to peek at the file or rely on metadata.
    # For now, we assume we load a small sample or rely on args if provided.
    # In a real scenario, T058 would run here to estimate size before full load.
    
    # Placeholder for T058 logic:
    # We will assume a default small size for the check if not provided,
    # but in the full pipeline, this would be done after a quick header read.
    n_subjects = args.n_subjects if hasattr(args, 'n_subjects') and args.n_subjects else 100
    n_taxa = args.n_taxa if hasattr(args, 'n_taxa') and args.n_taxa else 500
    
    strategy = determine_compute_strategy(n_subjects, n_taxa)
    est_gb = estimate_ram_usage(n_subjects, n_taxa)
    
    save_compute_strategy(strategy, n_subjects, n_taxa, est_gb, base_path)
    
    if strategy == 'FAIL':
        print(f"CRITICAL: Estimated RAM ({est_gb:.2f} GB) exceeds 7GB limit.")
        print("Please downsample the dataset or use a smaller dataset.")
        sys.exit(1)
    
    return strategy

def run_ingestion_and_validation(args, base_path):
    """
    Execute US1: Ingestion, Validation, Outlier Detection, Filtering.
    Returns path to filtered data.
    """
    print("=== Starting Ingestion and Validation (US1) ===")
    
    # Load config
    config = load_config(base_path)
    
    # Validate variables
    required_vars = load_required_variables(base_path)
    # Note: validate_variables logic is in ingest.py, called here or internally
    # We assume ingest.py handles the file loading and validation logic internally
    # based on the mode.
    
    # Determine input source
    if args.mode == 'synthetic':
        # Generate synthetic data if not exists or forced
        from data_generator import main as gen_main
        # We need to generate the synthetic data first if it doesn't exist
        # This is a call to the generator script logic
        # In a real pipeline, we might check existence first.
        # For now, we assume the generator creates the necessary files.
        # We'll call the generator directly to ensure data exists.
        from data_generator import generate_synthetic_dataset, generate_synthetic_manifest
        
        # Generate manifest
        generate_synthetic_manifest(base_path / "data" / "metadata")
        
        # Generate dataset
        generate_synthetic_dataset(base_path, args.n_subjects)
        
        input_file = base_path / "data" / "raw" / "synthetic_data.csv"
    else:
        input_file = Path(args.input)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Validate variables
    # This function should read the schema and the input file and produce metrics
    validate_variables(input_file, base_path)
    
    # Load data (this checks the metrics from validate_variables)
    # If validation failed (missing vars), this will exit
    df = load_data(input_file, base_path)
    
    # Outlier detection
    outliers = detect_outliers_iqr(df)
    save_outlier_report(outliers, base_path / "data" / "results")
    
    # Filter outliers
    df_filtered = filter_outliers(df, outliers)
    save_filtered_data(df_filtered, base_path / "data" / "processed")
    
    # Register checksum
    filtered_path = base_path / "data" / "processed" / "filtered_data.parquet"
    checksum = calculate_checksum(filtered_path)
    register_checksum_in_state(base_path, "filtered_data.parquet", checksum)
    
    print("=== Ingestion and Validation Complete ===")
    return df_filtered

def run_analysis(args, base_path, df):
    """
    Execute US2: Distribution Check, Method Selection, Correlation, FDR.
    Returns correlation matrix path.
    """
    print("=== Starting Analysis (US2) ===")
    
    # Set seed
    set_analysis_seed(42)
    
    # Distribution Check (T020)
    # This logic is in analysis.py, we call the relevant functions
    # We need to determine if data is zero-inflated or compositional
    # For this orchestration, we assume analysis.py handles the internal logic
    # based on the data passed.
    
    # Select method (T021)
    # This reads the flags generated by T020/T022a
    # We assume the analysis module handles the file I/O for flags
    method_info = select_correlation_method(df, base_path)
    
    # Run Correlation
    # This executes the selected method (ZINB, Spearman, Pearson)
    results = run_correlation_analysis(df, method_info, base_path)
    
    # FDR Correction (T025)
    results_fdr = benjamini_hochberg_fdr(results)
    
    # Save results
    output_path = base_path / "data" / "results" / "correlation_matrix.json"
    with open(output_path, 'w') as f:
        json.dump(results_fdr, f, indent=2)
    
    print("=== Analysis Complete ===")
    return output_path

def run_diagnostics(args, base_path, correlation_results_path):
    """
    Execute US3: Collinearity, Sensitivity, Power Analysis.
    Returns diagnostics report path.
    """
    print("=== Starting Diagnostics (US3) ===")
    
    set_diagnostics_seed(42)
    
    # Collinearity Diagnostics (T021h, T031)
    # This includes static and dynamic checks
    collinearity_report = run_collinearity_diagnostics(base_path)
    
    # Sensitivity Analysis (T030)
    sensitivity_report = run_sensitivity_analysis(correlation_results_path, base_path)
    
    # Power Analysis (T033)
    power_report = calculate_power(base_path)
    
    # Stability Metrics (T030a)
    # This is calculated from sensitivity report
    # Assuming generate_diagnostics_report handles this aggregation
    
    # Generate final diagnostics report
    diag_report_path = base_path / "data" / "results" / "diagnostics_report.json"
    generate_diagnostics_report(collinearity_report, sensitivity_report, power_report, base_path)
    
    print("=== Diagnostics Complete ===")
    return diag_report_path

def main():
    parser = argparse.ArgumentParser(description="Gut Microbiome - Sleep Architecture Analysis Pipeline")
    parser.add_argument("--project_root", type=str, default=None, help="Project root directory")
    parser.add_argument("--mode", type=str, default="synthetic", choices=["synthetic", "real"], help="Data mode")
    parser.add_argument("--input", type=str, default=None, help="Input file for real data mode")
    parser.add_argument("--n_subjects", type=int, default=100, help="Number of subjects for synthetic/estimation")
    parser.add_argument("--n_taxa", type=int, default=500, help="Number of taxa for synthetic/estimation")
    args = parser.parse_args()
    
    base_path = setup_paths(args)
    
    # 1. Compute Feasibility (T058)
    strategy = run_compute_feasibility_check(args, base_path)
    
    # 2. Constitution Check (Pre-run)
    run_constitution_check(base_path, mode=args.mode)
    
    # 3. Ingestion & Validation (US1)
    df = run_ingestion_and_validation(args, base_path)
    
    # 4. Analysis (US2)
    corr_path = run_analysis(args, base_path, df)
    
    # 5. Diagnostics (US3)
    diag_path = run_diagnostics(args, base_path, corr_path)
    
    # 6. Report Generation (Integration)
    # This consumes all artifacts and generates the final report
    from report import main as report_main
    # We need to pass the paths or let report.py find them
    # Assuming report.py looks for standard paths in base_path
    report_main(base_path, args.mode)
    
    print("Pipeline execution complete.")

if __name__ == "__main__":
    main()