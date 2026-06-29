"""
End-to-end driver script for the A/B test audit pipeline.

Orchestrates: ingestion → fetch → extract → reconstruct → validate → write artifacts

This script implements task T032 and depends on:
- T025: Validator module
- T028: Power analysis module
- T029: Evaluation module
- T031: Monte Carlo validation at startup
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing modules per API surface
from code.src.config import set_rng_seed, get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message
from code.src.audit.ingestor import ingest_and_deduplicate, read_urls_from_csv
from code.src.audit.fetcher import ingest_and_fetch
from code.src.audit.extractor import extract_all, write_summaries_to_json
from code.src.audit.test_type_detector import detect_outcome_type_from_ab_summary
from code.src.audit.reconstructor import reconstruct_all, write_reconstructed_results
from code.src.audit.validator import validate_all_summaries, write_audit_report, filter_for_prevalence
from code.src.audit.power_analysis import run_power_analysis, write_power_analysis_result
from code.src.audit.monte_carlo_validation import run_monte_carlo_validation
from code.src.audit.evaluation import load_synthetic_summaries, load_ground_truth, evaluate_detection, write_evaluation_results
from code.src.audit.prevalence import compute_prevalence, write_prevalence_results
from code.src.audit.bias_adjustment import compute_bias_adjusted_prevalence, write_bias_adjustment_results
from code.src.audit.report_generator import generate_summary_report
from code.src.audit.subgroup_analysis import run_subgroup_analysis, write_subgroup_report
from code.src.utils.manifest import generate_manifest, write_manifest
from code.src.utils.resource_monitor import start_monitoring, stop_monitoring, write_resource_log
from code.src.contracts.validation import validate_audit_record
from code.src.models.data_models import ABTestSummary, AuditRecord


def setup_paths() -> Dict[str, Path]:
    """Set up all required paths for the pipeline."""
    root = Path(__file__).parent.parent.parent.parent
    paths = {
        'root': root,
        'input': root / 'input',
        'data': root / 'data',
        'data_raw': root / 'data' / 'raw',
        'data_synthetic': root / 'data' / 'synthetic',
        'output': root / 'output',
        'logs': root / 'logs',
    }

    # Ensure all directories exist
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    return paths


def run_monte_carlo_startup_validation(logger: AuditLogger) -> bool:
    """
    Run Monte Carlo validation at startup as per T031.
    Returns True if validation passes, False otherwise.
    """
    logger.info("Running Monte Carlo validation at startup...")
    try:
        success, results = run_monte_carlo_validation()
        if not success:
            logger.error("ERR-801: Monte Carlo validation failed")
            return False
        logger.info("Monte Carlo validation passed")
        return True
    except Exception as e:
        logger.error(f"ERR-801: Monte Carlo validation failed with exception: {e}")
        return False


def run_power_analysis_step(paths: Dict[str, Path], logger: AuditLogger) -> bool:
    """Run power analysis as per T028."""
    logger.info("Running power analysis...")
    try:
        success, result = run_power_analysis(paths)
        if success:
            write_power_analysis_result(paths['output'], result)
            logger.info("Power analysis completed successfully")
            return True
        else:
            logger.error("ERR-280: Power analysis failed")
            return False
    except Exception as e:
        logger.error(f"ERR-280: Power analysis failed with exception: {e}")
        return False


def run_full_pipeline(paths: Dict[str, Path], logger: AuditLogger, config: Dict[str, Any]) -> bool:
    """
    Run the full audit pipeline: ingestion → fetch → extract → reconstruct → validate.
    """
    # Step 1: Ingestion
    logger.info("Starting URL ingestion...")
    try:
        urls_csv = paths['input'] / 'urls.csv'
        if not urls_csv.exists():
            logger.error("ERR-180: Input URLs file not found")
            return False

        success, deduped_urls = ingest_and_deduplicate(urls_csv, paths['data'])
        if not success:
            logger.error("ERR-181: Ingestion failed")
            return False
        logger.info(f"Ingested {len(deduped_urls)} unique URLs")
    except Exception as e:
        logger.error(f"ERR-181: Ingestion failed with exception: {e}")
        return False

    # Step 2: Fetch
    logger.info("Starting HTML fetch...")
    try:
        success, fetched_urls = ingest_and_fetch(deduped_urls, paths['data_raw'], config)
        if not success:
            logger.error("ERR-190: Fetch failed")
            return False
        logger.info(f"Fetched {len(fetched_urls)} HTML files")
    except Exception as e:
        logger.error(f"ERR-190: Fetch failed with exception: {e}")
        return False

    # Step 3: Extract
    logger.info("Starting extraction...")
    try:
        success, summaries = extract_all(fetched_urls, paths['data'])
        if not success:
            logger.error("ERR-200: Extraction failed")
            return False
        write_summaries_to_json(summaries, paths['data'] / 'extracted_summaries.json')
        logger.info(f"Extracted {len(summaries)} summaries")
    except Exception as e:
        logger.error(f"ERR-200: Extraction failed with exception: {e}")
        return False

    # Step 4: Reconstruct
    logger.info("Starting statistical reconstruction...")
    try:
        success, reconstructed = reconstruct_all(summaries, paths['data'])
        if not success:
            logger.error("ERR-230: Reconstruction failed")
            return False
        write_reconstructed_results(reconstructed, paths['data'] / 'reconstructed_results.json')
        logger.info(f"Reconstructed {len(reconstructed)} statistical tests")
    except Exception as e:
        logger.error(f"ERR-230: Reconstruction failed with exception: {e}")
        return False

    # Step 5: Validate
    logger.info("Starting validation...")
    try:
        success, audit_records = validate_all_summaries(reconstructed, paths['data'])
        if not success:
            logger.error("ERR-250: Validation failed")
            return False
        write_audit_report(audit_records, paths['output'] / 'audit_report.json')
        logger.info(f"Validated {len(audit_records)} records")
    except Exception as e:
        logger.error(f"ERR-250: Validation failed with exception: {e}")
        return False

    return True


def run_evaluation_step(paths: Dict[str, Path], logger: AuditLogger) -> bool:
    """Run evaluation on synthetic dataset as per T029."""
    logger.info("Running evaluation on synthetic dataset...")
    try:
        synthetic_csv = paths['data_synthetic'] / 'synthetic_validation.csv'
        ground_truth_json = paths['data_synthetic'] / 'synthetic_ground_truth.json'

        if synthetic_csv.exists() and ground_truth_json.exists():
            summaries = load_synthetic_summaries(synthetic_csv)
            ground_truth = load_ground_truth(ground_truth_json)
            success, metrics = evaluate_detection(summaries, ground_truth)
            if success:
                write_evaluation_results(metrics, paths['output'] / 'evaluation_results.json')
                logger.info(f"Evaluation completed: precision={metrics['precision']:.3f}, recall={metrics['recall']:.3f}")
                return True
            else:
                logger.error("ERR-800: Evaluation thresholds not met")
                return False
        else:
            logger.warning("Synthetic validation dataset not found, skipping evaluation")
            return True
    except Exception as e:
        logger.error(f"ERR-800: Evaluation failed with exception: {e}")
        return False


def run_prevalence_and_reporting(paths: Dict[str, Path], logger: AuditLogger) -> bool:
    """Run prevalence computation, bias adjustment, and report generation."""
    # Compute prevalence
    logger.info("Computing prevalence...")
    try:
        audit_report_path = paths['output'] / 'audit_report.json'
        if not audit_report_path.exists():
            logger.error("ERR-420: Audit report not found for prevalence computation")
            return False

        success, prevalence_result = compute_prevalence(audit_report_path, paths['data'])
        if success:
            write_prevalence_results(paths['output'] / 'prevalence.json', prevalence_result)
        else:
            logger.error("ERR-420: Prevalence computation failed")
            return False
    except Exception as e:
        logger.error(f"ERR-420: Prevalence computation failed with exception: {e}")
        return False

    # Bias adjustment
    logger.info("Computing bias-adjusted prevalence...")
    try:
        success, bias_result = compute_bias_adjusted_prevalence(paths['output'] / 'prevalence.json', paths['data'])
        if success:
            write_bias_adjustment_results(paths['output'] / 'bias_adjustment.json', bias_result)
        else:
            logger.error("ERR-450: Bias adjustment failed")
            return False
    except Exception as e:
        logger.error(f"ERR-450: Bias adjustment failed with exception: {e}")
        return False

    # Generate summary report
    logger.info("Generating summary report...")
    try:
        success = generate_summary_report(
            paths['output'] / 'audit_report.json',
            paths['output'] / 'prevalence.json',
            paths['output'] / 'bias_adjustment.json',
            paths['output'] / 'summary_report.csv'
        )
        if not success:
            logger.error("ERR-470: Summary report generation failed")
            return False
    except Exception as e:
        logger.error(f"ERR-470: Summary report generation failed with exception: {e}")
        return False

    # Subgroup analysis
    logger.info("Running subgroup analysis...")
    try:
        success, subgroup_result = run_subgroup_analysis(paths['output'] / 'audit_report.json', paths['data'])
        if success:
            write_subgroup_report(paths['output'] / 'subgroup_report.json', subgroup_result)
            write_subgroup_report(paths['output'] / 'subgroup_report.csv', subgroup_result, as_csv=True)
        else:
            logger.error("ERR-500: Subgroup analysis failed")
            return False
    except Exception as e:
        logger.error(f"ERR-500: Subgroup analysis failed with exception: {e}")
        return False

    return True


def generate_manifest_and_validate(paths: Dict[str, Path], logger: AuditLogger) -> bool:
    """Generate manifest and validate all output artifacts."""
    logger.info("Generating manifest...")
    try:
        output_files = [
            'audit_report.json',
            'summary_report.csv',
            'prevalence.json',
            'bias_adjustment.json',
            'subgroup_report.json',
            'subgroup_report.csv',
            'power_analysis.json',
            'evaluation_results.json',
            'resource_log.json',
        ]

        manifest = generate_manifest(paths['output'], output_files)
        write_manifest(paths['output'] / 'manifest.json', manifest)
        logger.info("Manifest generated successfully")
    except Exception as e:
        logger.error(f"ERR-560: Manifest generation failed with exception: {e}")
        return False

    # Validate audit report schema
    logger.info("Validating audit report schema...")
    try:
        audit_report_path = paths['output'] / 'audit_report.json'
        if audit_report_path.exists():
            with open(audit_report_path, 'r') as f:
                audit_data = json.load(f)
            for record in audit_data.get('records', []):
                is_valid, errors = validate_audit_record(record)
                if not is_valid:
                    logger.error(f"ERR-570: Audit record validation failed: {errors}")
                    return False
        logger.info("Audit report schema validation passed")
    except Exception as e:
        logger.error(f"ERR-570: Audit report validation failed with exception: {e}")
        return False

    return True


def main():
    """Main entry point for the audit pipeline driver."""
    parser = argparse.ArgumentParser(
        description='End-to-end A/B test audit pipeline driver',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--input-urls',
        type=str,
        default='input/urls.csv',
        help='Path to input URLs CSV file'
    )
    parser.add_argument(
        '--skip-monte-carlo',
        action='store_true',
        help='Skip Monte Carlo validation at startup'
    )
    parser.add_argument(
        '--skip-evaluation',
        action='store_true',
        help='Skip synthetic dataset evaluation'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup paths
    paths = setup_paths()

    # Setup logging
    logger = get_default_logger(paths['logs'] / 'audit_pipeline.log')
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Starting A/B Test Audit Pipeline")
    logger.info(f"Config: {get_config_summary()}")
    logger.info("=" * 60)

    # Set RNG seed for reproducibility
    set_rng_seed(42)

    # Step 1: Monte Carlo validation (T031)
    if not args.skip_monte_carlo:
        if not run_monte_carlo_startup_validation(logger):
            logger.error("Pipeline aborted due to Monte Carlo validation failure")
            sys.exit(1)

    # Step 2: Resource monitoring
    monitor = start_monitoring(paths['output'] / 'resource_log.json')

    # Step 3: Power analysis (T028)
    config = {
        'random_seed': 42,
        'alpha': 0.05,
        'power': 0.80,
        'baseline_conversion': 0.10,
        'detectable_effect': 0.05,
    }
    if not run_power_analysis_step(paths, logger):
        logger.error("Pipeline aborted due to power analysis failure")
        sys.exit(1)

    # Step 4: Full pipeline
    if not run_full_pipeline(paths, logger, config):
        logger.error("Pipeline aborted due to pipeline failure")
        sys.exit(1)

    # Step 5: Evaluation (T029)
    if not args.skip_evaluation:
        if not run_evaluation_step(paths, logger):
            logger.error("Pipeline aborted due to evaluation failure")
            sys.exit(1)

    # Step 6: Prevalence and reporting
    if not run_prevalence_and_reporting(paths, logger):
        logger.error("Pipeline aborted due to reporting failure")
        sys.exit(1)

    # Step 7: Manifest and validation (T056-T059)
    if not generate_manifest_and_validate(paths, logger):
        logger.error("Pipeline aborted due to manifest/validation failure")
        sys.exit(1)

    # Stop resource monitoring
    stop_monitoring(monitor)

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully")
    logger.info(f"Output artifacts written to: {paths['output']}")
    logger.info("=" * 60)

    sys.exit(0)


if __name__ == '__main__':
    main()
