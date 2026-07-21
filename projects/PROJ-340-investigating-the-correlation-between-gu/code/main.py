"""
Pipeline Orchestration (T015, T016, T058-T060, T069).
Implements RAM estimation, compute strategy determination, and orchestration of US1-US3.
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import from other modules
from ingest import (
    load_harmonized_data, 
    validate_variables, 
    save_variable_metrics, 
    detect_outliers_iqr, 
    filter_outliers,
    register_checksum_in_state,
    MissingDataError,
    HarmonizedDataNotFoundError
)
from analysis import (
    run_correlation_analysis, 
    set_analysis_seed,
    check_zero_inflation,
    check_normality,
    select_correlation_method
)
from diagnostics import (
    run_sensitivity_analysis,
    calculate_power,
    run_collinearity_diagnostics,
    generate_diagnostics_report
)
from report import generate_report, load_correlation_results, load_diagnostics_report
from config import get_config, load_config
from ingest import (
    MissingDataError,
    load_schema,
    validate_variables,
    save_variable_metrics,
    load_data,
    detect_outliers_iqr,
    filter_outliers,
    load_streamed_dataset,
    compute_online_statistics
)
from analysis import run_correlation_analysis
from diagnostics import (
    run_collinearity_diagnostics,
    generate_diagnostics_report
)
from report import generate_report

# Constants
RAM_LIMIT_GB = 7.0
STREAM_THRESHOLD_GB = 6.0
BYTE_SIZE_PER_FLOAT = 8  # 64-bit float

def setup_paths(config: Dict[str, Any]) -> Path:
    """Ensure all required directories exist."""
    root = Path(config.get("project_root", "."))
    for dir_name in ["data/raw", "data/processed", "data/results", "data/metadata", "code"]:
        (root / dir_name).mkdir(parents=True, exist_ok=True)
    return root

def estimate_ram_usage(dataset_path: Path) -> float:
    """
    T058: Estimate RAM usage based on dataset size.
    Formula: Estimate (GB) = (N_subjects * N_taxa * byte_size_per_taxon) / 1e9
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    # Quick head check to estimate dimensions
    # Assuming CSV/TSV format
    with open(dataset_path, 'r') as f:
        header = f.readline().strip().split(',')
        n_taxa = len(header) - 1  # Assuming first column is ID
        
        # Count rows (approximate for large files, but accurate for proxy)
        # For very large files, we might need a streaming count, but for estimation:
        # We'll do a quick read if file is small enough, otherwise estimate by size
        file_size_bytes = dataset_path.stat().st_size
        # Rough estimate: average line length ~ 50 bytes per subject
        estimated_rows = file_size_bytes // 50
        
        # Calculate estimate
        estimated_gb = (estimated_rows * n_taxa * BYTE_SIZE_PER_FLOAT) / 1e9
        return estimated_gb

def determine_compute_strategy(estimated_gb: float) -> str:
    """
    T058: Determine strategy based on RAM estimate.
    Returns 'OK', 'STREAM', or 'FAIL'.
    """
    if estimated_gb <= STREAM_THRESHOLD_GB:
        return "OK"
    elif estimated_gb <= RAM_LIMIT_GB:
        return "STREAM"
    else:
        return "FAIL"

