"""
Main entry point for the Dark Matter Halo Shape Analysis Pipeline.

This script orchestrates the full research pipeline:
1. Loads configuration and initializes logging.
2. Triggers TNG-100 data ingestion (T011).
3. Triggers inertia tensor and shape metric computation (T012-T014).
4. Triggers statistical analysis and reporting (T021-T025).
5. Handles orientation misalignment (T036-T039) if data is available.
6. Generates final reports (T046).

It acts as the central coordinator, ensuring dependencies are met and
logging is consistent across all stages.
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
from utils.config import load_config, get_project_root, get_data_raw_path, get_data_processed_path, set_random_seed
from utils.logging import (
    get_pipeline_logger, log_pipeline_start, log_pipeline_end,
    log_error, log_metric, log_task_start, log_task_end
)
from utils.io import load_config_safe, get_file_size_mb

# Import pipeline stages (orchestration targets)
# T011: Ingestion
from ingestion.tng_loader import fetch_tng_halo_data, main as tng_loader_main
# T012-T014: Processing
from processing.pipeline_runner import run_pipeline as run_shape_pipeline
# T018: Galaxy properties (integrated into pipeline runner or separate)
# T021-T025: Statistical Analysis
from analysis.run_statistical_analysis import main as run_stats_main
from analysis.sensitivity import main as run_sensitivity_main
# T036-T039: Alignment
from analysis.generate_alignment_report import main as run_alignment_main
# T046: Final Report
from analysis.integrate_alignment_report import main as run_final_report_main

def run_dry_run(logger, config: Dict[str, Any]):
    """
    Validates the pipeline structure and configuration without executing heavy logic.
    """
    logger.info("Running in DRY-RUN mode.")
    logger.info("Validating configuration paths...")
    
    paths_to_check = [
        get_project_root(),
        get_data_raw_path(),
        get_data_processed_path(),
        config.get("logging", {}).get("log_dir", "logs")
    ]
    
    for p_str in paths_to_check:
        p = Path(p_str)
        if not p.exists():
            logger.warning(f"Path does not exist (expected in full run): {p}")
        else:
            logger.info(f"Path OK: {p}")

    logger.info("Configuration validation complete.")
    logger.info("Skipping data processing steps.")
    return True

def run_ingestion_stage(logger, config: Dict[str, Any]) -> bool:
    """
    Executes T011: Data Ingestion.
    Fetches TNG-100 data if not present or if forced.
    """
    log_task_start(logger, "T011", "Data Ingestion")
    try:
        # Check if raw data exists to decide if we need to fetch
        raw_path = get_data_raw_path()
        if not Path(raw_path).exists():
            Path(raw_path).mkdir(parents=True, exist_ok=True)
        
        # Check for existing files
        existing_files = list(Path(raw_path).glob("*"))
        if not existing_files:
            logger.info("No raw data found. Initiating TNG-100 fetch.")
            # Trigger the fetcher
            fetch_tng_halo_data(config)
        else:
            total_size = sum(get_file_size_mb(f) for f in existing_files)
            logger.info(f"Found {len(existing_files)} existing raw files ({total_size:.2f} MB).")
            logger.info("Skipping fetch (data present).")
        
        log_task_end(logger, "T011", "Data Ingestion", success=True)
        return True
    except Exception as e:
        log_error(logger, "T011", f"Data Ingestion failed: {e}")
        return False

def run_processing_stage(logger, config: Dict[str, Any]) -> bool:
    """
    Executes T012-T017: Shape Metrics and Pipeline Processing.
    Computes inertia tensors, axial ratios, and generates halo_shapes.csv.
    """
    log_task_start(logger, "T012-T017", "Shape Processing")
    try:
        # The pipeline_runner handles the chunked loop, inertia calculation,
        # shape metric derivation, filtering, and aggregation.
        success = run_shape_pipeline(config)
        
        if success:
            log_task_end(logger, "T012-T017", "Shape Processing", success=True)
            return True
        else:
            log_error(logger, "T012-T017", "Shape Processing failed or returned False.")
            return False
    except Exception as e:
        log_error(logger, "T012-T017", f"Shape Processing failed: {e}")
        return False

def run_statistics_stage(logger, config: Dict[str, Any]) -> bool:
    """
    Executes T021-T025: Statistical Analysis.
    Runs correlation, regression, and binning tests.
    """
    log_task_start(logger, "T021-T025", "Statistical Analysis")
    try:
        success = run_stats_main(config)
        if not success:
            return False
        
        # Optional: Run sensitivity analysis if configured
        if config.get("analysis", {}).get("run_sensitivity", False):
            logger.info("Running Sensitivity Analysis (T030)...")
            run_sensitivity_main(config)
        
        log_task_end(logger, "T021-T025", "Statistical Analysis", success=True)
        return True
    except Exception as e:
        log_error(logger, "T021-T025", f"Statistical Analysis failed: {e}")
        return False

def run_alignment_stage(logger, config: Dict[str, Any]) -> bool:
    """
    Executes T036-T039: Orientation Misalignment Analysis.
    Computes angles and correlations.
    """
    log_task_start(logger, "T036-T039", "Alignment Analysis")
    try:
        success = run_alignment_main(config)
        if success:
            log_task_end(logger, "T036-T039", "Alignment Analysis", success=True)
            return True
        else:
            log_error(logger, "T036-T039", "Alignment Analysis failed.")
            return False
    except Exception as e:
        log_error(logger, "T036-T039", f"Alignment Analysis failed: {e}")
        return False

def run_final_report_stage(logger, config: Dict[str, Any]) -> bool:
    """
    Executes T046: Final Report Generation.
    Integrates all results into the final markdown report.
    """
    log_task_start(logger, "T046", "Final Report Generation")
    try:
        success = run_final_report_main(config)
        if success:
            log_task_end(logger, "T046", "Final Report Generation", success=True)
            return True
        else:
            log_error(logger, "T046", "Final Report Generation failed.")
            return False
    except Exception as e:
        log_error(logger, "T046", f"Final Report Generation failed: {e}")
        return False

def main():
    """
    Entry point for the pipeline orchestration.
    """
    parser = argparse.ArgumentParser(description="Dark Matter Halo Shape Analysis Pipeline")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Validate setup without processing data')
    parser.add_argument('--stages', type=str, default='all', 
                        help='Comma-separated list of stages to run (ingestion, processing, statistics, alignment, report, all)')
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

    # Set random seed for reproducibility
    seed = config.get("random_seed", 42)
    set_random_seed(seed)
    print(f"Pipeline initialized with random seed: {seed}")

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

    # Determine stages to run
    stages_to_run = []
    if args.stages == 'all':
        stages_to_run = ['ingestion', 'processing', 'statistics', 'alignment', 'report']
    else:
        stages_to_run = [s.strip() for s in args.stages.split(',')]

    if args.dry_run:
        run_dry_run(logger, config)
    else:
        # Execute stages sequentially
        # 1. Ingestion (T011)
        if 'ingestion' in stages_to_run:
            if not run_ingestion_stage(logger, config):
                logger.error("Ingestion failed. Aborting pipeline.")
                log_pipeline_end(logger, success=False, duration=time.time() - start_time)
                return 1

        # 2. Processing (T012-T017)
        if 'processing' in stages_to_run:
            if not run_processing_stage(logger, config):
                logger.error("Processing failed. Aborting pipeline.")
                log_pipeline_end(logger, success=False, duration=time.time() - start_time)
                return 1

        # 3. Statistics (T021-T025)
        if 'statistics' in stages_to_run:
            if not run_statistics_stage(logger, config):
                logger.error("Statistics failed. Aborting pipeline.")
                log_pipeline_end(logger, success=False, duration=time.time() - start_time)
                return 1

        # 4. Alignment (T036-T039)
        if 'alignment' in stages_to_run:
            if not run_alignment_stage(logger, config):
                logger.error("Alignment failed. Aborting pipeline.")
                log_pipeline_end(logger, success=False, duration=time.time() - start_time)
                return 1

        # 5. Final Report (T046)
        if 'report' in stages_to_run:
            if not run_final_report_stage(logger, config):
                logger.error("Final Report failed. Aborting pipeline.")
                log_pipeline_end(logger, success=False, duration=time.time() - start_time)
                return 1

    # Finalize
    duration = time.time() - start_time
    log_metric(logger, "pipeline_duration_seconds", duration)
    
    log_pipeline_end(logger, success=True, duration=duration)
    
    logger.info("Pipeline orchestration finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())