"""
Main Pipeline Orchestrator.

This module coordinates the execution of the full analysis pipeline.
It handles ingestion, validation, analysis, diagnostics, and reporting.
"""
import sys
import os
import json
import time
import argparse
import logging
from pathlib import Path

# Import from existing modules
from ingest import load_data, validate_variables, detect_outliers_iqr, save_outlier_report, filter_outliers, save_filtered_data, record_artifact_checksum
from analysis import set_analysis_seed, check_distribution, select_correlation_method, run_correlation_analysis, benjamini_hochberg_fdr, save_method_selection_log
from diagnostics import set_diagnostics_seed, detect_perfect_multicollinearity, calculate_vif, run_sensitivity_analysis, calculate_power
from report import generate_report, load_json_file
from config import load_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_paths(base_dir: Path):
    """Setup output directories."""
    dirs = [
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "results",
        base_dir / "metadata"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def estimate_ram_usage(df):
    """Estimate RAM usage based on dataframe size."""
    # Rough estimate: 8 bytes per float64, 4 bytes per int32, etc.
    return df.memory_usage(deep=True).sum()

def determine_compute_strategy(ram_estimate_gb):
    """Determine compute strategy based on RAM estimate."""
    if ram_estimate_gb > 14:
        return "streaming"
    elif ram_estimate_gb > 7:
        return "chunked"
    else:
        return "full"

def save_compute_strategy(strategy, output_path: Path):
    """Save compute strategy decision."""
    with open(output_path, 'w') as f:
        json.dump({"strategy": strategy}, f, indent=2)

def check_validation_mode(config_path: Path):
    """Check if running in validation (synthetic) mode."""
    # This is a placeholder; actual logic depends on env vars or config flags
    return os.environ.get("VALIDATION_MODE", "false").lower() == "true"

def run_ingestion_and_validation(input_path: Path, config_path: Path, output_path: Path):
    """Run data ingestion, validation, outlier detection, and filtering."""
    logger.info("Starting ingestion and validation...")
    
    # Load and validate
    df, metrics = load_data(input_path, config_path)
    
    # Save metrics
    metrics_path = output_path / "results" / "variable_load_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Outlier detection
    outlier_report = detect_outliers_iqr(df)
    save_outlier_report(outlier_report, output_path / "results" / "outlier_report.json")
    
    # Filtering
    filtered_df, exclusion_log = filter_outliers(df, outlier_report)
    filtered_path = output_path / "processed" / "filtered_data.parquet"
    save_filtered_data(filtered_df, filtered_path)
    record_artifact_checksum(filtered_path, output_path / "results" / "artifact_checksums.json")
    
    # Save exclusion log
    with open(output_path / "results" / "outlier_exclusion_log.json", 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    return filtered_df

def run_analysis(input_path: Path, output_path: Path):
    """Run correlation analysis."""
    logger.info("Running analysis...")
    
    import pandas as pd
    df = pd.read_parquet(input_path)
    
    # Distribution check
    dist_info = check_distribution(df)
    
    # Method selection
    method = select_correlation_method(df, dist_info)
    save_method_selection_log(method, output_path / "metadata" / "method_selection_log.json")
    
    # Correlation analysis
    results = run_correlation_analysis(df, method)
    corrected_results = benjamini_hochberg_fdr(results)
    
    # Save results
    corr_matrix_path = output_path / "results" / "correlation_matrix.json"
    with open(corr_matrix_path, 'w') as f:
        json.dump(corrected_results, f, indent=2)
    
    return corrected_results

def run_diagnostics(input_path: Path, output_path: Path):
    """Run diagnostics."""
    logger.info("Running diagnostics...")
    
    import pandas as pd
    df = pd.read_parquet(input_path)
    
    # Collinearity
    collinearity_map = detect_perfect_multicollinearity(df)
    
    # VIF
    vif_report = calculate_vif(df)
    with open(output_path / "results" / "vif_report.json", 'w') as f:
        json.dump(vif_report, f, indent=2)
    
    # Sensitivity
    sensitivity_results = run_sensitivity_analysis(df)
    sensitivity_results.to_csv(output_path / "results" / "sensitivity_analysis.csv", index=False)
    
    # Power
    power_report = calculate_power(df)
    with open(output_path / "results" / "power_analysis_report.json", 'w') as f:
        json.dump(power_report, f, indent=2)
    
    # Collinearity warnings
    with open(output_path / "results" / "collinearity_warnings.json", 'w') as f:
        json.dump({"collinearity_map": collinearity_map, "vif_flags": vif_report.get("flags", [])}, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline Orchestrator")
    parser.add_argument("--input", type=str, required=True, help="Input data path")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--config", type=str, default="data/config/required_variables.yaml", help="Config path")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    config_path = Path(args.config)
    
    start_time = time.time()
    
    setup_paths(output_path)
    
    # Ingestion
    filtered_path = run_ingestion_and_validation(input_path, config_path, output_path)
    
    # Analysis
    run_analysis(filtered_path, output_path)
    
    # Diagnostics
    run_diagnostics(filtered_path, output_path)
    
    # Timing
    timing = {"total_runtime_seconds": time.time() - start_time, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(output_path / "results" / "timing_evidence.json", 'w') as f:
        json.dump(timing, f, indent=2)
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()