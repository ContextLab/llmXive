"""
Main orchestration script for the Equipartition Theorem Validity Pipeline.
Handles dependency checks, stage execution, and CLI argument parsing.
"""
import argparse
import sys
import os
import logging
from pathlib import Path
import json

from config import load_config, validate_config
from ingestion import main as run_ingestion_main
from stats import main as run_stats_main
from sensitivity import main as run_sensitivity_main
from regression import main as run_regression_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants for dependency paths
DEPENDENCY_ENERGY_SAMPLES = "data/derived/energy_samples.csv"
DEPENDENCY_STATISTICAL_RESULTS = "artifacts/statistical_results.json"
DEPENDENCY_CONFIG = "data/config.yaml"

def validate_data_source(args):
    """
    Validates the data source provided via CLI or config.
    Returns True if valid, False otherwise.
    """
    if args.data_source:
        path = Path(args.data_source)
        if not path.exists():
            logger.error(f"Data source not found: {path}")
            return False
        if not path.is_file():
            logger.error(f"Data source is not a file: {path}")
            return False
    return True

def check_dependency_energy_samples():
    """
    Verifies that the energy_samples.csv file exists and is valid.
    Exits the program with an error message if missing or invalid.
    This is the specific implementation for T054.
    """
    path = Path(DEPENDENCY_ENERGY_SAMPLES)
    
    if not path.exists():
        logger.error(f"ERROR: Dependency file {DEPENDENCY_ENERGY_SAMPLES} missing. Run US1 first.")
        sys.exit(1)
    
    if path.stat().st_size == 0:
        logger.error(f"ERROR: Dependency file {DEPENDENCY_ENERGY_SAMPLES} is empty. Run US1 first.")
        sys.exit(1)

    # Basic validation: check if it looks like a CSV with headers
    try:
        with open(path, 'r') as f:
            header = f.readline().strip()
            if not header:
                logger.error(f"ERROR: Dependency file {DEPENDENCY_ENERGY_SAMPLES} has no header. Run US1 first.")
                sys.exit(1)
            # Check for expected columns
            required_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib']
            headers = [h.strip() for h in header.split(',')]
            missing = [col for col in required_cols if col not in headers]
            if missing:
                logger.warning(f"Warning: Missing expected columns in {DEPENDENCY_ENERGY_SAMPLES}: {missing}. Proceeding with caution.")
        
        logger.info(f"Dependency check passed: {DEPENDENCY_ENERGY_SAMPLES} exists and is valid.")
        return True
    except Exception as e:
        logger.error(f"ERROR: Failed to validate {DEPENDENCY_ENERGY_SAMPLES}: {e}")
        sys.exit(1)

def check_dependency_statistical_results():
    """
    Verifies that statistical_results.json exists.
    """
    path = Path(DEPENDENCY_STATISTICAL_RESULTS)
    if not path.exists():
        logger.error(f"ERROR: Dependency file {DEPENDENCY_STATISTICAL_RESULTS} missing. Run US2 first.")
        sys.exit(1)
    logger.info(f"Dependency check passed: {DEPENDENCY_STATISTICAL_RESULTS} exists.")
    return True

def run_dry_run(args):
    """
    Validates all dependencies and configuration without executing heavy computation.
    """
    logger.info("Running dry-run validation...")
    
    # Check config
    if not Path(DEPENDENCY_CONFIG).exists():
        logger.error(f"ERROR: Config file {DEPENDENCY_CONFIG} missing.")
        return False
    
    # Check data source if provided
    if args.data_source and not validate_data_source(args):
        return False

    # Check US1 dependency if stats/sensitivity/regression stages are requested
    stages_to_check = ['stats', 'sensitivity', 'regression']
    if args.stage in stages_to_check or args.stage == 'all':
        if not check_dependency_energy_samples():
            return False

    # Check US2 dependency if sensitivity/regression stages are requested
    if args.stage in ['sensitivity', 'regression'] or args.stage == 'all':
        if not check_dependency_statistical_results():
            return False

    logger.info("Dry-run validation completed successfully.")
    return True

