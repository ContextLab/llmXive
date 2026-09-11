"""
Main pipeline entry point for the llmXive automated science project.

Orchestrates the full workflow:
1. Download (Data Ingestion)
2. Preprocess (Alignment & Calibration)
3. Analyze (Spatial Metrics & Correlation)
4. Report (Summary Generation)

Usage:
    python code/main_pipeline.py --config path/to/config.yaml
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config
from utils.update_state import update_state
from utils.ingestion_stats import calculate_ingestion_stats, write_ingestion_stats
from data.ingest import ingest_and_filter_dataset
from preprocess.calibrate import calibrate_and_log, apply_mask_to_dataset
from data.align import create_aligned_dataset
from analysis.spatial_metrics import process_dataset_and_write_metrics
from analysis.aggregate_metrics import aggregate_spatial_metrics
from modeling.correlation import main as correlation_main
from modeling.gam import main as gam_main
from modeling.sensitivity import main as sensitivity_main
from modeling.power_analysis import main as power_analysis_main
from report.generate import main as report_main
from validation.depth_check import main as depth_check_main
from modeling.filter import main as filter_main


def setup_logging(log_path: Path) -> logging.Logger:
    """Configure logging to file and console."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler
    fh = logging.FileHandler(log_path, mode='w')
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def run_download_step(config: dict, logger: logging.Logger) -> bool:
    """Execute the data download and initial ingestion."""
    logger.info("Starting Download Step: Ingesting data from verified sources...")
    try:
        # T014c: Ingest and filter dataset
        # This step handles download, alignment (T012), and masking (T013)
        # It outputs the "pre-filter" unified dataset
        ingest_and_filter_dataset(config)
        
        # Calculate ingestion stats (T010b)
        calculate_ingestion_stats(config)
        write_ingestion_stats(config)
        
        logger.info("Download Step completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Download Step failed: {e}")
        return False


def run_preprocess_step(config: dict, logger: logging.Logger) -> bool:
    """Execute data preprocessing (calibration and masking)."""
    logger.info("Starting Preprocess Step: Calibrating and masking defective regions...")
    try:
        # Apply calibration and masking to the ingested dataset
        # T013: Mask defective regions
        calibrate_and_log(config)
        
        # Ensure masks are applied to the dataset
        apply_mask_to_dataset(config)
        
        # T012: Create aligned dataset (if not already done in ingest)
        # The ingest step handles basic alignment, but this ensures final alignment
        create_aligned_dataset(config)
        
        logger.info("Preprocess Step completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Preprocess Step failed: {e}")
        return False


def run_analyze_step(config: dict, logger: logging.Logger) -> bool:
    """Execute spatial analysis and correlation modeling."""
    logger.info("Starting Analyze Step: Computing spatial metrics and correlations...")
    try:
        # T024/T019: Compute spatial metrics (autocorrelation, Fourier)
        process_dataset_and_write_metrics(config)
        
        # Aggregate metrics
        aggregate_spatial_metrics(config)
        
        # T016/T023: Depth check and co-location validation
        depth_check_main(config)
        
        # T034: Filter samples based on validation flags
        filter_main(config)
        
        # T027/T028: Calculate correlations with BH correction
        correlation_main(config)
        
        # T029: GAM analysis for non-linear relationships
        gam_main(config)
        
        # T030: Robustness check (LOO CV)
        # Assuming robustness is part of the correlation or separate module
        # Importing from analysis.robustness
        from analysis.robustness import main as robustness_main
        robustness_main(config)
        
        # T031c: Sensitivity analysis
        sensitivity_main(config)
        
        # T033: Power analysis
        power_analysis_main(config)
        
        logger.info("Analyze Step completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Analyze Step failed: {e}")
        return False


def run_report_step(config: dict, logger: logging.Logger) -> bool:
    """Generate final summary reports."""
    logger.info("Starting Report Step: Generating summary reports...")
    try:
        report_main(config)
        logger.info("Report Step completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Report Step failed: {e}")
        return False


def update_state_final(config: dict, logger: logging.Logger) -> None:
    """Update the project state file with final artifact hashes."""
    logger.info("Updating project state...")
    try:
        update_state(config)
        logger.info("State updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update state: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Main pipeline for quantifying spatial correlations in perovskite solar cells."
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the configuration YAML file."
    )
    
    args = parser.parse_args()
    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    
    # Load configuration
    config = get_config(config_path)
    
    # Setup logging
    log_dir = Path(config.get("log_dir", "logs"))
    log_file = log_dir / "pipeline.log"
    logger = setup_logging(log_file)
    
    logger.info("Pipeline started.")
    logger.info(f"Configuration loaded from: {config_path}")
    
    # Define pipeline steps
    steps = [
        ("Download", lambda: run_download_step(config, logger)),
        ("Preprocess", lambda: run_preprocess_step(config, logger)),
        ("Analyze", lambda: run_analyze_step(config, logger)),
        ("Report", lambda: run_report_step(config, logger)),
    ]
    
    success = True
    for step_name, step_func in steps:
        logger.info(f"--- Executing {step_name} Step ---")
        if not step_func():
            logger.error(f"Pipeline failed at {step_name} Step.")
            success = False
            break
    
    if success:
        update_state_final(config, logger)
        logger.info("Pipeline completed successfully.")
    else:
        logger.error("Pipeline execution failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()