"""
Main entry point for the Plant Disease Resistance Prediction Pipeline.

Orchestrates the full workflow:
1. Data Integrity Check (T060, T049, T010)
2. Data Download/Generation (T010)
3. Preprocessing (T011)
4. Splitting (T015, T045)
5. Feature Selection (T016a, T016b, T026, T047)
6. Modeling (T017, T017b)
7. Validation (T018, T032, T033, T034)
8. Reporting (T022, T027, T053)
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Local imports matching API surface
from config import get_data_path, get_artifacts_path, get_reports_path
from utils.logging import get_logger, log_pipeline_step, log_error_context
from utils.exceptions import EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT
from data.manifest import load_manifest, create_default_manifest
from data.download import run_download_pipeline
from data.preprocess import process_pipeline
from data.split import run_split_pipeline
from analysis.feature_selection import run_feature_selection_pipeline
from analysis.modeling import run_modeling_pipeline
from analysis.validation import run_validation_pipeline
from analysis.success_criteria_check import check_success_criteria, write_success_report
from reports.generate_final_report import main as generate_final_report_main

# Initialize logger
logger = get_logger(__name__)

def check_data_integrity(manifest_path: Path) -> Dict[str, Any]:
    """
    T060: Final sanity check before analysis begins.
    Verifies:
    1. Manifest exists and is valid.
    2. Source is either 'SIMULATED' or 'REAL_DATA'.
    3. Sample count >= 100 (FR-007/FR-008).
    """
    log_pipeline_step(logger, "CHECK_DATA_INTEGRITY", "Starting final sanity check on data manifest")
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        raise FileNotFoundError(f"Data manifest not found at {manifest_path}")

    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        raise EX_DATA_INTEGRITY(code=101, message=f"Malformed manifest: {e}")

    # Check source type
    source_type = manifest.get("source", "UNKNOWN")
    if source_type not in ["SIMULATED", "REAL_DATA"]:
        logger.error(f"Invalid source type in manifest: {source_type}. Must be 'SIMULATED' or 'REAL_DATA'.")
        raise EX_DATA_INTEGRITY(code=102, message=f"Invalid source type: {source_type}")

    # Check sample count
    sample_count = manifest.get("sample_count", 0)
    if sample_count < 100:
        logger.error(f"Insufficient samples: {sample_count}. Required >= 100 for multivariate analysis.")
        raise EX_POWER_INSUFFICIENT(code=103, message=f"Power deficiency: n={sample_count} < 100 required")

    logger.info(f"Pipeline Ready: Source={source_type}, Samples={sample_count}")
    log_pipeline_step(logger, "CHECK_DATA_INTEGRITY", "PASSED", {
        "source": source_type,
        "sample_count": sample_count
    })

    return {
        "source": source_type,
        "sample_count": sample_count,
        "valid": True
    }

def run_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Orchestrates the full pipeline execution.
    """
    start_time = time.time()
    results = {}

    # 1. Setup Paths
    data_path = get_data_path()
    manifest_path = data_path / "data_manifest.yaml"
    processed_path = get_artifacts_path() / "processed"
    
    # Ensure directories exist
    processed_path.mkdir(parents=True, exist_ok=True)

    # 2. T060: Final Sanity Check
    # Note: T010 handles download/generation and updates manifest.
    # We verify the result here before proceeding to heavy analysis.
    manifest_info = check_data_integrity(manifest_path)
    results["manifest"] = manifest_info

    # 3. Preprocessing (T011)
    # If raw data exists, preprocess it. If synthetic was generated, it might be pre-formatted.
    # We assume preprocess_pipeline handles the alignment and normalization.
    log_pipeline_step(logger, "PREPROCESS", "Starting preprocessing pipeline")
    # Note: T011 creates exclusion_log.csv and aligned tables
    preprocess_results = process_pipeline(data_path, processed_path)
    results["preprocess"] = preprocess_results

    # 4. Splitting (T015, T045)
    log_pipeline_step(logger, "SPLIT", "Starting data splitting")
    split_results = run_split_pipeline(processed_path)
    results["split"] = split_results

    # 5. Feature Selection (T016a, T016b, T047)
    log_pipeline_step(logger, "FEATURE_SELECTION", "Starting feature selection")
    selection_results = run_feature_selection_pipeline(processed_path, get_reports_path())
    results["selection"] = selection_results

    # 6. Modeling (T017, T017b)
    log_pipeline_step(logger, "MODELING", "Starting model training")
    modeling_results = run_modeling_pipeline(processed_path, get_artifacts_path() / "models")
    results["modeling"] = modeling_results

    # 7. Validation (T018, T032, T033, T034)
    log_pipeline_step(logger, "VALIDATION", "Starting validation pipeline")
    validation_results = run_validation_pipeline(
        get_artifacts_path() / "models",
        processed_path,
        get_reports_path()
    )
    results["validation"] = validation_results

    # 8. Success Criteria Check (T041)
    log_pipeline_step(logger, "SUCCESS_CHECK", "Checking success criteria")
    success_results = check_success_criteria(get_reports_path())
    write_success_report(get_reports_path(), success_results)
    results["success"] = success_results

    # 9. Final Report Generation (T053)
    log_pipeline_step(logger, "FINAL_REPORT", "Generating final validation report")
    generate_final_report_main()

    end_time = time.time()
    total_runtime = end_time - start_time
    results["runtime_seconds"] = total_runtime

    logger.info(f"Pipeline completed successfully in {total_runtime:.2f} seconds")
    return results

def main():
    """
    CLI Entry Point.
    """
    parser = argparse.ArgumentParser(description="Plant Disease Resistance Prediction Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup without running full pipeline")
    
    args = parser.parse_args()

    # Initialize logging
    log_file = get_artifacts_path() / "pipeline.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = get_logger("pipeline_root")
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(ch)

    try:
        if args.dry_run:
            logger.info("Running in DRY-RUN mode. Checking configuration and paths only.")
            # Just check manifest and paths
            data_path = get_data_path()
            manifest_path = data_path / "data_manifest.yaml"
            if manifest_path.exists():
                logger.info(f"Manifest found at {manifest_path}")
                # Try to load and check integrity (T060)
                check_data_integrity(manifest_path)
            else:
                logger.warning(f"Manifest not found at {manifest_path}. Run full pipeline to generate data.")
            logger.info("Dry run complete.")
            return 0

        # Full pipeline execution
        results = run_pipeline(args)
        
        # Write summary to console
        logger.info("Pipeline Summary:")
        logger.info(f"  - Source: {results['manifest']['source']}")
        logger.info(f"  - Samples: {results['manifest']['sample_count']}")
        logger.info(f"  - Runtime: {results['runtime_seconds']:.2f}s")
        
        return 0

    except EX_DATA_INTEGRITY as e:
        logger.critical(f"DATA INTEGRITY ERROR: {e.message} (Code: {e.code})")
        return 1
    except EX_POWER_INSUFFICIENT as e:
        logger.critical(f"POWER ERROR: {e.message} (Code: {e.code})")
        return 2
    except Exception as e:
        log_error_context(logger, "UNEXPECTED_ERROR", str(e))
        logger.exception("Unexpected error occurred")
        return 3

if __name__ == "__main__":
    sys.exit(main())