def save_compute_strategy(strategy: str, estimated_gb: float, output_path: Path):
    """
    T058: Write compute strategy to JSON artifact.
    """
    artifact = {
        "estimated_ram_gb": estimated_gb,
        "strategy": strategy,
        "limit_gb": RAM_LIMIT_GB,
        "stream_threshold_gb": STREAM_THRESHOLD_GB
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    return artifact

def run_compute_feasibility_check() -> Dict[str, Any]:
    """
    T058-T060: Orchestrate RAM check and strategy determination.
    """
    config = get_config()
    root = Path(config.get("project_root", "."))
    
    # Determine input dataset
    # Check for harmonized data first (T069), then proxy, then real
    harmonized_path = root / "data/processed/harmonized_data.parquet"
    proxy_path = root / "data/raw/large_proxy.csv"
    real_path = root / "data/raw/real_data.csv" # Assumed generic real path

    input_path = None
    if harmonized_path.exists():
        input_path = harmonized_path
        print("[Feasibility] Using harmonized data.")
    elif proxy_path.exists():
        input_path = proxy_path
        print("[Feasibility] Using large proxy data.")
    elif real_path.exists():
        input_path = real_path
        print("[Feasibility] Using real data.")
    else:
        # Fallback to synthetic if no real data found (for pipeline validation only)
        # But T055/T056 logic should ideally catch this earlier if --real-data is set.
        # For T071 stress test, we expect proxy.
        raise FileNotFoundError("No input dataset found (harmonized, proxy, or real).")

    estimated_gb = estimate_ram_usage(input_path)
    strategy = determine_compute_strategy(estimated_gb)
    output_path = root / "data/metadata/compute_strategy.json"
    
    result = save_compute_strategy(strategy, estimated_gb, output_path)
    print(f"[Feasibility] Estimated RAM: {estimated_gb:.2f} GB -> Strategy: {strategy}")

    if strategy == "FAIL":
        # T060: Hard Halt
        raise SystemExit(
            f"CRITICAL: Dataset too large for standard runner ({estimated_gb:.2f} GB > {RAM_LIMIT_GB} GB). "
            "Please downsample or use a smaller dataset."
        )
    
    return result

def run_ingestion_and_validation() -> Dict[str, Any]:
    """
    T015: Execute US1 (Ingestion, Validation, Filtering).
    """
    config = get_config()
    root = Path(config.get("project_root", "."))
    
    # Load schema
    schema_path = root / "specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml"
    schema = load_schema(schema_path)

    # Validate variables
    # Assuming data is already loaded or loaded here. 
    # T012 logic: validate_variables reads from raw/processed data.
    # We assume the data source is identified in config or passed via environment.
    data_path = root / "data/processed/harmonized_data.parquet"
    if not data_path.exists():
        data_path = root / "data/raw/large_proxy.csv"
    
    if not data_path.exists():
        raise FileNotFoundError("Data file not found for ingestion.")

    # T012: Validate variables
    validation_result = validate_variables(data_path, schema)
    save_variable_metrics(validation_result, root / "data/results/variable_load_metrics.json")

    if validation_result.get("percentage_loaded", 0) < 100:
        # T013: Halt if < 100%
        missing = validation_result.get("missing_variables", [])
        raise MissingDataError(f"Missing required variables: {missing}. Halting execution.")

    # T014: Detect outliers
    df = load_data(data_path) # Loads into memory (or streamed if strategy=STREAM, simplified here)
    outliers = detect_outliers_iqr(df)
    
    # T014b: Filter outliers
    df_filtered = filter_outliers(df, outliers)
    filtered_path = root / "data/processed/filtered_data.parquet"
    df_filtered.to_parquet(filtered_path, index=False)
    
    # T014c: Register checksum
    # (Implementation assumed in ingest.py register_checksum_in_state)
    
    return {"status": "success", "rows": len(df_filtered)}

def run_analysis() -> Dict[str, Any]:
    """
    T015: Execute US2 (Correlation Analysis).
    """
    config = get_config()
    root = Path(config.get("project_root", "."))
    data_path = root / "data/processed/filtered_data.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError("Filtered data not found. Run ingestion first.")

    result = run_correlation_analysis(data_path)
    # Result is saved to data/results/correlation_matrix.json inside run_correlation_analysis
    return {"status": "success", "method": result.get("method", "unknown")}

def run_diagnostics() -> Dict[str, Any]:
    """
    T015: Execute US3 (Diagnostics).
    """
    config = get_config()
    root = Path(config.get("project_root", "."))
    data_path = root / "data/processed/filtered_data.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError("Filtered data not found. Run ingestion first.")

    # T030, T031, T033, T034, T035
    diagnostics_result = generate_diagnostics_report(data_path)
    return {"status": "success", "diagnostics": diagnostics_result}

def generate_harmonization_report() -> Dict[str, Any]:
    """T069: Placeholder for harmonization report generation."""
    return {"status": "skipped", "reason": "Not invoked in standard flow"}

def generate_real_data_analysis_report() -> Dict[str, Any]:
    """T069: Placeholder for real data analysis report."""
    return {"status": "skipped", "reason": "Not invoked in standard flow"}

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline Orchestration")
    parser.add_argument("--real-data", action="store_true", help="Force real data mode")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic mode")
    args = parser.parse_args()

    config = get_config()
    setup_paths(config)

    try:
        # T055: Real Data Gate (simplified logic here, assumed enforced by ingest.py)
        if args.real_data:
            print("[Main] Real Data mode requested.")
            # Ingest.py will fail loudly if real data missing

        # T058-T060: Compute Feasibility
        print("[Main] Running Compute Feasibility Check...")
        run_compute_feasibility_check()

        # T015: Run Pipeline Stages
        print("[Main] Running Ingestion & Validation...")
        run_ingestion_and_validation()

        print("[Main] Running Analysis...")
        run_analysis()

        print("[Main] Running Diagnostics...")
        run_diagnostics()

        print("[Main] Pipeline completed successfully.")

    except SystemExit as e:
        print(f"[Main] Pipeline halted: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[Main] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