def run_ingestion(args):
    """
    Executes the ingestion pipeline (US1).
    """
    logger.info("Starting ingestion pipeline...")
    
    # Prepare args for ingestion module
    ingestion_args = argparse.Namespace(
        data_source=args.data_source,
        sample_ratio=args.sample_ratio,
        local_only=args.local_only,
        verbose=args.verbose,
        config=args.config,
        chirp_handling=args.chirp_handling if hasattr(args, 'chirp_handling') else 'exclude'
    )
    
    # Run ingestion main
    # Note: ingestion.py main expects specific args, mapping them here
    return run_ingestion_main(ingestion_args)

def run_statistics(args):
    """
    Executes the statistical analysis pipeline (US2).
    """
    logger.info("Starting statistical analysis pipeline...")
    check_dependency_energy_samples()
    
    # Prepare args for stats module
    stats_args = argparse.Namespace(
        config=args.config,
        alpha=args.alpha,
        verbose=args.verbose,
        local_only=args.local_only
    )
    
    return run_stats_main(stats_args)

def run_sensitivity(args):
    """
    Executes the sensitivity analysis pipeline (US3).
    """
    logger.info("Starting sensitivity analysis pipeline...")
    check_dependency_statistical_results()
    
    # Parse thresholds
    thresholds = [float(t) for t in args.thresholds.split(',')] if args.thresholds else [0.01, 0.05, 0.10]
    
    sensitivity_args = argparse.Namespace(
        config=args.config,
        alpha=args.alpha,
        thresholds=thresholds,
        verbose=args.verbose,
        local_only=args.local_only
    )
    
    return run_sensitivity_main(sensitivity_args)

def run_regression(args):
    """
    Executes the regression analysis pipeline (US4).
    """
    logger.info("Starting regression analysis pipeline...")
    check_dependency_statistical_results()
    
    regression_args = argparse.Namespace(
        config=args.config,
        verbose=args.verbose,
        local_only=args.local_only
    )
    
    return run_regression_main(regression_args)

def main():
    parser = argparse.ArgumentParser(
        description="Equipartition Theorem Validity Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--stage',
        type=str,
        choices=['all', 'checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression'],
        default='all',
        help='Pipeline stage to execute. Default: all'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='data/config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--sample-ratio',
        type=float,
        default=1.0,
        help='Ratio of data to sample (0.0 to 1.0)'
    )
    
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level for statistical tests'
    )
    
    parser.add_argument(
        '--thresholds',
        type=str,
        default='0.01,0.05,0.10',
        help='Comma-separated list of thresholds for sensitivity analysis'
    )
    
    parser.add_argument(
        '--data-source',
        type=str,
        default=None,
        help='Path to the input data source (CSV)'
    )
    
    parser.add_argument(
        '--local-only',
        action='store_true',
        help='Run only on local data, skip remote fetching'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle dry-run if explicitly requested or if stage is 'all' but we just want to validate
    if args.stage == 'all' and args.sample_ratio == 1.0 and not args.data_source:
        # Default behavior for 'all' without specific flags might be to run everything,
        # but let's respect the dependency checks first.
        pass

    # Execute based on stage
    success = True
    
    if args.stage in ['all', 'ingest']:
        # Ingestion stage does not require previous dependency checks (it produces them)
        if not run_ingestion(args):
            success = False
            if args.stage == 'all':
                logger.error("Stopping 'all' run due to ingestion failure.")
                sys.exit(1)

    if args.stage in ['all', 'stats']:
        if success:
            if not run_statistics(args):
                success = False
                if args.stage == 'all':
                    logger.error("Stopping 'all' run due to stats failure.")
                    sys.exit(1)

    if args.stage in ['all', 'sensitivity']:
        if success:
            if not run_sensitivity(args):
                success = False
                if args.stage == 'all':
                    logger.error("Stopping 'all' run due to sensitivity failure.")
                    sys.exit(1)

    if args.stage in ['all', 'regression']:
        if success:
            if not run_regression(args):
                success = False
                if args.stage == 'all':
                    logger.error("Stopping 'all' run due to regression failure.")
                    sys.exit(1)

    if success:
        logger.info("Pipeline execution completed successfully.")
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()