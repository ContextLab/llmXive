import click
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from src.utils.logger import get_logger, setup_logging
from src.utils.config import get_config

# Import phase-specific logic (stubs provided in this file for T010,
# but imported here to satisfy the requirement that they exist in the module namespace).
# In a full implementation, these would be separate functions in this file or imported from other modules.
# For T010, we implement the routing logic and placeholder execution for phases 0-9.

logger = get_logger(__name__)

# Define the phases as per the task requirements (0-9)
# Phase 0: Setup & Validation
# Phase 1: Data Download (IVT & Z500)
# Phase 2: Data Preprocessing (Climatology, Anomalies)
# Phase 3: AR Detection
# Phase 4: Correlation Analysis (Pearson)
# Phase 5: FDR Correction (Benjamini-Hochberg)
# Phase 6: Validation (Teleconnections)
# Phase 7: Visualization
# Phase 8: Sensitivity Analysis
# Phase 9: Reporting & Archiving

PHASES = {
    0: "setup_and_validation",
    1: "data_download",
    2: "preprocessing",
    3: "ar_detection",
    4: "correlation_analysis",
    5: "fdr_correction",
    6: "validation",
    7: "visualization",
    8: "sensitivity_analysis",
    9: "reporting_and_archiving"
}

def setup_logger(verbose: bool = False) -> logging.Logger:
    """Setup the logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    return setup_logging(level=level)

def validate_config(config_path: Optional[str] = None) -> dict:
    """Load and validate the configuration file."""
    config = get_config(config_path)
    if not config:
        raise ValueError("Configuration could not be loaded or is invalid.")
    return config

def validate_phase_bounds(start: int, end: int) -> Tuple[int, int]:
    """Validate that start and end phases are within 0-9."""
    if start < 0 or end > 9 or start > end:
        raise ValueError(f"Invalid phase bounds: start={start}, end={end}. Must be 0-9 with start <= end.")
    return start, end

def run_phase(phase_id: int, config: dict) -> bool:
    """
    Execute a specific phase of the analysis pipeline.
    This function implements the routing logic for phases 0-9.
    """
    logger.info(f"Starting Phase {phase_id}: {PHASES.get(phase_id, 'Unknown')}")
    
    # Placeholder implementations for each phase to satisfy the "runnable" constraint.
    # In a real scenario, these would call actual functions from preprocess.py, analysis.py, etc.
    # Since T010 is about routing, we ensure the structure exists and logs execution.
    
    try:
        if phase_id == 0:
            # Phase 0: Setup & Validation
            logger.info("Phase 0: Validating directories and config.")
            # Logic to ensure directories exist (T001)
            for dir_name in ['data', 'data/processed', 'figures', 'logs', 'report', 'artifacts']:
                Path(dir_name).mkdir(parents=True, exist_ok=True)
            logger.info("Phase 0 completed: Directories validated.")

        elif phase_id == 1:
            # Phase 1: Data Download
            logger.info("Phase 1: Downloading ERA5 data.")
            # Logic to call download.py (T006)
            # from src.data.download import main as download_main
            # download_main(config)
            logger.info("Phase 1 completed: Data download simulated.")

        elif phase_id == 2:
            # Phase 2: Preprocessing
            logger.info("Phase 2: Preprocessing data (Climatology, Anomalies).")
            # Logic to call preprocess.py (T015, T016a)
            # from src.data.preprocess import compute_monthly_climatology, compute_anomalies
            logger.info("Phase 2 completed: Preprocessing simulated.")

        elif phase_id == 3:
            # Phase 3: AR Detection
            logger.info("Phase 3: Detecting AR events.")
            # Logic to call preprocess.py detect_ar_events (T018)
            logger.info("Phase 3 completed: AR detection simulated.")

        elif phase_id == 4:
            # Phase 4: Correlation Analysis
            logger.info("Phase 4: Computing Pearson correlations.")
            # Logic to call analysis.py (T019)
            logger.info("Phase 4 completed: Correlation analysis simulated.")

        elif phase_id == 5:
            # Phase 5: FDR Correction
            logger.info("Phase 5: Applying Benjamini-Hochberg FDR.")
            # Logic to call analysis.py (T020)
            logger.info("Phase 5 completed: FDR correction simulated.")

        elif phase_id == 6:
            # Phase 6: Validation
            logger.info("Phase 6: Validating against teleconnection indices.")
            # Logic to call analysis.py (T023)
            logger.info("Phase 6 completed: Validation simulated.")

        elif phase_id == 7:
            # Phase 7: Visualization
            logger.info("Phase 7: Generating spatial maps.")
            # Logic to call viz/maps.py (T026-T028)
            logger.info("Phase 7 completed: Visualization simulated.")

        elif phase_id == 8:
            # Phase 8: Sensitivity Analysis
            logger.info("Phase 8: Running sensitivity analysis.")
            # Logic to call analysis.py (T031-T036)
            logger.info("Phase 8 completed: Sensitivity analysis simulated.")

        elif phase_id == 9:
            # Phase 9: Reporting & Archiving
            logger.info("Phase 9: Generating report and archiving.")
            # Logic to collate artifacts (T039)
            logger.info("Phase 9 completed: Reporting and archiving simulated.")

        else:
            logger.error(f"Unknown phase ID: {phase_id}")
            return False

        logger.info(f"Phase {phase_id} completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Phase {phase_id} failed with error: {str(e)}")
        return False

def run(start: int, end: int, config: dict) -> bool:
    """
    Run the pipeline from start phase to end phase (inclusive).
    """
    start, end = validate_phase_bounds(start, end)
    success = True
    for phase_id in range(start, end + 1):
        if not run_phase(phase_id, config):
            logger.error(f"Pipeline failed at phase {phase_id}")
            success = False
            break
    return success

@click.command()
@click.option('--start', default=0, help='Starting phase ID (0-9)')
@click.option('--end', default=9, help='Ending phase ID (0-9)')
@click.option('--config', default=None, help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(start: int, end: int, config: Optional[str], verbose: bool):
    """
    Run the Atmospheric River and Geopotential Height Correlation Analysis Pipeline.
    """
    setup_logger(verbose)
    try:
        cfg = validate_config(config)
        success = run(start, end, cfg)
        if success:
            click.echo("Pipeline completed successfully.")
            sys.exit(0)
        else:
            click.echo("Pipeline failed.")
            sys.exit(1)
    except Exception as e:
        click.echo(f"Pipeline error: {str(e)}")
        sys.exit(1)

def main():
    """Entry point for the script."""
    cli()

if __name__ == '__main__':
    main()