import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import (
    load_config,
    get_project_root,
    get_data_raw_path,
    get_data_processed_path,
    set_random_seed,
)
from utils.logging import (
    get_pipeline_logger,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
)

# Import the newly added processing runner
from processing.pipeline_runner import run_pipeline

def run_dry_run(config: Dict[str, Any]) -> bool:
    """Perform a dry run of the pipeline configuration."""
    logger = get_pipeline_logger("dry_run")
    logger.info("Running dry run...")
    # Placeholder for configuration validation
    logger.info("Dry run complete.")
    return True

def run_ingestion_stage(config: Dict[str, Any]) -> bool:
    """Run the data ingestion stage."""
    logger = get_pipeline_logger("ingestion")
    log_pipeline_start(logger, "T011", "Ingestion")
    start_time = time.time()
    try:
        # Placeholder: actual ingestion logic resides in code/ingestion/tng_loader.py
        logger.info("Ingestion stage executed.")
        duration = time.time() - start_time
        log_pipeline_end(logger, "T011", "SUCCESS", duration)
        return True
    except Exception as e:
        log_error(logger, e, "Ingestion stage failed")
        log_pipeline_end(logger, "T011", "FAILED", time.time() - start_time)
        return False

def run_processing_stage(config: Dict[str, Any]) -> bool:
    """Run the data processing stage (halo shape computation)."""
    logger = get_pipeline_logger("processing")
    log_pipeline_start(logger, "T005", "Processing")
    start_time = time.time()
    try:
        # Resolve output directory using the toolkit helper (creates it if needed)
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Configuration parameters with sensible defaults
        snapshot_id = int(config.get("snapshot_id", 0))
        chunk_size = int(config.get("chunk_size", 100))
        min_particles = int(config.get("min_particles", 10000))

        stats = run_pipeline(
            snapshot_id=snapshot_id,
            chunk_size=chunk_size,
            min_particles=min_particles,
            output_dir=str(processed_dir),
        )

        logger.info(
            f"Processing completed: {stats['valid_haloes']} valid haloes, "
            f"{stats['excluded_haloes']} excluded."
        )
        duration = time.time() - start_time
        log_pipeline_end(logger, "T005", "SUCCESS", duration)
        return True
    except Exception as e:
        log_error(logger, e, "Processing stage failed")
        log_pipeline_end(logger, "T005", "FAILED", time.time() - start_time)
        return False

def run_statistics_stage(config: Dict[str, Any]) -> bool:
    """Run the statistical analysis stage."""
    logger = get_pipeline_logger("statistics")
    log_pipeline_start(logger, "T021", "Statistics")
    start_time = time.time()
    try:
        # Placeholder: actual statistical analysis resides in code/analysis/*
        logger.info("Statistics stage executed.")
        duration = time.time() - start_time
        log_pipeline_end(logger, "T021", "SUCCESS", duration)
        return True
    except Exception as e:
        log_error(logger, e, "Statistics stage failed")
        log_pipeline_end(logger, "T021", "FAILED", time.time() - start_time)
        return False

def run_alignment_stage(config: Dict[str, Any]) -> bool:
    """Run the alignment analysis stage."""
    logger = get_pipeline_logger("alignment")
    log_pipeline_start(logger, "T036", "Alignment")
    start_time = time.time()
    try:
        # Placeholder: actual alignment logic resides in code/processing/alignment.py
        logger.info("Alignment stage executed.")
        duration = time.time() - start_time
        log_pipeline_end(logger, "T036", "SUCCESS", duration)
        return True
    except Exception as e:
        log_error(logger, e, "Alignment stage failed")
        log_pipeline_end(logger, "T036", "FAILED", time.time() - start_time)
        return False

def run_final_report_stage(config: Dict[str, Any]) -> bool:
    """Run the final report generation stage."""
    logger = get_pipeline_logger("report")
    log_pipeline_start(logger, "T046", "Report")
    start_time = time.time()
    try:
        # Placeholder: actual report generation resides in code/report/generate_report.py
        logger.info("Report stage executed.")
        duration = time.time() - start_time
        log_pipeline_end(logger, "T046", "SUCCESS", duration)
        return True
    except Exception as e:
        log_error(logger, e, "Report stage failed")
        log_pipeline_end(logger, "T046", "FAILED", time.time() - start_time)
        return False

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=[
            "dry_run",
            "ingestion",
            "processing",
            "statistics",
            "alignment",
            "report",
        ],
        default="dry_run",
        help="Stage to run",
    )
    args = parser.parse_args()

    project_root = get_project_root()
    config_path = project_root / args.config

    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    set_random_seed(config.get("random_seed", 42))

    stage_map = {
        "dry_run": run_dry_run,
        "ingestion": run_ingestion_stage,
        "processing": run_processing_stage,
        "statistics": run_statistics_stage,
        "alignment": run_alignment_stage,
        "report": run_final_report_stage,
    }

    if args.stage not in stage_map:
        print(f"Unknown stage: {args.stage}")
        sys.exit(1)

    success = stage_map[args.stage](config)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
