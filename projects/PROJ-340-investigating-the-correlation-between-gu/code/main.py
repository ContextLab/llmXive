"""
Pipeline Orchestration Script.
Sequences ingestion, validation, analysis, and diagnostics.
Implements the Real-Data Gate (T082) and timing evidence (T016).
"""
import sys
import os
import json
import time
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main")

def setup_paths():
    """Ensure directory structure exists."""
    dirs = ["data/raw", "data/processed", "data/results", "data/config", "data/metadata"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def estimate_ram_usage(df_size_mb: float) -> str:
    """Estimate RAM usage based on data size."""
    return "low" if df_size_mb < 100 else "medium" if df_size_mb < 1000 else "high"

def determine_compute_strategy(ram_level: str) -> str:
    """Determine compute strategy based on RAM level."""
    return "streaming" if ram_level == "high" else "standard"

def save_compute_strategy(strategy: str, output_path: str = "data/metadata/compute_strategy.json"):
    """Save compute strategy to file."""
    with open(output_path, 'w') as f:
        json.dump({"strategy": strategy}, f, indent=2)

def check_validation_mode():
    """
    Check if the pipeline is running in synthetic validation mode.
    Returns True if validation_mode_flag.json exists and 'active' is True.
    """
    flag_path = "data/metadata/validation_mode_flag.json"
    if not os.path.exists(flag_path):
        return False
    try:
        with open(flag_path, 'r') as f:
            data = json.load(f)
            return data.get("active", False)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read validation mode flag: {e}")
        return False

def run_ingestion_and_validation(input_path: str, mode: str):
    """Run ingestion and validation steps."""
    from ingest import load_data, save_filtered_data, record_checksum, save_outlier_report
    
    logger.info("Starting ingestion and validation...")
    df = load_data(input_path, mode)
    
    # Ensure filtered data exists (side effect of load_data in ingest.py)
    filtered_path = "data/processed/filtered_data.parquet"
    if not os.path.exists(filtered_path):
        logger.warning(f"Filtered data not found at {filtered_path}. Ingestion may have failed to write it.")
    
    logger.info("Ingestion and validation complete.")

def run_analysis():
    """Run correlation analysis."""
    from analysis import main as analysis_main
    logger.info("Starting analysis...")
    analysis_main()
    logger.info("Analysis complete.")

def run_diagnostics():
    """Run diagnostics (VIF, Power, etc.)."""
    from diagnostics import main as diagnostics_main
    logger.info("Starting diagnostics...")
    diagnostics_main()
    logger.info("Diagnostics complete.")

def main():
    parser = argparse.ArgumentParser(description="Pipeline Orchestration")
    parser.add_argument("--input", type=str, help="Input data file")
    parser.add_argument("--mode", type=str, default="real", choices=["real", "synthetic"], help="Data mode")
    parser.add_argument("--output", type=str, default="data/results/", help="Output directory")
    args = parser.parse_args()
    
    setup_paths()
    
    start_time = time.time()
    
    # T082: IMPLEMENT REAL-DATA GATE IN ORCHESTRATION
    # Check for real data existence before proceeding.
    real_data_path = "data/raw/real_data.csv"
    if not os.path.exists(real_data_path):
        is_validation_mode = check_validation_mode()
        if not is_validation_mode:
            logger.error("Real data not found. Aborting pipeline. Please provide a verified real dataset.")
            logger.error("If this is a validation run, ensure 'data/metadata/validation_mode_flag.json' has 'active': true.")
            sys.exit(1)
        else:
            logger.info("Real data not found, but validation mode is active. Proceeding with synthetic data generation.")
            # Trigger synthetic data generation if in validation mode and real data is missing
            from synthetic_data import main as synthetic_main
            synthetic_main()
            # Update input path to the generated synthetic data for subsequent steps
            args.input = "data/raw/synthetic_data.csv"
            logger.info(f"Synthetic data generated at {args.input}. Resuming pipeline.")
    else:
        logger.info("Real data found. Proceeding with real data pipeline.")

    # 1. Ingestion & Validation
    run_ingestion_and_validation(args.input, args.mode)
    
    # 2. Analysis
    run_analysis()
    
    # 3. Diagnostics
    run_diagnostics()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Timing Evidence (T016)
    timing_report = {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "status": "PASS" if duration < 6 * 3600 else "FAIL"
    }
    with open("data/results/timing_evidence.json", 'w') as f:
        json.dump(timing_report, f, indent=2)
    
    logger.info(f"Pipeline complete. Duration: {duration:.2f}s")

if __name__ == "__main__":
    main()