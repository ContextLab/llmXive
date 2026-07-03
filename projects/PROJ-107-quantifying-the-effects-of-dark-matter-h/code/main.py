"""
Main entry point for the Dark Matter Halo Shape Analysis Pipeline.

This script orchestrates the full research pipeline:
1. Loads configuration and initializes logging.
2. (Future) Triggers TNG-100 data ingestion.
3. (Future) Triggers inertia tensor and shape metric computation.
4. (Future) Triggers statistical analysis and reporting.

Currently implements the orchestration skeleton and logging infrastructure
as defined in Phase 2 (Foundational).
"""

import sys
import time
import argparse
from pathlib import Path

# Import project utilities
from utils.config import load_config, get_project_root, get_data_raw_path, get_data_processed_path
from utils.logging import get_pipeline_logger, log_pipeline_start, log_pipeline_end, log_error, log_metric
from utils.io import load_config_safe, get_file_size_mb

def main():
    """
    Entry point for the pipeline orchestration.
    """
    parser = argparse.ArgumentParser(description="Dark Matter Halo Shape Analysis Pipeline")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Validate setup without processing data')
    args = parser.parse_args()

    # Initialize
    start_time = time.time()
    project_root = get_project_root()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"CRITICAL: Failed to load configuration: {e}")
        sys.exit(1)

    # Setup Logger
    logger = get_pipeline_logger("main_pipeline")
    
    log_pipeline_start(logger, config, args)
    
    logger.info("Pipeline initialization complete.")
    logger.info(f"Project Root: {project_root}")
    logger.info(f"Data Raw Path: {get_data_raw_path()}")
    logger.info(f"Data Processed Path: {get_data_processed_path()}")

    # Validate directories exist
    for path_str in [get_data_raw_path(), get_data_processed_path()]:
        p = Path(path_str)
        if not p.exists():
            logger.warning(f"Directory does not exist, creating: {p}")
            p.mkdir(parents=True, exist_ok=True)

    # Check for existing raw data (placeholder for T011)
    raw_path = get_data_raw_path()
    raw_files = list(Path(raw_path).glob("*"))
    if not raw_files:
        logger.info("No raw data found. Pipeline expects TNG-100 data in 'data/raw/'. "
                    "In a full run, T011 (tng_loader) would fetch this here.")
        if not args.dry_run:
            logger.warning("Skipping processing steps due to missing input data.")
            # In a real scenario, we might trigger the fetcher here:
            # from ingestion.tng_loader import fetch_tng_data
            # fetch_tng_data(config)
    else:
        total_size = sum(get_file_size_mb(f) for f in raw_files)
        logger.info(f"Found {len(raw_files)} raw data files ({total_size:.2f} MB).")

    # Pipeline Stages (Orchestration Logic)
    # These are stubs for future tasks (T011-T040) to ensure the main entry point
    # is functional and logs correctly.
    
    stages = [
        ("Data Ingestion", "T011"),
        ("Inertia Tensor Calculation", "T012"),
        ("Shape Metrics Derivation", "T013"),
        ("Statistical Analysis", "T020"),
        ("Report Generation", "T046")
    ]

    if args.dry_run:
        logger.info("DRY RUN: Validating pipeline structure only.")
        for stage_name, task_id in stages:
            logger.info(f"  [Mock] Executing {stage_name} ({task_id})")
    else:
        if not raw_files:
            logger.info("Skipping processing stages due to missing input data.")
        else:
            for stage_name, task_id in stages:
                logger.info(f"Executing {stage_name} ({task_id})...")
                # TODO: Invoke actual processing functions once implemented
                # Example:
                # if task_id == "T011":
                #     from ingestion.tng_loader import process_snapshot
                #     process_snapshot(config)
                time.sleep(0.1) # Placeholder for actual work
                logger.info(f"  Completed {stage_name}.")

    # Finalize
    duration = time.time() - start_time
    log_metric(logger, "pipeline_duration_seconds", duration)
    
    log_pipeline_end(logger, success=True, duration=duration)
    
    logger.info("Pipeline orchestration finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())