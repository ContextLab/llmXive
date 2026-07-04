import argparse
import json
import logging
import sys
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.utils.resource_monitor import start_monitoring, stop_monitoring, write_resource_log, ResourceMonitor
from code.src.utils.manifest import generate_manifest, find_files_to_hash
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.audit.power_analysis import run_power_analysis
from code.src.audit.synthetic import generate_synthetic_dataset, write_csv_output, write_json_output
from code.src.audit.evaluation import load_synthetic_summaries, load_ground_truth, evaluate_detection
from code.src.audit.prevalence import run_prevalence_analysis
from code.src.audit.bias_adjustment import run_bias_adjustment
from code.src.audit.subgroup_analysis import run_subgroup_analysis
from code.src.audit.report_generator import generate_summary_report, generate_subgroup_report
from code.src.audit.export_validator import run_export_validation
from code.src.audit.export_schema_validator import run_schema_validation
from code.src.audit.manifest_schema_validator import run_manifest_schema_validation
from code.src.audit.ingestor import ingest_and_deduplicate
from code.src.audit.fetcher import ingest_and_fetch
from code.src.audit.extractor import extract_all, write_summaries_to_json
from code.src.audit.reconstructor import reconstruct_all
from code.src.audit.validator import validate_all_summaries, write_audit_report
from code.src.config import set_rng_seed, get_config_summary

def setup_paths(input_urls: str, output_dir: str) -> tuple[Path, Path, Path]:
    """Setup directories and return paths for input, output, and raw data."""
    input_path = Path(input_urls)
    output_path = Path(output_dir)
    raw_path = output_path.parent / "data" / "raw"
    
    output_path.mkdir(parents=True, exist_ok=True)
    raw_path.mkdir(parents=True, exist_ok=True)
    
    return input_path, output_path, raw_path

def run_monte_carlo_startup_validation(logger: AuditLogger) -> bool:
    """Run Monte Carlo validation as a startup check."""
    try:
        run_monte_carlo_validation()
        logger.info("Monte Carlo validation passed")
        return True
    except Exception as e:
        logger.error(f"ERR-801: Monte Carlo validation failed: {str(e)}")
        return False

def run_power_analysis_step(output_dir: Path, logger: AuditLogger) -> bool:
    """Run power analysis step."""
    try:
        run_power_analysis(output_dir)
        logger.info("Power analysis completed")
        return True
    except Exception as e:
        logger.error(f"ERR-802: Power analysis failed: {str(e)}")
        return False

def run_full_pipeline(input_urls: Path, output_dir: Path, raw_dir: Path, logger: AuditLogger) -> bool:
    """Run the full audit pipeline."""
    try:
        # Ingest and deduplicate URLs
        logger.info("Starting URL ingestion and deduplication")
        ingest_and_deduplicate(str(input_urls), str(output_dir / "urls_deduped.csv"))
        
        # Fetch HTML
        logger.info("Fetching HTML content")
        ingest_and_fetch(str(output_dir / "urls_deduped.csv"), str(raw_dir))
        
        # Extract summaries
        logger.info("Extracting A/B test summaries")
        summaries = extract_all(str(raw_dir))
        write_summaries_to_json(summaries, str(output_dir / "extracted_summaries.json"))
        
        # Reconstruct statistical tests
        logger.info("Reconstructing statistical tests")
        reconstructed = reconstruct_all(summaries)
        
        # Validate consistency
        logger.info("Validating statistical consistency")
        audit_records = validate_all_summaries(reconstructed)
        write_audit_report(audit_records, str(output_dir / "audit_report.json"))
        
        logger.info("Full pipeline completed successfully")
        return True
    except Exception as e:
        logger.error(f"ERR-900: Pipeline execution failed: {str(e)}")
        return False

