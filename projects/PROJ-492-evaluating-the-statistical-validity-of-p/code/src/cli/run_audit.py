"""
End-to-end driver script for the A/B test audit pipeline.
Orchestrates: ingestion -> fetch -> extract -> reconstruct -> validate -> report -> manifest
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import SEED, set_rng_seed
from code.src.audit.ingestor import ingest_and_deduplicate
from code.src.audit.fetcher import fetch_urls_batch
from code.src.audit.extractor import extract_all, write_summaries_to_json
from code.src.audit.reconstructor import reconstruct_all
from code.src.audit.validator import validate_all_summaries, write_audit_report
from code.src.audit.power_analysis import run_power_analysis
from code.src.audit.evaluation import run_evaluation_step
from code.src.audit.prevalence import run_prevalence_analysis
from code.src.audit.report_generator import generate_summary_report, generate_subgroup_report
from code.src.audit.subgroup_analysis import run_subgroup_analysis
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.utils.manifest import generate_manifest, validate_manifest
from code.src.contracts.validation import validate_audit_record

logger = get_default_logger(__name__)

def setup_paths(input_dir: str = "input", output_dir: str = "output", data_dir: str = "data") -> Dict[str, Path]:
    """Set up and validate directory paths."""
    paths = {
        "input": Path(input_dir).resolve(),
        "output": Path(output_dir).resolve(),
        "data": Path(data_dir).resolve(),
        "raw": Path(data_dir) / "raw",
        "synthetic": Path(data_dir) / "synthetic",
    }

    for path_name, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created/verified directory: {path}")

    return paths

def run_monte_carlo_startup_validation() -> bool:
    """
    Run Monte-Carlo validation at startup to verify statistical functions.
    Returns True if all validations pass, False otherwise.
    """
    logger.info("Running startup Monte-Carlo validation...")
    try:
        # Run the validation module
        success = run_monte_carlo_validation()
        if not success:
            logger.error("Monte-Carlo validation failed. Aborting pipeline.")
            return False
        logger.info("Monte-Carlo validation passed.")
        return True
    except Exception as e:
        logger.error(f"Monte-Carlo validation error: {e}")
        return False

def run_power_analysis_step(paths: Dict[str, Path]) -> bool:
    """Run power analysis to verify corpus size requirements."""
    logger.info("Running power analysis...")
    try:
        success = run_power_analysis(
            audit_report_path=paths["output"] / "audit_report.json",
            output_path=paths["output"] / "power_analysis.json"
        )
        if not success:
            logger.error("Power analysis failed. Aborting pipeline.")
            return False
        logger.info("Power analysis completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Power analysis error: {e}")
        return False

def run_full_pipeline(paths: Dict[str, Path], input_urls: Optional[Path] = None) -> bool:
    """
    Run the full audit pipeline: ingest -> fetch -> extract -> reconstruct -> validate.
    """
    logger.info("Starting full audit pipeline...")

    # Step 1: Ingest and deduplicate URLs
    logger.info("Step 1: Ingesting URLs...")
    urls_path = input_urls or paths["input"] / "urls.csv"
    if not urls_path.exists():
        logger.error(f"Input URLs file not found: {urls_path}")
        return False
    
    deduped_urls_path = paths["output"] / "urls_deduped.csv"
    success = ingest_and_deduplicate(urls_path, deduped_urls_path)
    if not success:
        logger.error("URL ingestion failed.")
        return False

    # Step 2: Fetch HTML
    logger.info("Step 2: Fetching HTML...")
    success = fetch_urls_batch(deduped_urls_path, paths["raw"])
    if not success:
        logger.error("HTML fetching failed.")
        return False

    # Step 3: Extract summaries
    logger.info("Step 3: Extracting summaries...")
    summaries_path = paths["output"] / "extracted_summaries.json"
    success = extract_all(paths["raw"], summaries_path)
    if not success:
        logger.error("Extraction failed.")
        return False

    # Step 4: Reconstruct statistical tests
    logger.info("Step 4: Reconstructing statistical tests...")
    reconstructed_path = paths["output"] / "reconstructed_tests.json"
    success = reconstruct_all(summaries_path, reconstructed_path)
    if not success:
        logger.error("Reconstruction failed.")
        return False

    # Step 5: Validate and create audit records
    logger.info("Step 5: Validating summaries...")
    audit_report_path = paths["output"] / "audit_report.json"
    success = validate_all_summaries(reconstructed_path, audit_report_path)
    if not success:
        logger.error("Validation failed.")
        return False

    logger.info("Full pipeline completed successfully.")
    return True

def run_evaluation_step(paths: Dict[str, Path]) -> bool:
    """Run evaluation on synthetic dataset if available."""
    logger.info("Running evaluation step...")
    synthetic_csv = paths["synthetic"] / "synthetic_validation.csv"
    ground_truth = paths["synthetic"] / "synthetic_ground_truth.json"
    
    if synthetic_csv.exists() and ground_truth.exists():
        success = run_evaluation_step(
            synthetic_csv=synthetic_csv,
            ground_truth=ground_truth,
            audit_report=paths["output"] / "audit_report.json",
            output_path=paths["output"] / "evaluation_results.json"
        )
        if not success:
            logger.error("Evaluation failed. Aborting.")
            return False
        logger.info("Evaluation completed successfully.")
    else:
        logger.info("No synthetic dataset found, skipping evaluation.")
    
    return True

def run_prevalence_and_reporting(paths: Dict[str, Path]) -> bool:
    """Run prevalence analysis and generate reports."""
    logger.info("Running prevalence analysis and generating reports...")
    
    # Run prevalence analysis
    audit_report_path = paths["output"] / "audit_report.json"
    if not audit_report_path.exists():
        logger.error("Audit report not found for prevalence analysis.")
        return False
    
    success = run_prevalence_analysis(
        audit_report_path=audit_report_path,
        output_path=paths["output"] / "prevalence.json"
    )
    if not success:
        logger.error("Prevalence analysis failed.")
        return False

    # Generate summary report
    success = generate_summary_report(
        audit_report_path=audit_report_path,
        prevalence_path=paths["output"] / "prevalence.json",
        output_path=paths["output"] / "summary_report.csv"
    )
    if not success:
        logger.error("Summary report generation failed.")
        return False

    # Run subgroup analysis
    success = run_subgroup_analysis(
        audit_report_path=audit_report_path,
        output_json=paths["output"] / "subgroup_report.json",
        output_csv=paths["output"] / "subgroup_report.csv"
    )
    if not success:
        logger.error("Subgroup analysis failed.")
        return False

    logger.info("Prevalence and reporting completed successfully.")
    return True

def generate_manifest_and_validate(paths: Dict[str, Path]) -> bool:
    """
    Generate manifest with SHA256 hashes for all output and data files.
    Validates the manifest after generation.
    """
    logger.info("Generating manifest...")
    
    manifest_path = paths["output"] / "manifest.json"
    manifest_data = generate_manifest(
        output_dir=paths["output"],
        data_dir=paths["data"],
        manifest_path=manifest_path
    )
    
    if not manifest_data:
        logger.error("Failed to generate manifest.")
        return False
    
    # Validate the generated manifest
    is_valid, errors = validate_manifest(manifest_path)
    if not is_valid:
        logger.error("Manifest validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info(f"Manifest generated and validated successfully: {manifest_path}")
    return True

def main():
    """Main entry point for the audit pipeline."""
    parser = argparse.ArgumentParser(description="Run the A/B test audit pipeline")
    parser.add_argument("--input-dir", type=str, default="input", help="Input directory")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--input-urls", type=str, default=None, help="Path to input URLs CSV")
    parser.add_argument("--skip-monte-carlo", action="store_true", help="Skip Monte-Carlo validation")
    parser.add_argument("--skip-power-analysis", action="store_true", help="Skip power analysis")
    args = parser.parse_args()

    # Set random seed for reproducibility
    set_rng_seed(SEED)

    # Setup paths
    paths = setup_paths(args.input_dir, args.output_dir, args.data_dir)

    # Run Monte-Carlo validation (unless skipped)
    if not args.skip_monte_carlo:
        if not run_monte_carlo_startup_validation():
            logger.error(get_error_message("ERR-801"))
            return 1

    # Run full pipeline
    input_urls = Path(args.input_urls) if args.input_urls else None
    if not run_full_pipeline(paths, input_urls):
        logger.error("Pipeline execution failed.")
        return 1

    # Run power analysis (unless skipped)
    if not args.skip_power_analysis:
        if not run_power_analysis_step(paths):
            return 1

    # Run evaluation if synthetic data exists
    if not run_evaluation_step(paths):
        return 1

    # Run prevalence and reporting
    if not run_prevalence_and_reporting(paths):
        return 1

    # Generate and validate manifest
    if not generate_manifest_and_validate(paths):
        return 1

    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())