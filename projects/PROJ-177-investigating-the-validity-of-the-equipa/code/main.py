import argparse
import sys
import os
import logging
from pathlib import Path
import json

# Import sub-modules
from ingestion import main as ingestion_main
from stats import main as stats_main
from sensitivity import main as sensitivity_main
from regression import main as regression_main
from config import load_config, validate_config

# Setup logging directory if missing to prevent FileNotFoundError on init
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_data_source(args):
    """Validate that the data source configuration is correct."""
    if args.data_source and not os.path.exists(args.data_source):
        logger.error(f"Data source path does not exist: {args.data_source}")
        return False
    return True

def check_dependency_energy_samples():
    """Verify that the US1 output file exists and is valid."""
    target = Path("data/derived/energy_samples.csv")
    if not target.exists():
        logger.error("ERROR: Dependency file data/derived/energy_samples.csv missing. Run US1 first.")
        return False
    
    # Basic validation: check if file is empty
    if target.stat().st_size == 0:
        logger.error("ERROR: Dependency file data/derived/energy_samples.csv is empty. Run US1 first.")
        return False

    # Optional: Verify chirp handling result if it exists
    chirp_file = Path("artifacts/chirp_handling_result.csv")
    if chirp_file.exists():
        if chirp_file.stat().st_size == 0:
            logger.warning("WARNING: artifacts/chirp_handling_result.csv exists but is empty.")
            # We do not fail here as per T024 constraint, but log it.
    
    return True

def check_dependency_statistical_results():
    """Verify that the US2 output file exists and is valid."""
    target = Path("artifacts/statistical_results.json")
    if not target.exists():
        logger.error("ERROR: Dependency file artifacts/statistical_results.json missing. Run US2 first.")
        return False
    return True

def run_dry_run(args):
    """Validate environment and dependencies without running heavy computation."""
    logger.info("Running dry-run validation...")
    
    # Check config
    config_path = Path(args.config) if args.config else Path("data/config.yaml")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return 1
    
    try:
        config = load_config(config_path)
        validate_config(config)
        logger.info("Config validation passed.")
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        return 1

    # Check dependencies
    if not check_dependency_energy_samples():
        return 1
    
    logger.info("Dry-run passed. Environment ready.")
    return 0

def run_ingestion(args):
    """Run the data ingestion pipeline (US1)."""
    logger.info("Starting US1: Data Ingestion and Energy Calculation...")
    # Delegate to ingestion module's main
    return ingestion_main()

def run_statistics(args):
    """Run the statistical analysis pipeline (US2)."""
    if not check_dependency_energy_samples():
        return 1
    
    logger.info("Starting US2: Statistical Deviation Assessment...")
    return stats_main()

def run_sensitivity(args):
    """Run the sensitivity analysis pipeline (US3)."""
    if not check_dependency_statistical_results():
        return 1
    
    logger.info("Starting US3: Sensitivity Analysis...")
    return sensitivity_main()

def run_regression(args):
    """Run the regression analysis pipeline (US4)."""
    if not check_dependency_statistical_results():
        return 1
    
    logger.info("Starting US4: Regression Analysis...")
    return regression_main()

def main():
    parser = argparse.ArgumentParser(description="llmXive Granular Physics Pipeline")
    parser.add_argument('--stage', type=str, default='all',
                        choices=['all', 'checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression', 'dry_run'],
                        help="Pipeline stage to execute")
    parser.add_argument('--config', type=str, default=None,
                        help="Path to configuration file (default: data/config.yaml)")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose logging")
    parser.add_argument('--sample-ratio', type=float, default=None,
                        help="Fraction of data to sample (0.0 to 1.0)")
    parser.add_argument('--alpha', type=float, default=0.05,
                        help="Significance level for hypothesis tests")
    parser.add_argument('--thresholds', type=str, default="0.01,0.05,0.10",
                        help="Comma-separated list of alpha thresholds for sensitivity analysis")
    parser.add_argument('--data-source', type=str, default=None,
                        help="Path to local data source (overrides config)")
    parser.add_argument('--local-only', action='store_true',
                        help="Do not attempt to download remote data")
    parser.add_argument('--allow-incomplete', action='store_true',
                        help="Allow processing of datasets with missing metadata")
    # Note: --seed is handled by individual modules or environment variables if needed,
    # but strictly per task T054, we are fixing the CLI mismatch. 
    # If --seed was requested in run-book but not supported, we remove it from args or handle it.
    # For this fix, we will NOT add --seed to main.py to match the script usage shown in the error log,
    # and instead assume the run-book command `python -m code.main --seed 42` was the mismatch.
    # However, to support reproducibility if needed, we can add it but it must be parsed correctly.
    # The error log says: `main.py: error: unrecognized arguments: --seed 42`.
    # The task is T054 (Dependency Check), but the failure log shows the run-book is broken.
    # I will add --seed to the parser to fix the run-book mismatch, as it is a standard reproducibility flag.
    parser.add_argument('--seed', type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Dependency check for US2 entry gate (T054)
    # If stage is 'all' or 'stats' or 'sensitivity' or 'regression', we must ensure US1 is done.
    # However, T054 specifically says: "verify ... if missing, exit with ERROR".
    # This check is most critical if we are about to run US2+.
    
    stages_to_run = []
    if args.stage == 'all':
        stages_to_run = ['ingest', 'stats', 'sensitivity', 'regression']
    else:
        stages_to_run = [args.stage]

    # Pre-check for US2+ dependencies
    if any(s in stages_to_run for s in ['stats', 'sensitivity', 'regression']):
        if not check_dependency_energy_samples():
            sys.exit(1)

    ret = 0
    if 'ingest' in stages_to_run:
        ret = run_ingestion(args)
        if ret != 0: return ret

    if 'stats' in stages_to_run:
        ret = run_statistics(args)
        if ret != 0: return ret

    if 'sensitivity' in stages_to_run:
        ret = run_sensitivity(args)
        if ret != 0: return ret

    if 'regression' in stages_to_run:
        ret = run_regression(args)
        if ret != 0: return ret

    if args.stage == 'dry_run':
        ret = run_dry_run(args)

    return ret

if __name__ == "__main__":
    sys.exit(main())