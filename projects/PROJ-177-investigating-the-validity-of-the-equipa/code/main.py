import argparse
import sys
import os
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

def validate_data_source(data_source: str) -> bool:
    """Validate that the data source exists."""
    path = Path(data_source)
    if not path.exists():
        logger.error(f"Data source not found: {data_source}")
        return False
    return True

def check_dependency_energy_samples() -> bool:
    """Check that energy_samples.csv exists."""
    path = Path("data/derived/energy_samples.csv")
    if not path.exists():
        logger.error("Dependency file data/derived/energy_samples.csv missing. Run US1 first.")
        return False
    return True

def check_dependency_statistical_results() -> bool:
    """Check that statistical_results.json exists."""
    path = Path("artifacts/statistical_results.json")
    if not path.exists():
        logger.error("Dependency file artifacts/statistical_results.json missing. Run US2 first.")
        return False
    return True

def run_dry_run(args) -> int:
    """Validate environment without running computation."""
    logger.info("Running dry-run validation...")
    
    # Check config
    if not Path("data/config.yaml").exists():
        logger.error("data/config.yaml not found")
        return 1
    
    # Check data source if provided
    if args.data_source:
        if not validate_data_source(args.data_source):
            return 1
    
    logger.info("Dry-run passed. Environment is ready.")
    return 0

def run_ingestion(args) -> int:
    """Run the ingestion pipeline stage."""
    logger.info("Starting ingestion stage...")
    
    from ingestion import main as ingestion_main
    
    # Prepare args for ingestion module
    ingestion_args = argparse.Namespace(
        data_source=args.data_source,
        sample_ratio=args.sample_ratio,
        allow_incomplete=args.allow_incomplete if hasattr(args, 'allow_incomplete') else False,
        verbose=args.verbose
    )
    
    return ingestion_main(ingestion_args)

def run_statistics(args) -> int:
    """Run the statistical analysis stage."""
    logger.info("Starting statistical analysis stage...")
    
    if not check_dependency_energy_samples():
        return 1
    
    from stats import main as stats_main
    
    stats_args = argparse.Namespace(
        alpha=args.alpha,
        verbose=args.verbose
    )
    
    return stats_main(stats_args)

def run_sensitivity(args) -> int:
    """Run the sensitivity analysis stage."""
    logger.info("Starting sensitivity analysis stage...")
    
    if not check_dependency_statistical_results():
        return 1
    
    from sensitivity import main as sensitivity_main
    
    thresholds = [float(t) for t in args.thresholds.split(',')] if args.thresholds else [0.01, 0.05, 0.10]
    
    sensitivity_args = argparse.Namespace(
        thresholds=thresholds,
        verbose=args.verbose
    )
    
    return sensitivity_main(sensitivity_args)

def run_regression(args) -> int:
    """Run the regression analysis stage."""
    logger.info("Starting regression analysis stage...")
    
    if not check_dependency_statistical_results():
        return 1
    
    from regression import main as regression_main
    
    return regression_main(args)

def main():
    parser = argparse.ArgumentParser(
        description='llmXive Pipeline: Investigating Equipartition Theorem in Granular Systems'
    )
    
    parser.add_argument(
        '--stage',
        choices=['all', 'checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression', 'dry_run'],
        default='all',
        help='Pipeline stage to execute'
    )
    
    parser.add_argument(
        '--config',
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
        help='Fraction of data to sample (0.0-1.0)'
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
        help='Comma-separated list of alpha thresholds for sensitivity analysis'
    )
    
    parser.add_argument(
        '--data-source',
        type=str,
        default=None,
        help='Path or identifier for data source'
    )
    
    parser.add_argument(
        '--local-only',
        action='store_true',
        help='Only use local data, do not attempt remote fetch'
    )
    
    parser.add_argument(
        '--allow-incomplete',
        action='store_true',
        help='Allow processing of datasets with incomplete metadata'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.stage == 'dry_run':
        return run_dry_run(args)
    
    elif args.stage == 'ingest':
        return run_ingestion(args)
    
    elif args.stage == 'stats':
        return run_statistics(args)
    
    elif args.stage == 'sensitivity':
        return run_sensitivity(args)
    
    elif args.stage == 'regression':
        return run_regression(args)
    
    elif args.stage == 'all':
        # Run full pipeline
        logger.info("Running full pipeline...")
        
        stages = ['ingest', 'stats', 'sensitivity', 'regression']
        for stage in stages:
            logger.info(f"Executing stage: {stage}")
            if stage == 'ingest':
                ret = run_ingestion(args)
            elif stage == 'stats':
                ret = run_statistics(args)
            elif stage == 'sensitivity':
                ret = run_sensitivity(args)
            elif stage == 'regression':
                ret = run_regression(args)
            
            if ret != 0:
                logger.error(f"Stage {stage} failed with code {ret}")
                return ret
        
        logger.info("Full pipeline completed successfully.")
        return 0
    
    else:
        logger.error(f"Unknown stage: {args.stage}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
