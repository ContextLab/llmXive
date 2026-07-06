import click
import os
import sys
from pathlib import Path
from src.utils.logger import setup_logging, get_logger
from src.utils.config import get_config

logger = None

def validate(ctx, param, value):
    """Validate the phase string input."""
    if value is None:
        return None
    try:
        parts = value.split(',')
        phases = []
        for p in parts:
            p = p.strip()
            if '-' in p:
                start, end = p.split('-')
                s, e = int(start), int(end)
                if s > e:
                    raise ValueError(f"Invalid range: {p}")
                phases.extend(range(s, e + 1))
            else:
                phases.append(int(p))
        
        if not all(0 <= x <= 9 for x in phases):
            raise ValueError("Phases must be integers between 0 and 9.")
        
        return sorted(list(set(phases)))
    except ValueError as e:
        raise click.BadParameter(f"Invalid phase specification: {value}. Error: {e}")

def run_phase(phase_id, config, logger):
    """Execute a specific phase of the analysis pipeline."""
    logger.info(f"Starting Phase {phase_id}")
    
    # Map phase IDs to their respective logic
    # Phase 0: Data Download (T006/T007)
    if phase_id == 0:
        from src.data.download import download_ivt_and_geopotential
        download_ivt_and_geopotential(config, logger)
    
    # Phase 1: Preprocessing & Climatology (T015)
    elif phase_id == 1:
        from src.data.preprocess import compute_monthly_climatology, slice_regional_domain
        slice_regional_domain(config, logger)
        compute_monthly_climatology(config, logger)
    
    # Phase 2: Anomaly Calculation (T016)
    elif phase_id == 2:
        from src.data.preprocess import compute_anomalies
        compute_anomalies(config, logger)
    
    # Phase 3: AR Detection (T018)
    elif phase_id == 3:
        from src.data.preprocess import detect_ar_events
        detect_ar_events(config, logger)
    
    # Phase 4: Correlation Analysis (T019, T020, T021)
    elif phase_id == 4:
        from src.data.analysis import compute_correlations, apply_fdr_correction
        compute_correlations(config, logger)
        apply_fdr_correction(config, logger)
    
    # Phase 5: Visualization (T026, T027, T028)
    elif phase_id == 5:
        from src.viz.maps import generate_correlation_maps
        generate_correlation_maps(config, logger)
    
    # Phase 6: Sensitivity Analysis (T031-T036)
    elif phase_id == 6:
        from src.data.analysis import run_sensitivity_analysis
        run_sensitivity_analysis(config, logger)
    
    # Phase 7: Performance Logging (T037, T038)
    elif phase_id == 7:
        from src.utils.performance import log_performance_metrics
        log_performance_metrics(config, logger)
    
    # Phase 8: Report Generation (T039)
    elif phase_id == 8:
        from src.report.generator import generate_report
        generate_report(config, logger)
    
    # Phase 9: Final Validation (T040)
    elif phase_id == 9:
        from src.validation.checks import run_final_validation
        run_final_validation(config, logger)
    
    else:
        logger.warning(f"Phase {phase_id} is not implemented yet.")
    
    logger.info(f"Completed Phase {phase_id}")

def run(phases, config, logger):
    """Execute the specified phases in order."""
    if not phases:
        logger.info("No phases specified. Running all phases (0-9).")
        phases = list(range(10))
    
    for phase_id in phases:
        try:
            run_phase(phase_id, config, logger)
        except Exception as e:
            logger.error(f"Phase {phase_id} failed: {e}")
            raise click.ClickException(f"Phase {phase_id} failed: {e}")

@click.command()
@click.option(
    '--phase', '-p',
    default=None,
    callback=validate,
    help='Phases to execute (e.g., "0", "1-3", "0,2,5"). If omitted, runs all phases.'
)
@click.option(
    '--config', '-c',
    default='config.yaml',
    type=click.Path(exists=True),
    help='Path to configuration file.'
)
def cli(phase, config):
    """
    Run the Atmospheric River and Geopotential Height Correlation Analysis.
    
    This CLI orchestrates the pipeline phases, allowing selective execution
    via the --phase flag.
    """
    global logger
    logger = setup_logging()
    
    try:
        cfg = get_config(config)
        logger.info("Configuration loaded successfully.")
        
        run(phase, cfg, logger)
        logger.info("Analysis pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()