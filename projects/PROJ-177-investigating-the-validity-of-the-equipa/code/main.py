"""
Main orchestration script for the granular system analysis pipeline.
Handles argument parsing and dispatches to stage-specific functions.
"""
import argparse
import sys
import os
import logging
from pathlib import Path

from checksum_raw_data import main as checksum_main
from hash_artifacts import main as hash_main
from ingestion import main as ingest_main
from stats import main as stats_main
from generate_sensitivity_report import main as sensitivity_main
from regression import main as regression_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Granular System Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--stage',
        choices=['all', 'checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression'],
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
        default=None,
        help='Sampling ratio for large datasets (0.0 to 1.0)'
    )

    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance threshold for statistical tests'
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
        default='local',
        help='Data source identifier (local path or dataset ID)'
    )

    parser.add_argument(
        '--local-only',
        action='store_true',
        help='Enforce local-only mode, disallowing remote fetches'
    )

    return parser.parse_args()

def run_ingestion(args):
    """Run the ingestion stage."""
    logger.info("Starting ingestion stage...")
    # Prepare args for ingestion module
    sys.argv = [
        'ingestion',
        '--config', args.config,
        '--data-source', args.data_source,
        '--local-only' if args.local_only else '',
    ]
    if args.sample_ratio is not None:
        sys.argv.extend(['--sample-ratio', str(args.sample_ratio)])
    # Filter out empty strings
    sys.argv = [arg for arg in sys.argv if arg]
    ingest_main()
    logger.info("Ingestion stage completed.")

def run_statistics(args):
    """Run the statistics stage."""
    logger.info("Starting statistics stage...")
    # Prepare args for stats module
    sys.argv = [
        'stats',
        '--config', args.config,
        '--alpha', str(args.alpha)
    ]
    stats_main()
    logger.info("Statistics stage completed.")

def run_sensitivity(args):
    """Run the sensitivity analysis stage."""
    logger.info("Starting sensitivity analysis stage...")
    # Prepare args for sensitivity module
    sys.argv = [
        'sensitivity',
        '--config', args.config,
        '--thresholds', args.thresholds
    ]
    sensitivity_main()
    logger.info("Sensitivity analysis stage completed.")

def run_regression(args):
    """Run the regression analysis stage."""
    logger.info("Starting regression analysis stage...")
    # Prepare args for regression module
    sys.argv = [
        'regression',
        '--config', args.config
    ]
    regression_main()
    logger.info("Regression analysis stage completed.")

def run_hash_artifacts(args):
    """Run the artifact hashing stage."""
    logger.info("Starting artifact hashing stage...")
    hash_main()
    logger.info("Artifact hashing stage completed.")

def main():
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Ensure directories exist
    Path('data/derived').mkdir(parents=True, exist_ok=True)
    Path('artifacts').mkdir(parents=True, exist_ok=True)

    if args.stage == 'all':
        logger.info("Running full pipeline...")
        run_ingestion(args)
        run_statistics(args)
        run_sensitivity(args)
        run_regression(args)
        run_hash_artifacts(args)
    elif args.stage == 'checksum_raw':
        checksum_main()
    elif args.stage == 'hash_artifacts':
        run_hash_artifacts(args)
    elif args.stage == 'ingest':
        run_ingestion(args)
    elif args.stage == 'stats':
        run_statistics(args)
    elif args.stage == 'sensitivity':
        run_sensitivity(args)
    elif args.stage == 'regression':
        run_regression(args)
    else:
        logger.error(f"Unknown stage: {args.stage}")
        sys.exit(1)

if __name__ == '__main__':
    main()
