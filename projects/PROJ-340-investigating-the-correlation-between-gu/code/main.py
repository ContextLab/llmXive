import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
import argparse

from config import get_config, load_config
from data_generator import generate_synthetic_dataset, generate_coc_log
from ingest import (
    load_schema,
    validate_variables,
    save_variable_metrics,
    load_data,
    detect_outliers_iqr,
    filter_outliers,
    calculate_checksum,
    register_checksum_in_state,
    main as ingest_main
)
from analysis import run_correlation_analysis
from diagnostics import run_collinearity_diagnostics, generate_diagnostics_report
from report import generate_final_report

def setup_paths():
    """Initialize project paths and ensure directories exist."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    processed_dir = data_dir / "processed"
    results_dir = data_dir / "results"
    metadata_dir = data_dir / "metadata"
    state_dir = base_dir / "state" / "projects"

    for d in [data_dir, processed_dir, results_dir, metadata_dir, state_dir]:
        d.mkdir(parents=True, exist_ok=True)

    return {
        "base": base_dir,
        "data": data_dir,
        "processed": processed_dir,
        "results": results_dir,
        "metadata": metadata_dir,
        "state": state_dir,
    }

def run_ingestion_and_validation(paths, config, use_real_data=False):
    """Run data ingestion, validation, and filtering."""
    print(f"[{datetime.now().isoformat()}] Starting ingestion and validation...")

    # Load schema
    schema_path = paths["base"] / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts" / "dataset.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    schema = load_schema(schema_path)

    # Validate variables (checks against schema)
    if use_real_data:
        # For real data, we expect the raw file to exist at a specific location
        raw_data_path = paths["data"] / "raw" / "real_data.csv"
        if not raw_data_path.exists():
            raise FileNotFoundError(f"Real data file not found: {raw_data_path}. Please ensure T043/T044 have populated this file.")
        data = load_data(raw_data_path, schema)
    else:
        # Synthetic mode: generate data if not already present or force regeneration
        synthetic_data_path = paths["data"] / "processed" / "synthetic_data.parquet"
        coc_log_path = paths["metadata"] / "synthetic_coc_log.json"

        # Generate synthetic data if needed
        if not synthetic_data_path.exists() or True: # Always regenerate for consistency in this context
            print("Generating synthetic dataset...")
            dataset = generate_synthetic_dataset(seed=42)
            dataset.to_parquet(synthetic_data_path)
            print(f"Synthetic data saved to {synthetic_data_path}")

            # Generate COC log
            generate_coc_log(paths["metadata"], seed=42)
            print(f"COC log saved to {coc_log_path}")

        # Load the synthetic data for validation
        data = load_data(synthetic_data_path, schema)

    # Validate variables presence
    validation_result = validate_variables(data, schema)
    save_variable_metrics(paths["results"] / "variable_load_metrics.json", validation_result)

    if validation_result["percentage_loaded"] < 100:
        missing = [k for k, v in validation_result["found"].items() if not v]
        print(f"ERROR: Missing required variables: {missing}")
        sys.exit(1)

    # Detect and filter outliers
    print("Detecting outliers...")
    outliers = detect_outliers_iqr(data)
    filtered_data = filter_outliers(data, outliers)

    # Save filtered data
    filtered_path = paths["processed"] / "filtered_data.parquet"
    filtered_data.to_parquet(filtered_path)
    print(f"Filtered data saved to {filtered_path}")

    # Register checksum
    checksum = calculate_checksum(filtered_path)
    register_checksum_in_state(paths["state"], "PROJ-340-investigating-the-correlation-between-gu.yaml", filtered_path, checksum)

    print(f"[{datetime.now().isoformat()}] Ingestion and validation complete.")
    return filtered_data

def run_analysis(data, paths):
    """Run correlation analysis."""
    print(f"[{datetime.now().isoformat()}] Starting correlation analysis...")
    results = run_correlation_analysis(data)
    output_path = paths["results"] / "correlation_matrix.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Correlation results saved to {output_path}")
    print(f"[{datetime.now().isoformat()}] Analysis complete.")
    return results

def run_diagnostics(data, results, paths):
    """Run diagnostics and sensitivity analysis."""
    print(f"[{datetime.now().isoformat()}] Starting diagnostics...")
    diagnostics = run_collinearity_diagnostics(data, results)
    diagnostics_path = paths["results"] / "diagnostics_report.json"
    with open(diagnostics_path, "w") as f:
        json.dump(diagnostics, f, indent=2, default=str)
    print(f"Diagnostics saved to {diagnostics_path}")
    print(f"[{datetime.now().isoformat()}] Diagnostics complete.")
    return diagnostics

def main():
    parser = argparse.ArgumentParser(description="Gut Microbiome & Sleep Architecture Analysis Pipeline")
    parser.add_argument(
        "--real-data",
        action="store_true",
        help="Switch to real data mode. Requires real data to be present in data/raw/real_data.csv (populated by T043/T044)."
    )
    args = parser.parse_args()

    paths = setup_paths()
    config = load_config(paths["base"] / "data" / "config" / "config.yaml")

    start_time = time.time()

    try:
        # 1. Ingestion & Validation
        data = run_ingestion_and_validation(paths, config, use_real_data=args.real_data)

        # 2. Analysis
        results = run_analysis(data, paths)

        # 3. Diagnostics
        diagnostics = run_diagnostics(data, results, paths)

        # 4. Report Generation
        print(f"[{datetime.now().isoformat()}] Generating final report...")
        end_time = time.time()
        runtime_hours = (end_time - start_time) / 3600

        # Prepare timing evidence
        timing_evidence = {
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": end_time - start_time,
            "duration_hours": runtime_hours,
            "under_6h_limit": runtime_hours < 6.0,
            "data_mode": "real" if args.real_data else "synthetic"
        }

        with open(paths["results"] / "timing_evidence.json", "w") as f:
            json.dump(timing_evidence, f, indent=2)

        # Generate report
        generate_final_report(
            paths,
            results,
            diagnostics,
            timing_evidence,
            data_source="real" if args.real_data else "synthetic"
        )

        if runtime_hours > 6.0:
            print(f"WARNING: Pipeline execution exceeded 6-hour limit ({runtime_hours:.2f} hours).")
        else:
            print(f"Pipeline completed successfully in {runtime_hours:.2f} hours.")

    except Exception as e:
        print(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()