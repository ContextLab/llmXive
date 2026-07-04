"""
Main driver script for the A/B test audit pipeline.
Orchestrates ingestion, fetching, extraction, reconstruction, validation,
and artifact generation including manifest creation.
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.config import set_rng_seed, get_config_summary
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.audit.power_analysis import run_power_analysis, write_power_analysis_result
from code.src.audit.synthetic import generate_synthetic_dataset
from code.src.audit.evaluation import evaluate_detection
from code.src.audit.prevalence import run_prevalence_analysis
from code.src.audit.bias_adjustment import run_bias_adjustment
from code.src.audit.subgroup_analysis import run_subgroup_analysis
from code.src.audit.report_generator import generate_summary_report, generate_subgroup_report
from code.src.utils.manifest import generate_manifest, validate_manifest
from code.src.audit.export_validator import run_export_validation
from code.src.audit.export_schema_validator import run_schema_validation
from code.src.audit.manifest_schema_validator import run_manifest_schema_validation
from code.src.audit.ingestor import ingest_and_deduplicate
from code.src.audit.fetcher import fetch_urls_batch
from code.src.audit.extractor import extract_all, write_summaries_to_json
from code.src.audit.reconstructor import reconstruct_all
from code.src.audit.validator import validate_all_summaries, write_audit_report

logger = get_default_logger(__name__)

def setup_paths(base_dir: Optional[Path] = None) -> dict:
    """Set up directory paths for the pipeline."""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent.parent
    
    paths = {
        "base": base_dir,
        "input": base_dir / "input",
        "output": base_dir / "output",
        "data": base_dir / "data",
        "data_raw": base_dir / "data" / "raw",
        "data_synthetic": base_dir / "data" / "synthetic",
        "contracts": base_dir / "contracts",
        "state": base_dir / "state" / "projects" / "PROJ-492-evaluating-the-statistical-validity-of-p.yaml"
    }
    
    # Ensure directories exist
    for path in paths.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
    
    return paths

def run_monte_carlo_startup_validation(paths: dict) -> bool:
    """Run Monte Carlo validation at startup."""
    logger.info("Running Monte Carlo startup validation...")
    try:
        result = run_monte_carlo_validation()
        if result:
            logger.info("Monte Carlo validation passed.")
            return True
        else:
            logger.error(get_error_message("ERR-801"))
            return False
    except Exception as e:
        logger.error(f"Monte Carlo validation failed: {e}")
        return False

def run_power_analysis_step(paths: dict) -> bool:
    """Run power analysis step."""
    logger.info("Running power analysis...")
    try:
        # Count corpus size from synthetic or manual validation data
        corpus_path = paths["data_synthetic"] / "synthetic_validation.csv"
        if not corpus_path.exists():
            logger.warning("Synthetic validation data not found, using placeholder count.")
            corpus_size = 300
        else:
            corpus_size = sum(1 for _ in open(corpus_path)) - 1  # Exclude header
        
        result = run_power_analysis(corpus_size, paths["output"])
        if result:
            logger.info("Power analysis completed successfully.")
            return True
        else:
            logger.error("Power analysis failed.")
            return False
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return False

def run_full_pipeline(paths: dict, urls_file: Optional[Path] = None) -> bool:
    """Run the full audit pipeline."""
    logger.info("Starting full audit pipeline...")
    
    try:
        # 1. Ingestion
        logger.info("Step 1: Ingestion and deduplication...")
        if urls_file is None:
            urls_file = paths["input"] / "urls.csv"
        
        if not urls_file.exists():
            logger.warning(f"URLs file not found: {urls_file}. Skipping ingestion.")
            return False
        
        ingest_and_deduplicate(urls_file, paths["output"])
        
        # 2. Fetching
        logger.info("Step 2: Fetching URLs...")
        fetch_urls_batch(paths["output"] / "urls_deduped.csv", paths["data_raw"])
        
        # 3. Extraction
        logger.info("Step 3: Extracting summaries...")
        extract_all(paths["data_raw"], paths["output"])
        write_summaries_to_json(paths["output"], paths["output"] / "extracted_summaries.json")
        
        # 4. Reconstruction
        logger.info("Step 4: Reconstructing statistical tests...")
        reconstruct_all(paths["output"] / "extracted_summaries.json", paths["output"])
        
        # 5. Validation
        logger.info("Step 5: Validating consistency...")
        validate_all_summaries(paths["output"] / "reconstructed_summaries.json", paths["output"])
        write_audit_report(paths["output"] / "audit_records.json", paths["output"] / "audit_report.json")
        
        return True
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False

def run_evaluation_step(paths: dict) -> bool:
    """Run evaluation on synthetic dataset."""
    logger.info("Running evaluation step...")
    try:
        synthetic_csv = paths["data_synthetic"] / "synthetic_validation.csv"
        ground_truth_json = paths["data_synthetic"] / "synthetic_ground_truth.json"
        
        if not synthetic_csv.exists() or not ground_truth_json.exists():
            logger.warning("Synthetic data not found. Skipping evaluation.")
            return True  # Not a failure if data doesn't exist yet
        
        result = evaluate_detection(synthetic_csv, ground_truth_json, paths["output"])
        if result:
            logger.info("Evaluation completed successfully.")
            return True
        else:
            logger.error("Evaluation failed to meet thresholds.")
            return False
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return False

def run_prevalence_and_reporting(paths: dict) -> bool:
    """Run prevalence analysis, bias adjustment, and report generation."""
    logger.info("Running prevalence and reporting steps...")
    try:
        # Prevalence analysis
        run_prevalence_analysis(paths["output"] / "audit_report.json", paths["output"])
        
        # Bias adjustment
        run_bias_adjustment(paths["output"] / "audit_report.json", paths["output"])
        
        # Subgroup analysis
        run_subgroup_analysis(paths["output"] / "audit_report.json", paths["output"])
        
        # Report generation
        generate_summary_report(paths["output"] / "audit_report.json", paths["output"] / "summary_report.csv")
        generate_subgroup_report(paths["output"] / "subgroup_report.json", paths["output"] / "subgroup_report.csv")
        
        logger.info("Prevalence and reporting completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Prevalence and reporting failed: {e}")
        return False

def generate_manifest_and_validate(paths: dict) -> bool:
    """Generate manifest.json and validate it."""
    logger.info("Generating and validating manifest...")
    try:
        output_dir = paths["output"]
        
        # Generate manifest
        manifest = generate_manifest(output_dir)
        
        # Validate manifest against schema
        manifest_path = output_dir / "manifest.json"
        is_valid, errors = run_manifest_schema_validation(manifest_path)
        
        if not is_valid:
            logger.error(f"Manifest schema validation failed: {errors}")
            return False
        
        # Validate file hashes
        is_valid_hashes, hash_errors = validate_manifest(manifest_path, output_dir)
        
        if not is_valid_hashes:
            logger.error(f"Manifest hash validation failed: {hash_errors}")
            return False
        
        # Run export consistency check (JSON vs CSV)
        export_valid, export_errors = run_export_validation(
            paths["output"] / "audit_report.json",
            paths["output"] / "summary_report.csv"
        )
        
        if not export_valid:
            logger.error(f"Export validation failed: {export_errors}")
            return False
        
        logger.info("Manifest generated and validated successfully.")
        return True
    except Exception as e:
        logger.error(f"Manifest generation/validation failed: {e}")
        return False

def main():
    """Main entry point for the audit pipeline."""
    parser = argparse.ArgumentParser(description="Run the A/B test audit pipeline")
    parser.add_argument(
        "--base-dir",
        type=str,
        default=None,
        help="Base directory for the project"
    )
    parser.add_argument(
        "--urls-file",
        type=str,
        default=None,
        help="Path to URLs CSV file"
    )
    parser.add_argument(
        "--skip-monte-carlo",
        action="store_true",
        help="Skip Monte Carlo validation"
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Skip evaluation step"
    )
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir) if args.base_dir else None
    urls_file = Path(args.urls_file) if args.urls_file else None
    
    # Set random seed for reproducibility
    set_rng_seed()
    
    paths = setup_paths(base_dir)
    
    # 1. Monte Carlo validation (unless skipped)
    if not args.skip_monte_carlo:
        if not run_monte_carlo_startup_validation(paths):
            logger.error("Startup validation failed. Exiting.")
            return 1
    
    # 2. Power analysis
    if not run_power_analysis_step(paths):
        logger.error("Power analysis failed. Exiting.")
        return 1
    
    # 3. Full pipeline
    if not run_full_pipeline(paths, urls_file):
        logger.error("Pipeline execution failed. Exiting.")
        return 1
    
    # 4. Evaluation (unless skipped)
    if not args.skip_evaluation:
        if not run_evaluation_step(paths):
            logger.error("Evaluation failed. Exiting.")
            return 1
    
    # 5. Prevalence and reporting
    if not run_prevalence_and_reporting(paths):
        logger.error("Prevalence and reporting failed. Exiting.")
        return 1
    
    # 6. Generate and validate manifest (T056)
    if not generate_manifest_and_validate(paths):
        logger.error("Manifest generation or validation failed. Exiting.")
        return 1
    
    logger.info("Audit pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())