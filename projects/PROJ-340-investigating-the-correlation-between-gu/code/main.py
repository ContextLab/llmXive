"""
Main pipeline orchestration script for the Gut Microbiome - Sleep Architecture study.
Coordinates ingestion, validation, analysis, and diagnostics.
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path

# Importing from sibling modules as per API surface
from ingest import (
    setup_logging, 
    load_schema, 
    load_required_variables, 
    validate_variables, 
    save_variable_metrics, 
    fetch_real_data, 
    load_data, 
    detect_outliers_iqr, 
    save_outlier_report, 
    filter_outliers, 
    save_filtered_data, 
    record_checksum,
    RealDataFetchError
)
from analysis import (
    set_analysis_seed, 
    select_correlation_method, 
    run_correlation_analysis, 
    benjamini_hochberg_fdr, 
    main as analysis_main
)
from diagnostics import (
    set_diagnostics_seed, 
    calculate_vif, 
    detect_perfect_multicollinearity, 
    run_sensitivity_analysis, 
    calculate_power, 
    run_collinearity_diagnostics, 
    generate_diagnostics_report,
    main as diagnostics_main
)
from config import load_config, get_config
from constitution_checker import run_constitution_check
from reference_validator import ReferenceValidator
from report import generate_report, main as report_main

def setup_paths(base_dir=None):
    """Ensure all necessary directories exist."""
    base = Path(base_dir) if base_dir else Path.cwd()
    dirs = [
        base / "data" / "raw",
        base / "data" / "processed",
        base / "data" / "results",
        base / "data" / "logs",
        base / "data" / "metadata",
        base / "data" / "config",
        base / "state" / "projects",
        base / "specs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return base

def estimate_ram_usage(df_shape):
    """Rough estimate of RAM usage based on dataframe shape."""
    # Assume float64 (8 bytes) per value
    bytes_needed = df_shape[0] * df_shape[1] * 8
    return bytes_needed / (1024 ** 3)  # Convert to GB

def determine_compute_strategy(ram_gb):
    """Determine if we need streaming or can load fully."""
    if ram_gb > 7.0:  # Threshold for safe CPU execution
        return "streaming"
    return "full_load"

def save_compute_strategy(strategy, output_path):
    """Save the computed strategy to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump({"strategy": strategy}, f, indent=2)

def run_ingestion_and_validation(config):
    """
    Execute ingestion and validation steps.
    Implements T082: Real-Data Gate in Orchestration.
    """
    logger = setup_logging()
    logger.info("Starting ingestion and validation phase.")

    # T082: REAL-DATA GATE IN ORCHESTRATION
    # Check for the existence of data/raw/real_data.csv before proceeding.
    # If missing, HALT with a clear error message.
    real_data_path = config.get("real_data_path", "data/raw/real_data.csv")
    if not os.path.exists(real_data_path):
        error_msg = "Real data not found. Aborting pipeline. Please provide a verified real dataset."
        logger.error(error_msg)
        # Halt execution immediately as per T082 requirements
        sys.exit(1)

    # Load required variables schema
    required_vars_path = config.get("required_variables_path", "data/config/required_variables.yaml")
    if not os.path.exists(required_vars_path):
        logger.error(f"Required variables file not found: {required_vars_path}")
        sys.exit(1)

    required_vars = load_required_variables(required_vars_path)
    
    # Validate variables in the real data
    validation_result = validate_variables(real_data_path, required_vars)
    save_variable_metrics(validation_result, "data/results/variable_load_metrics.json")

    if validation_result["status"] == "FAIL":
        missing = ", ".join(validation_result["missing_variables"])
        logger.error(f"Validation failed. Missing variables: {missing}")
        sys.exit(1)

    logger.info("Variable validation passed.")

    # Load the data
    data = load_data(real_data_path)
    logger.info(f"Data loaded successfully. Shape: {data.shape}")

    # T014: Outlier detection
    outliers = detect_outliers_iqr(data)
    save_outlier_report(outliers, "data/results/outlier_report.json")

    # T014b: Filter outliers
    filtered_data = filter_outliers(data, outliers)
    save_filtered_data(filtered_data, "data/processed/filtered_data.parquet")
    logger.info("Outlier filtering complete.")

    # T014c: Record checksum
    record_checksum("data/processed/filtered_data.parquet", "state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml")

    return filtered_data

