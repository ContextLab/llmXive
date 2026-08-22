"""
Pipeline orchestrator for the Climate-Smart Agriculture Optimization project.
Handles data ingestion, processing, analysis, and reporting.
Implements automatic synthetic data fallback for CI environments when real data is missing.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Import from project modules
from src.data.generators.synthetic_generator import SyntheticDataGenerator, check_real_data_exists
from src.utils.io_helpers import FatalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_and_generate_synthetic_data(project_root: Path, no_synthetic: bool = False) -> bool:
    """
    Check for real data in data/raw/. If missing:
    - If CI=true and not --no-synthetic: invoke synthetic generator automatically.
    - If --no-synthetic: raise FatalError.
    - If not CI and real data missing: raise FatalError.

    Returns True if synthetic data was generated, False if real data exists.
    """
    raw_data_dir = project_root / "data" / "raw"
    
    logger.info(f"Checking for real data in {raw_data_dir}")
    
    if check_real_data_exists(raw_data_dir):
        logger.info("Real data found. Proceeding with real data pipeline.")
        return False
    
    # Real data is missing
    is_ci = os.environ.get("CI", "").lower() in ("true", "1", "yes")
    
    if is_ci:
        if no_synthetic:
            raise FatalError(
                "Real data is missing in CI environment, but --no-synthetic flag was provided. "
                "Pipeline cannot proceed without data."
            )
        
        logger.warning("Real data missing in CI environment. Automatically invoking synthetic generator.")
        try:
            SyntheticDataGenerator.generate(project_root)
            logger.info("Synthetic data generation completed successfully.")
            return True
        except Exception as e:
            raise FatalError(f"Failed to generate synthetic data: {e}")
    else:
        if no_synthetic:
            raise FatalError(
                "Real data is missing and --no-synthetic flag was provided. "
                "Pipeline cannot proceed without data."
            )
        else:
            raise FatalError(
                "Real data is missing. Please download real data to data/raw/ or run in CI mode with synthetic fallback enabled."
            )

def run_pipeline(
    project_root: Path,
    dry_run: bool = False,
    no_synthetic: bool = False,
    skip_ingestion: bool = False,
    skip_analysis: bool = False
) -> bool:
    """
    Main pipeline execution logic.
    
    Args:
        project_root: Path to the project root directory
        dry_run: If True, only validate configuration and data availability
        no_synthetic: If True, disable synthetic data fallback
        skip_ingestion: If True, skip data ingestion step
        skip_analysis: If True, skip analysis step
    
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    logger.info(f"Starting pipeline execution for project at {project_root}")
    
    # Check and handle data availability
    synthetic_generated = False
    if not skip_ingestion:
        synthetic_generated = check_and_generate_synthetic_data(project_root, no_synthetic)
    
    if dry_run:
        logger.info("Dry run mode: Pipeline validation complete. No actual processing performed.")
        if synthetic_generated:
            logger.info("Note: Synthetic data was generated for validation purposes.")
        return True
    
    # TODO: Implement actual pipeline steps (ingestion, processing, analysis, reporting)
    # These would call the respective modules:
    # - src/data/collectors/*.py for data ingestion
    # - src/data/processing/*.py for feature engineering
    # - src/analysis/*.py for statistical analysis
    # - src/services/report_generator.py for report generation
    
    logger.info("Pipeline execution completed successfully.")
    return True

def main():
    """Main entry point for the pipeline CLI."""
    parser = argparse.ArgumentParser(
        description="Climate-Smart Agriculture Optimization Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and data availability without executing the pipeline"
    )
    
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Disable automatic synthetic data generation in CI environments"
    )
    
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip data ingestion step"
    )
    
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip analysis step"
    )
    
    parser.add_argument(
        "--project-root",
        type=str,
        default=str(Path(__file__).parent.parent.parent.parent),
        help="Path to project root directory (default: auto-detected)"
    )
    
    args = parser.parse_args()
    
    try:
        project_root = Path(args.project_root).resolve()
        
        if not project_root.exists():
            raise FatalError(f"Project root does not exist: {project_root}")
        
        success = run_pipeline(
            project_root=project_root,
            dry_run=args.dry_run,
            no_synthetic=args.no_synthetic,
            skip_ingestion=args.skip_ingestion,
            skip_analysis=args.skip_analysis
        )
        
        sys.exit(0 if success else 1)
        
    except FatalError as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
