import click
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import logging
from datetime import datetime

from src.utils.logger import setup_logging, get_logger
from src.data.preprocess import (
    load_chunked_netcdf,
    slice_regional_domain,
    compute_monthly_climatology,
    compute_anomalies,
    detect_ar_events,
    aggregate_monthly_frequency,
    save_processed_dataset
)
from src.utils.config import get_config

# Global configuration for the analysis
# FR-009: Full global grid processing (90°S-90°N, 180°W-180°E)
GLOBAL_LAT_BOUNDS = (-90, 90)
GLOBAL_LON_BOUNDS = (-180, 180)

# Phases defined in the pipeline
PHASES = {
    0: "load_data",
    1: "climatology",
    2: "anomalies",
    3: "ar_detection",
    4: "frequency_aggregation",
    5: "correlation",
    6: "fdr_correction",
    7: "validation",
    8: "visualization",
    9: "sensitivity"
}

def setup_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging for the analysis pipeline."""
    return setup_logging(name, log_file)

def validate_config(config: dict) -> bool:
    """Validate the configuration dictionary."""
    required_keys = ['data_path', 'output_path', 'phases']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    return True

def validate_phase_bounds(phases: List[int]) -> bool:
    """Validate that requested phases are within valid range."""
    if not phases:
        return False
    for p in phases:
        if p < 0 or p > 9:
            raise ValueError(f"Invalid phase number: {p}. Must be 0-9.")
    return True

def run_phase(
    phase_id: int,
    config: dict,
    logger: logging.Logger,
    data_cache: Optional[dict] = None
) -> dict:
    """
    Execute a specific phase of the analysis pipeline.
    
    This function implements the domain filtering logic for FR-009,
    ensuring that all operations respect the full global grid bounds
    (90°S-90°N, 180°W-180°E) using streaming/chunked operations.
    
    Args:
        phase_id: The phase to execute (0-9)
        config: Configuration dictionary
        logger: Logger instance
        data_cache: Optional cache for intermediate data
        
    Returns:
        Updated data cache with phase results
    """
    if data_cache is None:
        data_cache = {}

    logger.info(f"Starting Phase {phase_id}: {PHASES.get(phase_id, 'Unknown')}")
    
    # Global domain parameters for FR-009 compliance
    lat_bounds = GLOBAL_LAT_BOUNDS
    lon_bounds = GLOBAL_LON_BOUNDS

    try:
        if phase_id == 0:
            # Load raw data with streaming/chunked operations
            raw_ivt_path = os.path.join(config['data_path'], 'ivt_raw.nc')
            raw_z500_path = os.path.join(config['data_path'], 'z500_raw.nc')
            
            logger.info(f"Loading IVT data from {raw_ivt_path} with global domain filtering")
            ds_ivt = load_chunked_netcdf(
                raw_ivt_path, 
                chunks={'time': 12, 'lat': 36, 'lon': 72},
                lat_bounds=lat_bounds,
                lon_bounds=lon_bounds
            )
            
            logger.info(f"Loading Z500 data from {raw_z500_path} with global domain filtering")
            ds_z500 = load_chunked_netcdf(
                raw_z500_path,
                chunks={'time': 12, 'lat': 36, 'lon': 72},
                lat_bounds=lat_bounds,
                lon_bounds=lon_bounds
            )
            
            data_cache['ds_ivt'] = ds_ivt
            data_cache['ds_z500'] = ds_z500
            logger.info("Phase 0 completed: Data loaded with global domain filtering")

        elif phase_id == 1:
            # Compute monthly climatology
            if 'ds_ivt' not in data_cache or 'ds_z500' not in data_cache:
                raise RuntimeError("Phase 0 must be completed before Phase 1")
            
            logger.info("Computing monthly climatology for global dataset...")
            climatology = compute_monthly_climatology(
                data_cache['ds_ivt'],
                dim='time',
                freq='MS'
            )
            data_cache['climatology_ivt'] = climatology
            logger.info("Phase 1 completed: Climatology computed")

        elif phase_id == 2:
            # Compute anomalies
            if 'climatology_ivt' not in data_cache:
                raise RuntimeError("Phase 1 must be completed before Phase 2")
            
            logger.info("Computing anomalies by subtracting climatology...")
            anomalies = compute_anomalies(
                data_cache['ds_z500'],
                data_cache['climatology_ivt'], # Using Z500 for anomalies, IVT for AR
                dim='time'
            )
            data_cache['anomalies'] = anomalies
            logger.info("Phase 2 completed: Anomalies computed")

        elif phase_id == 3:
            # Detect AR events
            if 'ds_ivt' not in data_cache:
                raise RuntimeError("Phase 0 must be completed before Phase 3")
            
            logger.info("Detecting AR events with global domain filtering...")
            ar_mask = detect_ar_events(
                data_cache['ds_ivt'],
                threshold=250.0, # kg m^-1 s^-1
                min_duration=24, # hours
                connectivity=8
            )
            data_cache['ar_mask'] = ar_mask
            logger.info("Phase 3 completed: AR events detected")

        elif phase_id == 4:
            # Aggregate monthly frequency
            if 'ar_mask' not in data_cache:
                raise RuntimeError("Phase 3 must be completed before Phase 4")
            
            logger.info("Aggregating monthly AR frequency...")
            freq_data = aggregate_monthly_frequency(
                data_cache['ar_mask'],
                time_dim='time'
            )
            data_cache['ar_frequency'] = freq_data
            logger.info("Phase 4 completed: Monthly frequency aggregated")

        elif phase_id == 5:
            # Compute correlation (placeholder for T019)
            logger.info("Phase 5: Correlation computation (to be implemented in T019)")
            # This would call analysis.py functions

        elif phase_id == 6:
            # Apply FDR correction (placeholder for T020)
            logger.info("Phase 6: FDR correction (to be implemented in T020)")
            # This would call analysis.py functions

        elif phase_id == 7:
            # Validation (placeholder for T023)
            logger.info("Phase 7: Validation (to be implemented in T023)")

        elif phase_id == 8:
            # Visualization (placeholder for T026-T029)
            logger.info("Phase 8: Visualization (to be implemented in T026-T029)")

        elif phase_id == 9:
            # Sensitivity analysis (placeholder for T031-T036)
            logger.info("Phase 9: Sensitivity analysis (to be implemented in T031-T036)")

        else:
            raise ValueError(f"Unknown phase ID: {phase_id}")

        logger.info(f"Phase {phase_id} completed successfully")
        return data_cache

    except Exception as e:
        logger.error(f"Phase {phase_id} failed with error: {str(e)}")
        raise

def run(config_path: str, phases: Optional[List[int]] = None, output_dir: Optional[str] = None):
    """
    Run the analysis pipeline with domain filtering for the full global grid.
    
    Args:
        config_path: Path to the YAML configuration file
        phases: List of phases to run (default: all)
        output_dir: Override output directory
    """
    logger = setup_logger("run_analysis")
    config = get_config(config_path)
    
    if not validate_config(config):
        raise ValueError("Invalid configuration")
    
    if phases is None:
        phases = list(range(10))
    
    if not validate_phase_bounds(phases):
        raise ValueError("Invalid phase bounds")
    
    if output_dir:
        config['output_path'] = output_dir
    
    data_cache = {}
    
    for phase_id in phases:
        data_cache = run_phase(phase_id, config, logger, data_cache)
        
        # Save intermediate results if needed
        if phase_id == 4:
            # Save AR frequency data
            output_path = os.path.join(config['output_path'], 'processed', 'ar_freq_global.nc')
            save_processed_dataset(
                data_cache['ar_frequency'],
                output_path,
                global_bounds=True
            )
            logger.info(f"Saved AR frequency to {output_path}")

@click.command()
@click.option('--config', '-c', default='config.yaml', help='Path to config file')
@click.option('--phases', '-p', default=None, help='Comma-separated list of phases to run')
@click.option('--output', '-o', default=None, help='Output directory override')
def cli(config, phases, output):
    """CLI entry point for the AR-Z500 correlation analysis pipeline."""
    phase_list = None
    if phases:
        phase_list = [int(p.strip()) for p in phases.split(',')]
    
    try:
        run(config, phase_list, output)
        click.echo("Analysis pipeline completed successfully.")
    except Exception as e:
        click.echo(f"Analysis pipeline failed: {str(e)}", err=True)
        sys.exit(1)

def main():
    """Main entry point."""
    cli()

if __name__ == '__main__':
    main()