def run_analysis(data, config):
    """Execute the correlation analysis pipeline."""
    logger = setup_logging()
    logger.info("Starting analysis phase.")

    # Set seed for reproducibility
    set_analysis_seed(config.get("analysis_seed", 42))

    # T020: Check distribution
    # T020a: Compositionality check (assuming flag exists from previous run or logic)
    comp_flag_path = "data/metadata/compositionality_flag.json"
    compositionality = False
    if os.path.exists(comp_flag_path):
        with open(comp_flag_path, 'r') as f:
            compositionality = json.load(f).get("is_compositional", False)
    
    # T021: Select method
    method = select_correlation_method(data, compositionality)
    logger.info(f"Selected correlation method: {method}")

    # T022: Transform if necessary (CLR)
    # Assuming transform logic is inside analysis or handled by method selection
    
    # T023/T024: Run correlation
    results = run_correlation_analysis(data, method)
    
    # T025: FDR Correction
    corrected_results = benjamini_hochberg_fdr(results)
    
    # Save results
    output_path = "data/results/correlation_matrix.json"
    with open(output_path, 'w') as f:
        json.dump(corrected_results, f, indent=2, default=str)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    return corrected_results

def run_diagnostics(data, config):
    """Execute diagnostics: Sensitivity, VIF, Power."""
    logger = setup_logging()
    logger.info("Starting diagnostics phase.")

    # T021f_new: Collinearity detection
    collinearity_map_path = "data/metadata/static_collinearity_map.json"
    collinearity_map = {}
    if os.path.exists(collinearity_map_path):
        with open(collinearity_map_path, 'r') as f:
            collinearity_map = json.load(f)

    # T079: VIF Calculation
    vif_report = calculate_vif(data, collinearity_map)
    with open("data/results/vif_report.json", 'w') as f:
        json.dump(vif_report, f, indent=2, default=str)

    # T078: Sensitivity Analysis
    sensitivity_results = run_sensitivity_analysis("data/results/correlation_matrix.json")
    with open("data/results/sensitivity_analysis.json", 'w') as f:
        json.dump(sensitivity_results, f, indent=2)

    # T084: Power Analysis
    power_results = calculate_power(data, config.get("effect_size", 0.3), config.get("power", 0.8))
    with open("data/results/power_analysis.json", 'w') as f:
        json.dump(power_results, f, indent=2)

    logger.info("Diagnostics complete.")
    return {
        "vif": vif_report,
        "sensitivity": sensitivity_results,
        "power": power_results
    }

def main():
    parser = argparse.ArgumentParser(description="Gut Microbiome - Sleep Architecture Analysis Pipeline")
    parser.add_argument("--config", type=str, default="data/config/pipeline_config.yaml", help="Path to config file")
    parser.add_argument("--input", type=str, help="Optional input data path (overrides config)")
    parser.add_argument("--output", type=str, help="Optional output directory (overrides config)")
    args = parser.parse_args()

    # Setup paths
    base_dir = setup_paths()
    
    # Load config
    config = load_config(args.config)
    if args.input:
        config["real_data_path"] = args.input
    if args.output:
        config["output_dir"] = args.output

    # T015: Orchestration Start
    start_time = time.time()
    
    try:
        # 1. Ingestion & Validation (Includes T082 Gate)
        data = run_ingestion_and_validation(config)

        # 2. Analysis
        analysis_results = run_analysis(data, config)

        # 3. Diagnostics
        diag_results = run_diagnostics(data, config)

        # 4. Timing Evidence (T016)
        end_time = time.time()
        duration = end_time - start_time
        timing_evidence = {
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "duration_hours": duration / 3600,
            "status": "SUCCESS" if duration < 21600 else "TIMEOUT" # 6 hours = 21600s
        }
        with open("data/results/timing_evidence.json", 'w') as f:
            json.dump(timing_evidence, f, indent=2)

        if timing_evidence["status"] == "TIMEOUT":
            logger = setup_logging()
            logger.error("Pipeline execution exceeded 6-hour limit.")
            sys.exit(1)

        # 5. Report Generation
        generate_report()

        logger.info("Pipeline completed successfully.")

    except RealDataFetchError as e:
        logger.error(f"Real data fetch error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise

if __name__ == "__main__":
    main()