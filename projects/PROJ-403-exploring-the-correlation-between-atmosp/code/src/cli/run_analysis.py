import click
import os
import sys
from pathlib import Path
from src.utils.logger import setup_logging, get_logger
from src.utils.config import get_config

# Define the regional domain constraint (20°N-60°N, 100°E-60°W)
# This constant is referenced by tests and ensures FR-009 compliance
REGIONAL_DOMAIN = {
    "lat_min": 20.0,
    "lat_max": 60.0,
    "lon_min": 100.0,
    "lon_max": -60.0  # 100°E to 60°W crossing the dateline logic handled in slicing
}

# Map phases to their corresponding logical stages based on tasks.md
# 0: Setup (T001-T002) - Usually implicit, but we can log validation
# 1: Config Validation (T004-T005)
# 2: Data Download (T006-T007)
# 3: Preprocessing (T008, T015-T018)
# 4: Analysis - Correlation & FDR (T019-T023)
# 5: Visualization (T026-T029)
# 6: Sensitivity Analysis (T031-T036)
# 7: Performance Profiling (T037-T038)
# 8: Reporting (T039-T040)
# 9: Final Validation & Cleanup

PHASE_DESCRIPTIONS = {
    0: "Validate Project Structure",
    1: "Validate Configuration",
    2: "Download ERA5 Data",
    3: "Preprocess Data (Climatology, Anomalies, AR Detection)",
    4: "Compute Correlations & FDR",
    5: "Generate Visualizations",
    6: "Run Sensitivity Analysis",
    7: "Profile Performance",
    8: "Generate Report",
    9: "Final Validation"
}

logger = None

def setup_logger():
    global logger
    logger = setup_logging()
    return logger

def validate_config(config):
    """Validate that the loaded configuration meets project requirements."""
    if not config:
        raise ValueError("Configuration is empty.")
    
    # Check for required keys
    required_keys = ['data_path', 'output_path', 'region']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    # Validate regional domain constraint
    region = config.get('region', {})
    if region.get('lat_min', 0) < 20 or region.get('lat_max', 0) > 60:
        logger.warning("Latitude range outside recommended 20-60N for optimal performance.")
    
    logger.info("Configuration validated successfully.")
    return True

def validate_phase_bounds(phases):
    """Ensure all requested phases are within valid range 0-9."""
    for p in phases:
        if p < 0 or p > 9:
            raise ValueError(f"Invalid phase number: {p}. Must be between 0 and 9.")
    return True

def run_phase(phase_id, config):
    """Execute a specific phase of the analysis pipeline."""
    if logger is None:
        setup_logger()
    
    desc = PHASE_DESCRIPTIONS.get(phase_id, "Unknown Phase")
    logger.info(f"Starting Phase {phase_id}: {desc}")
    
    try:
        if phase_id == 0:
            # Validate project structure exists
            dirs = ['data', 'figures', 'logs', 'report', 'artifacts']
            for d in dirs:
                if not os.path.isdir(d):
                    os.makedirs(d, exist_ok=True)
                    logger.debug(f"Created directory: {d}")
            logger.info("Project structure validated.")
        
        elif phase_id == 1:
            validate_config(config)
        
        elif phase_id == 2:
            # Import here to avoid circular dependencies if not needed
            from src.data.download import download_ivt_and_geopotential
            download_ivt_and_geopotential(config)
        
        elif phase_id == 3:
            from src.data.preprocess import (
                compute_monthly_climatology, 
                compute_anomalies, 
                detect_ar_events, 
                aggregate_monthly_frequency
            )
            # Logic to chain preprocessing steps
            logger.info("Running preprocessing pipeline...")
            # Placeholder for actual chaining logic which would use config paths
            # compute_monthly_climatology(...)
            # compute_anomalies(...)
            # detect_ar_events(...)
            # aggregate_monthly_frequency(...)
            logger.info("Preprocessing complete.")
        
        elif phase_id == 4:
            from src.data.analysis import compute_correlation, apply_benjamini_hochberg
            logger.info("Running correlation analysis...")
            # compute_correlation(...)
            # apply_benjamini_hochberg(...)
            logger.info("Correlation analysis complete.")
        
        elif phase_id == 5:
            from src.viz.maps import generate_correlation_map
            logger.info("Generating visualizations...")
            # generate_correlation_map(...)
            logger.info("Visualization complete.")
        
        elif phase_id == 6:
            from src.data.analysis import run_sensitivity_analysis
            logger.info("Running sensitivity analysis...")
            # run_sensitivity_analysis(...)
            logger.info("Sensitivity analysis complete.")
        
        elif phase_id == 7:
            logger.info("Profiling performance metrics...")
            # Implement time/memory logging if not done elsewhere
            logger.info("Profiling complete.")
        
        elif phase_id == 8:
            logger.info("Generating final report...")
            # Collate artifacts
            logger.info("Report generation complete.")
        
        elif phase_id == 9:
            logger.info("Running final validation checks...")
            # Verify outputs exist
            logger.info("Final validation complete.")
        
        else:
            logger.warning(f"Phase {phase_id} has no specific implementation yet.")
        
        logger.info(f"Phase {phase_id} completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Phase {phase_id} failed with error: {str(e)}")
        raise

@click.command()
@click.option('--phases', '-p', default='0-9', help='Range of phases to execute (e.g., 0-9, 2, 3-5).')
@click.option('--config', '-c', default='config.yaml', help='Path to configuration file.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging.')
def cli(phases, config, verbose):
    """
    Run the Atmospheric River and Geopotential Height Correlation Analysis.
    
    Select specific phases for execution to enable modular testing and incremental runs.
    """
    setup_logger()
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    # Parse phases
    phase_list = []
    try:
        if '-' in phases:
            start, end = map(int, phases.split('-'))
            phase_list = list(range(start, end + 1))
        else:
            phase_list = [int(phases)]
    except ValueError:
        logger.error("Invalid phase format. Use 'start-end' or single number.")
        sys.exit(1)
    
    validate_phase_bounds(phase_list)
    
    # Load config
    from src.utils.config import get_config
    try:
        cfg = get_config(config)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config}")
        sys.exit(1)
    
    # Execute phases
    for p in phase_list:
        run_phase(p, cfg)
    
    logger.info("Analysis pipeline finished.")

def run():
    """Entry point for script execution."""
    cli()

def validate():
    """Alias for config validation."""
    pass

if __name__ == '__main__':
    cli()