def run_evaluation_step(output_dir: Path, logger: AuditLogger) -> bool:
    """Run evaluation on synthetic dataset."""
    try:
        synthetic_csv = output_dir.parent / "data" / "synthetic" / "synthetic_validation.csv"
        ground_truth = output_dir.parent / "data" / "synthetic" / "synthetic_ground_truth.json"
        
        if not synthetic_csv.exists() or not ground_truth.exists():
            logger.warning("Synthetic validation data not found, skipping evaluation")
            return True
        
        synthetic_summaries = load_synthetic_summaries(str(synthetic_csv))
        ground_truth_data = load_ground_truth(str(ground_truth))
        
        precision, recall, f1 = evaluate_detection(synthetic_summaries, ground_truth_data)
        
        logger.info(f"Evaluation results: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
        
        if precision < 0.90 or recall < 0.80:
            logger.error(f"ERR-800: Evaluation thresholds not met (Precision={precision:.3f}, Recall={recall:.3f})")
            return False
        
        return True
    except Exception as e:
        logger.error(f"ERR-803: Evaluation failed: {str(e)}")
        return False

def run_prevalence_and_reporting(output_dir: Path, logger: AuditLogger) -> bool:
    """Run prevalence analysis and generate reports."""
    try:
        # Run prevalence analysis
        run_prevalence_analysis(str(output_dir / "audit_report.json"), str(output_dir))
        
        # Run bias adjustment
        run_bias_adjustment(str(output_dir / "audit_report.json"), str(output_dir))
        
        # Run subgroup analysis
        run_subgroup_analysis(str(output_dir / "audit_report.json"), str(output_dir))
        
        # Generate reports
        generate_summary_report(str(output_dir / "audit_report.json"), str(output_dir / "summary_report.csv"))
        generate_subgroup_report(str(output_dir / "subgroup_analysis.json"), str(output_dir / "subgroup_report.csv"))
        
        logger.info("Prevalence and reporting completed")
        return True
    except Exception as e:
        logger.error(f"ERR-901: Prevalence and reporting failed: {str(e)}")
        return False

def generate_manifest_and_validate(output_dir: Path, logger: AuditLogger) -> bool:
    """Generate manifest and validate schemas."""
    try:
        # Generate manifest with SHA256 hashes
        files_to_hash = find_files_to_hash(output_dir)
        manifest = generate_manifest(files_to_hash, str(output_dir / "manifest.json"))
        
        # Validate audit report schema
        run_schema_validation(str(output_dir / "audit_report.json"))
        
        # Validate manifest schema
        run_manifest_schema_validation(str(output_dir / "manifest.json"))
        
        # Validate export consistency
        run_export_validation(str(output_dir / "audit_report.json"), str(output_dir / "summary_report.csv"))
        
        logger.info("Manifest generation and validation completed")
        return True
    except Exception as e:
        logger.error(f"ERR-902: Manifest generation and validation failed: {str(e)}")
        return False

def check_resource_limits(logger: AuditLogger) -> bool:
    """Check if resource limits have been exceeded and abort if so."""
    try:
        # Stop monitoring and write resource log
        stop_monitoring()
        write_resource_log()
        
        # Read the resource log to check limits
        resource_log_path = Path("output/resource_log.json")
        if not resource_log_path.exists():
            logger.warning("Resource log not found, assuming limits not exceeded")
            return True
        
        with open(resource_log_path, 'r') as f:
            resource_data = json.load(f)
        
        peak_memory_gb = resource_data.get('peak_memory_gb', 0)
        peak_cpu_percent = resource_data.get('peak_cpu_percent', 0)
        
        # Check against limits (2 GB RAM, 2 vCPU)
        if peak_memory_gb > 2.0:
            error_msg = get_error_message("ERR-301")
            logger.error(f"ERR-301: Memory limit exceeded. Peak memory: {peak_memory_gb:.2f} GB (limit: 2.0 GB)")
            return False
        
        if peak_cpu_percent > 200:  # 200% = 2 vCPUs
            error_msg = get_error_message("ERR-301")
            logger.error(f"ERR-301: CPU limit exceeded. Peak CPU: {peak_cpu_percent:.1f}% (limit: 200%)")
            return False
        
        logger.info(f"Resource check passed: Memory={peak_memory_gb:.2f}GB, CPU={peak_cpu_percent:.1f}%")
        return True
    except Exception as e:
        logger.error(f"ERR-903: Resource limit check failed: {str(e)}")
        return False

def main():
    """Main entry point for the audit pipeline with resource monitoring."""
    parser = argparse.ArgumentParser(description="Run A/B test validity audit pipeline")
    parser.add_argument("--input-urls", type=str, default="input/urls.csv", help="Path to input URLs CSV")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--skip-monte-carlo", action="store_true", help="Skip Monte Carlo validation")
    parser.add_argument("--skip-evaluation", action="store_true", help="Skip evaluation step")
    args = parser.parse_args()

    # Setup logging
    logger = get_default_logger()
    logger.info(f"Audit pipeline started at {datetime.now().isoformat()}")
    logger.info(f"Configuration: {get_config_summary()}")

    # Setup paths
    input_path, output_path, raw_path = setup_paths(args.input_urls, args.output_dir)

    # Start resource monitoring
    start_monitoring()

    try:
        # Step 1: Monte Carlo validation (optional)
        if not args.skip_monte_carlo:
            if not run_monte_carlo_startup_validation(logger):
                logger.error("Aborting due to Monte Carlo validation failure")
                sys.exit(1)

        # Step 2: Run full pipeline
        if not run_full_pipeline(input_path, output_path, raw_path, logger):
            logger.error("Aborting due to pipeline failure")
            sys.exit(1)

        # Step 3: Evaluation (optional)
        if not args.skip_evaluation:
            if not run_evaluation_step(output_path, logger):
                logger.error("Aborting due to evaluation failure")
                sys.exit(1)

        # Step 4: Power analysis
        if not run_power_analysis_step(output_path, logger):
            logger.error("Aborting due to power analysis failure")
            sys.exit(1)

        # Step 5: Prevalence and reporting
        if not run_prevalence_and_reporting(output_path, logger):
            logger.error("Aborting due to prevalence/reporting failure")
            sys.exit(1)

        # Step 6: Generate manifest and validate
        if not generate_manifest_and_validate(output_path, logger):
            logger.error("Aborting due to manifest/validation failure")
            sys.exit(1)

        # Step 7: Check resource limits (T063 requirement)
        if not check_resource_limits(logger):
            # Resource limits exceeded - abort with ERR-301
            logger.error("Aborting due to resource limit violation (ERR-301)")
            sys.exit(1)

        logger.info("Audit pipeline completed successfully")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.error("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        # Ensure monitoring is stopped even on error
        try:
            stop_monitoring()
            write_resource_log()
        except:
            pass

if __name__ == "__main__":
    main()