"""
Main orchestration script for the granular system analysis pipeline.
"""
import argparse
import sys
import os
import logging
from pathlib import Path
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_data_source(data_source: str) -> bool:
    """Validate that the data source exists."""
    if not Path(data_source).exists():
        logger.error(f"Data source not found: {data_source}")
        return False
    return True

def check_dependency_energy_samples() -> bool:
    """Check if energy_samples.csv exists."""
    path = Path('data/derived/energy_samples.csv')
    if not path.exists():
        logger.error(f"Dependency file data/derived/energy_samples.csv missing. Run US1 first.")
        return False
    return True

def check_dependency_statistical_results() -> bool:
    """Check if statistical_results.json exists."""
    path = Path('artifacts/statistical_results.json')
    if not path.exists():
        logger.error(f"Dependency file artifacts/statistical_results.json missing. Run stats first.")
        return False
    return True

def run_dry_run(args) -> int:
    """Validate all dependencies and paths without executing."""
    logger.info("Running dry-run validation...")
    
    # Check config
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return 1
    
    # Check data source if provided
    if hasattr(args, 'data_source') and args.data_source:
        if not validate_data_source(args.data_source):
            return 1
    
    # Check output directories
    for dir_path in ['data/derived', 'artifacts', 'figures']:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    logger.info("Dry-run validation passed.")
    return 0

def run_ingestion(args) -> int:
    """Run the ingestion stage."""
    logger.info("Starting ingestion stage...")
    
    if args.data_source and not validate_data_source(args.data_source):
        return 1
    
    try:
        from ingestion import main as ingestion_main
        # Prepare arguments for ingestion
        sys.argv = ['ingestion', 
                    '--config', args.config,
                    '--data-source', args.data_source if hasattr(args, 'data_source') else '',
                    '--output-dir', 'data/derived',
                    '--sample-ratio', str(args.sample_ratio) if hasattr(args, 'sample_ratio') else '1.0',
                    '--verbose' if args.verbose else '']
        ingestion_main()
        logger.info("Ingestion stage completed.")
        return 0
    except Exception as e:
        logger.error(f"Ingestion stage failed: {e}")
        return 1

def run_statistics(args) -> int:
    """Run the statistical analysis stage."""
    logger.info("Starting statistics stage...")
    
    if not check_dependency_energy_samples():
        return 1
    
    try:
        from stats import main as stats_main
        sys.argv = ['stats', 
                    '--config', args.config,
                    '--alpha', str(args.alpha) if hasattr(args, 'alpha') else '0.05',
                    '--verbose' if args.verbose else '']
        stats_main()
        logger.info("Statistics stage completed.")
        return 0
    except Exception as e:
        logger.error(f"Statistics stage failed: {e}")
        return 1

def run_sensitivity(args) -> int:
    """Run the sensitivity analysis stage."""
    logger.info("Starting sensitivity stage...")
    
    if not check_dependency_statistical_results():
        return 1
    
    try:
        from sensitivity import main as sensitivity_main
        thresholds = [float(t) for t in args.thresholds.split(',')] if hasattr(args, 'thresholds') else [0.01, 0.05, 0.1]
        sys.argv = ['sensitivity', 
                    '--config', args.config,
                    '--thresholds', ','.join(str(t) for t in thresholds),
                    '--verbose' if args.verbose else '']
        sensitivity_main()
        logger.info("Sensitivity stage completed.")
        return 0
    except Exception as e:
        logger.error(f"Sensitivity stage failed: {e}")
        return 1

def run_regression(args) -> int:
    """Run the regression analysis stage."""
    logger.info("Starting regression stage...")
    
    if not check_dependency_statistical_results():
        return 1
    
    try:
        from regression import main as regression_main
        sys.argv = ['regression', 
                    '--config', args.config,
                    '--verbose' if args.verbose else '']
        regression_main()
        logger.info("Regression stage completed.")
        return 0
    except Exception as e:
        logger.error(f"Regression stage failed: {e}")
        return 1

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Granular System Analysis Pipeline')
    parser.add_argument('--stage', type=str, choices=['all', 'checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression'],
                      default='all', help='Pipeline stage to run')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--sample-ratio', type=float, default=1.0, help='Sampling ratio for large datasets')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level for statistical tests')
    parser.add_argument('--thresholds', type=str, default='0.01,0.05,0.10', help='Comma-separated list of thresholds for sensitivity analysis')
    parser.add_argument('--data-source', type=str, help='Path to data source')
    parser.add_argument('--local-only', action='store_true', help='Use local data only')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    logger.info(f"Starting pipeline with stage: {args.stage}")
    
    if args.stage == 'all':
        stages = ['ingest', 'stats', 'sensitivity', 'regression']
    else:
        stages = [args.stage]
    
    for stage in stages:
        if stage == 'checksum_raw':
            # Placeholder for checksum stage
            logger.info("Checksum stage not implemented in this run.")
            continue
        elif stage == 'hash_artifacts':
            # Placeholder for hash stage
            logger.info("Hash stage not implemented in this run.")
            continue
        elif stage == 'ingest':
            if run_ingestion(args) != 0:
                return 1
        elif stage == 'stats':
            if run_statistics(args) != 0:
                return 1
        elif stage == 'sensitivity':
            if run_sensitivity(args) != 0:
                return 1
        elif stage == 'regression':
            if run_regression(args) != 0:
                return 1
        else:
            logger.error(f"Unknown stage: {stage}")
            return 1
    
    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
