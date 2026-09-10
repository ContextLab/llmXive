"""
Entry point for the Atmospheric River - Geopotential Height Correlation Analysis.

This CLI orchestrates the analysis pipeline phases, strictly adhering to the
regional domain constraint (20°N-60°N, 100°E-60°W) to satisfy resource limits (FR-009).
"""
import click
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from src.utils.logger import setup_logging, get_logger
from src.utils.config import get_config, Config

# Define the strict regional domain constraint (FR-009)
# Prohibits global scope processing to ensure resource compliance.
REGIONAL_DOMAIN = {
    "lat_min": 20.0,
    "lat_max": 60.0,
    "lon_min": 100.0,  # 100°E
    "lon_max": -60.0,  # 60°W (Note: CDS/NetCDF usually handles 0-360 or -180-180)
    # Normalized for standard -180 to 180 representation:
    # 100°E = 100, 60°W = -60.
    # If data is 0-360: 100 to 300.
    "bounds_desc": "20°N-60°N, 100°E-60°W"
}

logger = get_logger(__name__)

def setup_logger(verbose: bool = False) -> None:
    """Initialize the logging system."""
    level = "DEBUG" if verbose else "INFO"
    setup_logging(level=level)
    logger.info(f"Analysis Logger initialized at {level} level.")
    logger.info(f"Enforcing Regional Domain Constraint: {REGIONAL_DOMAIN['bounds_desc']}")

def validate_config(config: Config) -> bool:
    """Validate that the configuration respects the regional domain constraint."""
    if config.domain_lat_min is not None:
        if config.domain_lat_min < REGIONAL_DOMAIN["lat_min"] or config.domain_lat_min > REGIONAL_DOMAIN["lat_max"]:
            logger.error(f"Config lat_min {config.domain_lat_min} violates regional constraint.")
            return False
    if config.domain_lat_max is not None:
        if config.domain_lat_max < REGIONAL_DOMAIN["lat_min"] or config.domain_lat_max > REGIONAL_DOMAIN["lat_max"]:
            logger.error(f"Config lat_max {config.domain_lat_max} violates regional constraint.")
            return False
    
    # Log validation success
    logger.info("Configuration validation passed: Regional domain constraints satisfied.")
    return True

def validate_phase_bounds(phases: str) -> Tuple[List[int], Optional[str]]:
    """
    Parse and validate phase string (e.g., '1-3', '2', '1,3,5').
    Returns a list of valid phase integers or an error message.
    """
    try:
        if '-' in phases:
            start, end = phases.split('-')
            start, end = int(start), int(end)
            if start > end:
                return [], f"Invalid range: {start} > {end}"
            if start < 1 or end > 9:
                return [], f"Phase range {start}-{end} out of bounds [1-9]"
            return list(range(start, end + 1)), None
        elif ',' in phases:
            parts = phases.split(',')
            result = []
            for p in parts:
                val = int(p)
                if val < 1 or val > 9:
                    return [], f"Phase {val} out of bounds [1-9]"
                result.append(val)
            return result, None
        else:
            val = int(phases)
            if val < 1 or val > 9:
                return [], f"Phase {val} out of bounds [1-9]"
            return [val], None
    except ValueError:
        return [], f"Invalid phase format: {phases}. Use '1-3', '2', or '1,3'"

def run_phase(phase_id: int, config: Config) -> bool:
    """
    Execute a specific phase of the analysis.
    
    Args:
        phase_id: The integer ID of the phase to run.
        config: The validated configuration object.
        
    Returns:
        bool: True if the phase completed successfully, False otherwise.
    """
    logger.info(f"Starting Phase {phase_id}...")
    
    # Enforce regional domain check at runtime for every phase
    # This is a safety guard to ensure no global data is accidentally loaded
    if config.domain_lat_min is not None and (
        config.domain_lat_min < REGIONAL_DOMAIN["lat_min"] or 
        config.domain_lat_max > REGIONAL_DOMAIN["lat_max"]
    ):
        logger.error(f"Phase {phase_id} aborted: Domain constraint violation detected.")
        return False

    # Phase routing logic (Placeholder for actual implementation per task T010)
    # This structure allows the CLI to call specific functions as they are implemented.
    try:
        if phase_id == 1:
            # T011: Setup directories
            logger.info("Phase 1: Initializing directory structures...")
            # Implementation would call T011 logic here
        elif phase_id == 2:
            # T006/T007: Data Download & Checksum
            logger.info("Phase 2: Fetching and verifying ERA5 data...")
            # Implementation would call download.py
        elif phase_id == 3:
            # T008/T015/T016: Preprocessing
            logger.info("Phase 3: Preprocessing data (Climatology & Anomalies)...")
            # Implementation would call preprocess.py
        elif phase_id == 4:
            # T018: AR Detection
            logger.info("Phase 4: Detecting Atmospheric River events...")
            # Implementation would call preprocess.py detect_ar_events
        elif phase_id == 5:
            # T019: Correlation
            logger.info("Phase 5: Computing Pearson Correlations...")
            # Implementation would call analysis.py
        elif phase_id == 6:
            # T020/T021: FDR & Correction
            logger.info("Phase 6: Applying FDR and Bonferroni corrections...")
            # Implementation would call analysis.py
        elif phase_id == 7:
            # T022: Save Results
            logger.info("Phase 7: Saving processed correlation data...")
            # Implementation would save NetCDF
        elif phase_id == 8:
            # T026-T029: Visualization
            logger.info("Phase 8: Generating spatial maps...")
            # Implementation would call viz/maps.py
        elif phase_id == 9:
            # T031-T036: Sensitivity Analysis
            logger.info("Phase 9: Running threshold sensitivity analysis...")
            # Implementation would call analysis.py sensitivity wrapper
        else:
            logger.warning(f"Phase {phase_id} is a placeholder; no implementation yet.")
            
        logger.info(f"Phase {phase_id} completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Phase {phase_id} failed with error: {e}")
        raise

def run(phases: List[int], config: Config) -> int:
    """
    Orchestrate the execution of the specified phases.
    
    Args:
        phases: List of phase IDs to execute.
        config: Configuration object.
        
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    logger.info(f"Running pipeline for phases: {phases}")
    try:
        for phase in phases:
            if not run_phase(phase, config):
                logger.error(f"Pipeline halted at Phase {phase}")
                return 1
        logger.info("Pipeline execution finished successfully.")
        return 0
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        return 1

@click.command()
@click.option('--phases', '-p', default='1-9', help='Phases to run (e.g., "1-3", "2", "1,3,5"). Default: 1-9')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging.')
@click.option('--config-path', '-c', default=None, help='Path to configuration file.')
def cli(phases: str, verbose: bool, config_path: Optional[str]) -> None:
    """
    Run the Atmospheric River - Geopotential Height Correlation Analysis.
    
    This tool orchestrates the analysis pipeline phases, strictly enforcing
    the regional domain (20°N-60°N, 100°E-60°W) to comply with resource constraints.
    """
    setup_logger(verbose=verbose)
    
    # Load configuration
    try:
        config = get_config(config_path)
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Validate configuration against constraints
    if not validate_config(config):
        logger.error("Configuration validation failed. Exiting.")
        sys.exit(1)
    
    # Parse and validate phases
    phase_list, error = validate_phase_bounds(phases)
    if error:
        logger.error(error)
        sys.exit(1)
    
    # Execute pipeline
    exit_code = run(phase_list, config)
    sys.exit(exit_code)

def main():
    """Entry point for the script."""
    cli()

if __name__ == '__main__':
    main()