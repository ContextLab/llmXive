import argparse
import json
import logging
import sys
import signal
from datetime import datetime
from pathlib import Path

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.utils.resource_monitor import start_monitoring, stop_monitoring, write_resource_log, get_memory_usage_gb, get_cpu_cores
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.audit.power_analysis import run_power_analysis, write_power_analysis_result
from code.src.audit.ingestor import ingest_and_deduplicate
from code.src.audit.fetcher import fetch_urls_batch
from code.src.audit.extractor import extract_all, write_summaries_to_json
from code.src.audit.reconstructor import reconstruct_all
from code.src.audit.validator import validate_all_summaries, write_audit_report
from code.src.audit.prevalence import run_prevalence_analysis, write_prevalence_results
from code.src.audit.report_generator import generate_summary_report, generate_subgroup_report
from code.src.audit.subgroup_analysis import run_subgroup_analysis, write_subgroup_report
from code.src.audit.export_validator import run_export_validation
from code.src.audit.export_schema_validator import run_schema_validation
from code.src.audit.manifest_schema_validator import run_manifest_schema_validation
from code.src.utils.manifest import generate_manifest, validate_manifest
from code.src.audit.evaluation import evaluate_detection, write_evaluation_results
from code.src.audit.provenance_archiver import archive_provenance
from code.src.audit.bias_adjustment import run_bias_adjustment, write_bias_adjustment_results
from code.src.audit.domain_subsample import run_domain_subsample
from code.src.audit.synthetic import generate_synthetic_dataset, write_csv_output, write_json_output
from code.src.audit.test_type_detector import detect_outcome_type_from_ab_summary

def setup_paths(args):
    """Initialize logging and paths based on arguments."""
    log_path = Path(args.log_dir) / "audit.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = get_default_logger("audit_pipeline", log_path)
    logger.info("Pipeline started at %s", datetime.now().isoformat())
    
    return logger

def run_monte_carlo_startup_validation(logger):
    """Run Monte Carlo validation at startup to ensure statistical functions are valid."""
    logger.info("Running Monte Carlo startup validation...")
    try:
        run_monte_carlo_validation()
        logger.info("Monte Carlo validation passed.")
    except Exception as e:
        logger.error("Monte Carlo validation failed: %s", str(e))
        raise SystemExit(1)

def run_power_analysis_step(logger):
    """Run power analysis to determine minimum corpus size."""
    logger.info("Running power analysis...")
    try:
        run_power_analysis()
        write_power_analysis_result()
        logger.info("Power analysis completed.")
    except Exception as e:
        logger.error("Power analysis failed: %s", str(e))
        raise SystemExit(1)

def run_full_pipeline(logger, args):
    """Execute the full audit pipeline: ingest, fetch, extract, reconstruct, validate."""
    logger.info("Starting full pipeline...")
    
    # Ingest
    logger.info("Ingesting URLs...")
    ingest_and_deduplicate(args.input_urls, args.output_dir)
    
    # Fetch
    logger.info("Fetching HTML...")
    fetch_urls_batch(args.output_dir, args.output_dir)
    
    # Extract
    logger.info("Extracting summaries...")
    summaries = extract_all(args.output_dir, args.output_dir)
    write_summaries_to_json(summaries, args.output_dir)
    
    # Reconstruct
    logger.info("Reconstructing statistics...")
    reconstruct_all(args.output_dir)
    
    # Validate
    logger.info("Validating summaries...")
    audit_records = validate_all_summaries(args.output_dir)
    write_audit_report(audit_records, args.output_dir)
    
    # Provenance
    logger.info("Archiving provenance...")
    archive_provenance(args.output_dir)
    
    logger.info("Full pipeline completed.")

def run_prevalence_and_reporting(logger, args):
    """Run prevalence analysis, bias adjustment, and report generation."""
    logger.info("Running prevalence and reporting...")
    
    # Prevalence
    run_prevalence_analysis(args.output_dir)
    write_prevalence_results(args.output_dir)
    
    # Bias Adjustment
    logger.info("Running bias adjustment...")
    run_domain_subsample(args.output_dir)
    run_bias_adjustment(args.output_dir)
    write_bias_adjustment_results(args.output_dir)
    
    # Reports
    logger.info("Generating summary report...")
    generate_summary_report(args.output_dir)
    generate_subgroup_report(args.output_dir)
    
    # Subgroup Analysis
    logger.info("Running subgroup analysis...")
    run_subgroup_analysis(args.output_dir)
    write_subgroup_report(args.output_dir)
    
    logger.info("Prevalence and reporting completed.")

