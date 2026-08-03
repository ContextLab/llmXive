"""
Main orchestration script for the granular system analysis pipeline.
Handles argument parsing and dispatching to stage-specific functions.
"""
import argparse
import sys
import os
import logging
from pathlib import Path
from checksum_raw_data import main as checksum_main
from hash_artifacts import main as hash_main
from ingestion import main as ingestion_main
from stats import main as stats_main
from sensitivity import main as sensitivity_main
from regression import main as regression_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Orchestrate the granular system analysis pipeline."
    )
    parser.add_argument(
        "--stage",
        choices=["all", "checksum_raw", "hash_artifacts", "ingest", "stats", "sensitivity", "regression"],
        default="all",
        help="Which stage of the pipeline to run. 'all' runs everything in order."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="data/config.yaml",
        help="Path to configuration file."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    # Added arguments for specific stages to match quickstart requirements
    parser.add_argument(
        "--sample-ratio",
        type=float,
        default=1.0,
        help="Ratio of data to sample (0.0 to 1.0). Used by ingest stage."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for statistical tests. Used by stats and sensitivity stages."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="0.01,0.05,0.10",
        help="Comma-separated list of thresholds for sensitivity analysis."
    )

    return parser.parse_args()

def run_ingestion(args):
    logger.info("Running ingestion stage...")
    # We need to pass sample_ratio to the ingestion script.
    # Since ingestion.py has its own main, we can simulate CLI args or call the function directly.
    # For simplicity, we'll set sys.argv or call the function if we refactor.
    # Here, we'll call the function directly if we can, or modify ingestion.py to accept args.
    # Let's assume ingestion.py's main() reads from sys.argv.
    # We can temporarily override sys.argv.
    old_argv = sys.argv
    sys.argv = ['ingestion.py', '--input', 'data/raw', '--output', 'data/derived/energy_samples.csv', '--sample-ratio', str(args.sample_ratio)]
    try:
        ingestion_main()
    finally:
        sys.argv = old_argv
    logger.info("Ingestion stage complete.")

def run_statistics(args):
    logger.info("Running statistics stage...")
    old_argv = sys.argv
    sys.argv = ['stats.py', '--input', 'data/derived/energy_samples.csv', '--output', 'artifacts/statistical_results.json', '--alpha', str(args.alpha)]
    try:
        stats_main()
    finally:
        sys.argv = old_argv
    logger.info("Statistics stage complete.")

def run_sensitivity(args):
    logger.info("Running sensitivity stage...")
    old_argv = sys.argv
    # Parse thresholds
    thresholds = [float(x) for x in args.thresholds.split(',')]
    thresholds_str = ','.join(str(t) for t in thresholds)
    sys.argv = ['sensitivity.py', '--input', 'artifacts/statistical_results.json', '--output', 'artifacts/sensitivity_analysis_report.json', '--alpha', str(args.alpha), '--thresholds', thresholds_str]
    try:
        sensitivity_main()
    finally:
        sys.argv = old_argv
    logger.info("Sensitivity stage complete.")

def run_regression(args):
    logger.info("Running regression stage...")
    old_argv = sys.argv
    sys.argv = ['regression.py', '--input', 'artifacts/statistical_results.json', '--output', 'artifacts/regression_results.json']
    try:
        regression_main()
    finally:
        sys.argv = old_argv
    logger.info("Regression stage complete.")

def run_hash_artifacts(args):
    logger.info("Running hash artifacts stage...")
    hash_main()
    logger.info("Hash artifacts stage complete.")

def main():
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    stages_to_run = []
    if args.stage == "all":
        stages_to_run = ["checksum_raw", "ingest", "stats", "sensitivity", "regression", "hash_artifacts"]
    else:
        # Map old names to new names if necessary, but choices are already aligned
        stages_to_run = [args.stage]

    for stage in stages_to_run:
        if stage == "checksum_raw":
            checksum_main()
        elif stage == "ingest":
            run_ingestion(args)
        elif stage == "stats":
            run_statistics(args)
        elif stage == "sensitivity":
            run_sensitivity(args)
        elif stage == "regression":
            run_regression(args)
        elif stage == "hash_artifacts":
            run_hash_artifacts(args)
        else:
            logger.error(f"Unknown stage: {stage}")
            sys.exit(1)

    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    main()
