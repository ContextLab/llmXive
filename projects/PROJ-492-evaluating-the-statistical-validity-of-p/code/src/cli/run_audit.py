import argparse
import json
import logging
import sys
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.utils.resource_monitor import ResourceMonitor, check_resource_limits
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.audit.power_analysis import run_power_analysis
from code.src.audit.validator import write_audit_report
from code.src.audit.prevalence import run_prevalence_analysis
from code.src.audit.report_generator import generate_summary_report
from code.src.audit.export_validator import run_export_validation
from code.src.utils.manifest import generate_manifest
from code.src.config import set_rng_seed, get_config_summary

logger: AuditLogger = get_default_logger(__name__)


def setup_paths(args: argparse.Namespace) -> Dict[str, Path]:
    """Initialize directory paths based on arguments or defaults."""
    base_path = Path(args.base_path) if args.base_path else Path.cwd()
    
    paths = {
        "base": base_path,
        "input": base_path / "input",
        "data_raw": base_path / "data" / "raw",
        "data_synthetic": base_path / "data" / "synthetic",
        "output": base_path / "output",
        "logs": base_path / "logs",
    }
    
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
        
    return paths


def run_monte_carlo_startup_validation(paths: Dict[str, Path]) -> None:
    """Run Monte Carlo validation at startup to ensure statistical integrity."""
    logger.info("Running Monte Carlo startup validation...")
    try:
        run_monte_carlo_validation()
        logger.info("Monte Carlo validation passed.")
    except Exception as e:
        logger.error(f"Monte Carlo validation failed: {e}")
        raise


def run_power_analysis_step(paths: Dict[str, Path]) -> None:
    """Run power analysis to verify corpus size requirements."""
    logger.info("Running power analysis...")
    try:
        run_power_analysis(paths["output"])
        logger.info("Power analysis completed.")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise


def run_full_pipeline(paths: Dict[str, Path], input_file: Optional[Path] = None) -> None:
    """Execute the main audit pipeline: ingest -> fetch -> extract -> reconstruct -> validate."""
    logger.info("Starting full audit pipeline...")
    
    # Import pipeline components locally to avoid circular imports if any
    from code.src.audit.ingestor import ingest_and_deduplicate
    from code.src.audit.fetcher import ingest_and_fetch
    from code.src.audit.extractor import extract_all
    from code.src.audit.reconstructor import reconstruct_tests
    from code.src.audit.validator import validate_all_summaries
    
    # 1. Ingest
    logger.info("Step 1: Ingesting URLs...")
    if not input_file:
        input_file = paths["input"] / "urls.csv"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    deduped_urls_path = paths["output"] / "urls_deduped.csv"
    ingest_and_deduplicate(input_file, deduped_urls_path)
    
    # 2. Fetch
    logger.info("Step 2: Fetching HTML...")
    ingest_and_fetch(deduped_urls_path, paths["data_raw"])
    
    # 3. Extract
    logger.info("Step 3: Extracting summaries...")
    extracted_summaries_path = paths["output"] / "extracted_summaries.json"
    extract_all(deduped_urls_path, paths["data_raw"], extracted_summaries_path)
    
    # 4. Reconstruct
    logger.info("Step 4: Reconstructing statistical tests...")
    reconstructed_path = paths["output"] / "reconstructed_tests.json"
    reconstruct_tests(extracted_summaries_path, reconstructed_path)
    
    # 5. Validate
    logger.info("Step 5: Validating consistency...")
    audit_report_path = paths["output"] / "audit_report.json"
    validate_all_summaries(reconstructed_path, audit_report_path)
    
    logger.info("Full pipeline completed.")


def run_prevalence_and_reporting(paths: Dict[str, Path]) -> None:
    """Run prevalence analysis and generate reports."""
    logger.info("Running prevalence analysis and reporting...")
    
    # Prevalence
    run_prevalence_analysis(paths["output"])
    
    # Report Generation
    generate_summary_report(paths["output"])
    
    logger.info("Prevalence and reporting completed.")


def generate_manifest_and_validate(paths: Dict[str, Path]) -> None:
    """Generate manifest and validate export consistency."""
    logger.info("Generating manifest and validating exports...")
    
    # Generate Manifest
    generate_manifest(paths["output"])
    
    # Validate Exports
    run_export_validation(paths["output"])
    
    logger.info("Manifest generated and exports validated.")


def main():
    parser = argparse.ArgumentParser(
        description="Run the A/B Test Validity Audit Pipeline."
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base directory for input/output data. Defaults to current working directory."
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to the input URLs CSV file."
    )
    parser.add_argument(
        "--skip-monte-carlo",
        action="store_true",
        help="Skip the initial Monte Carlo validation step."
    )
    
    args = parser.parse_args()
    
    # Setup logging and paths
    paths = setup_paths(args)
    logger.info(f"Audit pipeline started at {datetime.now().isoformat()}")
    logger.info(f"Base path: {paths['base']}")
    
    try:
        # 0. Resource Monitor Check (NEW FOR T063)
        # Initialize the monitor and check limits immediately. 
        # If limits are exceeded, this function will log ERR-301 and abort.
        logger.info("Checking resource limits...")
        monitor = ResourceMonitor()
        if not check_resource_limits(monitor):
            # check_resource_limits logs the error and returns False on failure
            logger.critical("Resource limits exceeded. Aborting pipeline.")
            sys.exit(1)
        
        # 1. Monte Carlo Validation
        if not args.skip_monte_carlo:
            run_monte_carlo_startup_validation(paths)
        
        # 2. Power Analysis
        run_power_analysis_step(paths)
        
        # 3. Main Pipeline
        input_file = Path(args.input_file) if args.input_file else None
        run_full_pipeline(paths, input_file)
        
        # 4. Prevalence & Reporting
        run_prevalence_and_reporting(paths)
        
        # 5. Manifest & Export Validation
        generate_manifest_and_validate(paths)
        
        logger.info("Pipeline execution completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()