def check_resource_limits(logger):
    """Check if resource limits have been exceeded and abort with ERR-301 if so."""
    logger.info("Checking resource limits...")
    
    try:
        # Stop monitoring if running
        stop_monitoring()
        
        # Read resource log if it exists
        resource_log_path = Path("output/resource_log.json")
        if resource_log_path.exists():
            with open(resource_log_path, 'r') as f:
                resource_data = json.load(f)
            
            peak_memory_gb = resource_data.get('peak_memory_gb', 0)
            peak_cpu_cores = resource_data.get('peak_cpu_cores', 0)
            
            # FR-009 limits: RAM <= 2GB, CPU <= 2 vCPU
            if peak_memory_gb > 2.0:
                error_msg = get_error_message("ERR-301")
                logger.error("ERR-301: Resource limit exceeded. Peak memory usage: %.2f GB (limit: 2.0 GB)", peak_memory_gb)
                raise SystemExit(1)
            
            if peak_cpu_cores > 2.0:
                error_msg = get_error_message("ERR-301")
                logger.error("ERR-301: Resource limit exceeded. Peak CPU cores: %.2f (limit: 2.0)", peak_cpu_cores)
                raise SystemExit(1)
            
            logger.info("Resource limits check passed. Peak memory: %.2f GB, Peak CPU: %.2f cores", peak_memory_gb, peak_cpu_cores)
        else:
            logger.warning("Resource log not found. Skipping resource limit check.")
    except Exception as e:
        logger.error("Error checking resource limits: %s", str(e))
        raise

def generate_manifest_and_validate(logger, args):
    """Generate manifest with checksums and validate schemas."""
    logger.info("Generating manifest and validating schemas...")
    
    # Generate manifest
    generate_manifest(args.output_dir)
    
    # Validate manifest schema
    run_manifest_schema_validation(args.output_dir)
    
    # Validate audit report schema
    run_schema_validation(args.output_dir)
    
    # Validate export consistency
    run_export_validation(args.output_dir)
    
    logger.info("Manifest generation and validation completed.")

def main():
    parser = argparse.ArgumentParser(description="Run the A/B test audit pipeline.")
    parser.add_argument("--input-urls", type=str, default="input/urls.csv", help="Path to input URLs CSV")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--log-dir", type=str, default="output/logs", help="Log directory")
    parser.add_argument("--skip-monte-carlo", action="store_true", help="Skip Monte Carlo validation")
    parser.add_argument("--skip-power-analysis", action="store_true", help="Skip power analysis")
    parser.add_argument("--skip-prevalence", action="store_true", help="Skip prevalence and reporting")
    parser.add_argument("--skip-manifest", action="store_true", help="Skip manifest generation")
    
    args = parser.parse_args()
    
    logger = setup_paths(args)
    
    try:
        # Start resource monitoring
        start_monitoring()
        
        # Monte Carlo validation
        if not args.skip_monte_carlo:
            run_monte_carlo_startup_validation(logger)
        
        # Power analysis
        if not args.skip_power_analysis:
            run_power_analysis_step(logger)
        
        # Full pipeline
        run_full_pipeline(logger, args)
        
        # Prevalence and reporting
        if not args.skip_prevalence:
            run_prevalence_and_reporting(logger, args)
        
        # Manifest and validation
        if not args.skip_manifest:
            generate_manifest_and_validate(logger, args)
        
        # Check resource limits
        check_resource_limits(logger)
        
        logger.info("Pipeline completed successfully.")
        
    except SystemExit as e:
        # Re-raise SystemExit to allow proper exit codes
        raise
    except Exception as e:
        logger.error("Pipeline failed with error: %s", str(e))
        raise

if __name__ == "__main__":
    main()