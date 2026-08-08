import argparse
import sys
import os
import logging
from pathlib import Path
import json

from ingestion import ingest_data
from stats import run_statistical_analysis
from sensitivity import run_sensitivity_analysis
from regression import run_regression_analysis
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_data_source(config_path: str) -> bool:
    """Validate that data source is configured."""
    config = load_config(config_path)
    source_id = os.environ.get('DATA_SOURCE_ID') or config.get('data_source', {}).get('source_id')
    if not source_id:
        logger.error("Data source ID missing in config or environment.")
        return False
    return True

def check_dependency_energy_samples() -> bool:
    """Check if energy_samples.csv exists."""
    path = Path("data/derived/energy_samples.csv")
    if not path.exists():
        logger.error(f"Dependency file {path} missing. Run US1 first.")
        return False
    return True

def check_dependency_statistical_results() -> bool:
    """Check if statistical_results.json exists."""
    path = Path("artifacts/statistical_results.json")
    if not path.exists():
        logger.error(f"Dependency file {path} missing. Run stats first.")
        return False
    return True

def run_dry_run(config_path: str) -> None:
    """Validate environment without running computation."""
    logger.info("Running dry run...")
    if not validate_data_source(config_path):
        sys.exit(1)
    logger.info("Dry run passed. Environment ready.")

def run_ingestion(config_path: str, data_source: str, sample_ratio: float, local_only: bool) -> None:
    """Run ingestion stage."""
    logger.info("Running ingestion...")
    ingest_data(config_path, data_source, sample_ratio, local_only)
    logger.info("Ingestion complete.")

def run_statistics(config_path: str, alpha: float) -> None:
    """Run statistics stage."""
    if not check_dependency_energy_samples():
        sys.exit(1)
    logger.info("Running statistics...")
    run_statistical_analysis(config_path, alpha)
    logger.info("Statistics complete.")

def run_sensitivity(config_path: str, thresholds: str) -> None:
    """Run sensitivity stage."""
    if not check_dependency_statistical_results():
        sys.exit(1)
    logger.info("Running sensitivity analysis...")
    threshold_list = [float(t) for t in thresholds.split(',')]
    run_sensitivity_analysis(config_path, threshold_list)
    logger.info("Sensitivity analysis complete.")

def run_regression(config_path: str) -> None:
    """Run regression stage."""
    if not check_dependency_statistical_results():
        sys.exit(1)
    logger.info("Running regression...")
    run_regression_analysis(config_path)
    logger.info("Regression complete.")

def parse_args():
    parser = argparse.ArgumentParser(description="Main orchestration script for granular system analysis.")
    parser.add_argument("--stage", type=str, choices=["all", "checksum_raw", "hash_artifacts", "ingest", "stats", "sensitivity", "regression"],
                      default="all", help="Pipeline stage to run.")
    parser.add_argument("--config", type=str, default="data/config.yaml", help="Path to config file.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("--sample-ratio", type=float, default=None, help="Fraction of data to sample.")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level for statistical tests.")
    parser.add_argument("--thresholds", type=str, default="0.01,0.05,0.10", help="Comma-separated thresholds for sensitivity analysis.")
    parser.add_argument("--data-source", type=str, default=None, help="Data source ID.")
    parser.add_argument("--local-only", action="store_true", help="Enforce local-only mode.")
    parser.add_argument("--dry-run", action="store_true", help="Validate environment without running computation.")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    if args.dry_run:
        run_dry_run(args.config)
        return

    if args.stage == "ingest" or args.stage == "all":
        run_ingestion(args.config, args.data_source, args.sample_ratio, args.local_only)

    if args.stage == "stats" or args.stage == "all":
        run_statistics(args.config, args.alpha)

    if args.stage == "sensitivity" or args.stage == "all":
        run_sensitivity(args.config, args.thresholds)

    if args.stage == "regression" or args.stage == "all":
        run_regression(args.config)

    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    main()
