"""
Main orchestration script for the Equipartition Theorem Investigation pipeline.
Handles argument parsing, dependency checking, and stage execution.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
import json
import shutil

# Configure logging directory creation
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")


def validate_data_source(args):
    """Validate the data source configuration."""
    if not args.data_source and not args.local_only:
        logger.warning("No data source specified. Running in local-only mode if --local-only is set.")
    return True


def check_dependency_energy_samples():
    """Check if energy_samples.csv exists and is valid."""
    path = Path("data/derived/energy_samples.csv")
    if not path.exists():
        logger.error(f"Dependency file {path} missing. Run US1 first.")
        return False
    if path.stat().st_size == 0:
        logger.error(f"Dependency file {path} is empty.")
        return False
    return True


def check_dependency_statistical_results():
    """Check if statistical_results.json exists and is valid."""
    path = Path("artifacts/statistical_results.json")
    if not path.exists():
        logger.error(f"Dependency file {path} missing. Run US2 first.")
        return False
    try:
        with open(path, 'r') as f:
            json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Dependency file {path} is not valid JSON.")
        return False
    return True


def run_dry_run(args):
    """Validate all dependencies, file paths, and configuration schemas without execution."""
    logger.info("Running dry-run validation...")
    
    # Check config
    config_path = Path(args.config) if args.config else Path("data/config.yaml")
    if not config_path.exists():
        logger.error(f"Config file {config_path} not found.")
        return False
    
    # Check data source if not local-only
    if not args.local_only and not args.data_source:
        logger.error("Data source required unless --local-only is set.")
        return False
    
    # Check specific dependencies if requested
    if not check_dependency_energy_samples():
        return False
    
    logger.info("Dry-run validation passed.")
    return True


def run_ingestion(args):
    """Execute the data ingestion stage."""
    logger.info("Starting ingestion stage...")
    
    # Import and run ingestion main
    from ingestion import main as ingestion_main
    
    # Prepare args for ingestion
    ingestion_args = argparse.Namespace(
        config=args.config,
        data_source=args.data_source,
        local_only=args.local_only,
        allow_incomplete=args.allow_incomplete,
        streaming=args.streaming if hasattr(args, 'streaming') else False,
        sample_ratio=args.sample_ratio
    )
    
    return ingestion_main(ingestion_args)


def run_statistics(args):
    """Execute the statistical analysis stage."""
    logger.info("Starting statistical analysis stage...")
    
    if not check_dependency_energy_samples():
        return False
    
    from stats import main as stats_main
    
    stats_args = argparse.Namespace(
        config=args.config,
        alpha=args.alpha,
        thresholds=args.thresholds,
        data_source=args.data_source
    )
    
    return stats_main(stats_args)


def run_sensitivity(args):
    """Execute the sensitivity analysis stage."""
    logger.info("Starting sensitivity analysis stage...")
    
    if not check_dependency_statistical_results():
        return False
    
    from sensitivity import main as sensitivity_main
    
    sensitivity_args = argparse.Namespace(
        config=args.config,
        alpha=args.alpha,
        thresholds=args.thresholds
    )
    
    return sensitivity_main(sensitivity_args)


def run_regression(args):
    """Execute the regression analysis stage."""
    logger.info("Starting regression analysis stage...")
    
    if not check_dependency_statistical_results():
        return False
    
    from regression import main as regression_main
    
    regression_args = argparse.Namespace(
        config=args.config
    )
    
    return regression_main(regression_args)


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Equipartition Theorem Investigation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--stage',
        type=str,
        choices=['all', 'checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression', 'dry_run'],
        default='all',
        help='Pipeline stage to execute'
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
        help='Fraction of data to sample (0.0 to 1.0)'
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
        help='Path to data source or Zenodo ID'
    )
    
    parser.add_argument(
        '--local-only',
        action='store_true',
        help='Only process local data, do not attempt downloads'
    )
    
    parser.add_argument(
        '--allow-incomplete',
        action='store_true',
        help='Allow processing of datasets with missing metadata'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    
    parser.add_argument(
        '--streaming',
        action='store_true',
        help='Enable streaming mode for large datasets'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.seed is not None:
        import numpy as np
        import random
        random.seed(args.seed)
        np.random.seed(args.seed)
        logger.info(f"Random seed set to {args.seed}")
    
    # Validate data source
    if not validate_data_source(args):
        return False
    
    # Execute stages
    if args.stage == 'all':
        stages = ['checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression']
    else:
        stages = [args.stage]
    
    success = True
    for stage in stages:
        logger.info(f"Executing stage: {stage}")
        try:
            if stage == 'checksum_raw':
                from checksum_raw_data import main as checksum_main
                checksum_main()
            elif stage == 'hash_artifacts':
                from hash_artifacts import main as hash_main
                hash_main()
            elif stage == 'ingest':
                if not run_ingestion(args):
                    success = False
                    break
            elif stage == 'stats':
                if not run_statistics(args):
                    success = False
                    break
            elif stage == 'sensitivity':
                if not run_sensitivity(args):
                    success = False
                    break
            elif stage == 'regression':
                if not run_regression(args):
                    success = False
                    break
            elif stage == 'dry_run':
                if not run_dry_run(args):
                    success = False
                    break
            else:
                logger.error(f"Unknown stage: {stage}")
                success = False
                break
        except Exception as e:
            logger.error(f"Stage {stage} failed with error: {e}")
            success = False
            break
    
    if success:
        logger.info("Pipeline completed successfully.")
    else:
        logger.error("Pipeline failed.")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())