"""
Main CLI entry point for the plant disease resistance prediction pipeline.
Orchestrates: Fetch -> Preprocess -> Split -> Select -> Train -> Validate.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Local imports from project structure
from config import get_data_path, get_artifacts_path, get_reports_path
from data.manifest import load_manifest, get_source_type
from utils.exceptions import EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT, PipelineError
from utils.logging import get_logger, log_pipeline_step, log_error_context
from data.download import run_download_pipeline
from data.preprocess import process_pipeline
from data.split import run_split_pipeline
from analysis.feature_selection import run_feature_selection_pipeline
from analysis.modeling import run_modeling_pipeline
from analysis.validation import run_validation_pipeline
from analysis.permutation_test import permutation_test_pipeline
from analysis.holdout_report import generate_holdout_report_pipeline
from analysis.success_criteria_check import check_success_criteria, write_success_report
from analysis.biomarker_report import generate_biomarker_report

# Initialize logger
logger = get_logger(__name__)

def check_data_integrity(manifest_path: str) -> Dict[str, Any]:
    """
    Check data integrity and power requirements based on source type.
    
    Args:
        manifest_path: Path to data_manifest.yaml
        
    Returns:
        Dictionary with validation results and counts
        
    Raises:
        EX_DATA_INTEGRITY: If data integrity checks fail for real data
        EX_POWER_INSUFFICIENT: If sample size is insufficient for real data
    """
    logger.info("Starting data integrity check...")
    
    # Load manifest
    manifest = load_manifest(manifest_path)
    source_type = get_source_type(manifest)
    
    # Get counts from manifest
    total_samples = 0
    missing_modalities = 0
    
    if 'datasets' in manifest:
        for dataset in manifest['datasets']:
          if 'samples' in dataset:
              total_samples += dataset['samples']
          if 'missing_modalities' in dataset:
              missing_modalities += dataset['missing_modalities']
    
    # Check source type
    is_simulated = (source_type == "SIMULATED")
    
    logger.info(f"Source type: {source_type}, Total samples: {total_samples}, Missing modalities: {missing_modalities}")
    
    # Bypass checks for simulated data
    if is_simulated:
        logger.info("Simulation Mode detected - bypassing data integrity and power checks")
        return {
            "source_type": source_type,
            "total_samples": total_samples,
            "missing_modalities": missing_modalities,
            "passed": True,
            "reason": "Simulation Mode"
        }
    
    # Real data checks
    # Priority 1: Power (FR-008) - Check sample size first
    if total_samples < 100:
        error_msg = f"Insufficient power: {total_samples} samples found. Minimum required: 100 (FR-008)"
        logger.error(error_msg)
        raise EX_POWER_INSUFFICIENT(error_msg)
    
    # Priority 2: Integrity (FR-007) - Check missing modalities
    if missing_modalities > 0:
        error_msg = f"Data integrity issue: {missing_modalities} samples missing modalities (FR-007)"
        logger.error(error_msg)
        raise EX_DATA_INTEGRITY(error_msg)
    
    logger.info("Data integrity and power checks passed")
    return {
        "source_type": source_type,
        "total_samples": total_samples,
        "missing_modalities": missing_modalities,
        "passed": True,
        "reason": "All checks passed"
    }

def run_pipeline(args: argparse.Namespace) -> None:
    """
    Execute the full prediction pipeline.
    
    Args:
        args: Command line arguments
    """
    logger.info("Starting plant disease resistance prediction pipeline")
    
    try:
        # 1. Check data integrity
        manifest_path = args.manifest or str(get_data_path() / "data_manifest.yaml")
        integrity_result = check_data_integrity(manifest_path)
        logger.info(f"Integrity check result: {integrity_result['reason']}")
        
        # 2. Fetch/Generate data
        logger.info("Step 1/7: Fetching or generating data...")
        download_result = run_download_pipeline(args)
        
        # 3. Preprocess data
        logger.info("Step 2/7: Preprocessing data...")
        preprocess_result = process_pipeline(args)
        
        # 4. Split data
        logger.info("Step 3/7: Splitting data...")
        split_result = run_split_pipeline(args)
        
        # 5. Feature selection
        logger.info("Step 4/7: Performing feature selection...")
        selection_result = run_feature_selection_pipeline(args)
        
        # 6. Model training and validation
        logger.info("Step 5/7: Training and validating models...")
        modeling_result = run_modeling_pipeline(args)
        
        # 7. Permutation testing on hold-out set
        logger.info("Step 6/7: Running permutation testing on hold-out set...")
        permutation_result = permutation_test_pipeline(args)
        
        # 8. Generate reports
        logger.info("Step 7/7: Generating reports...")
        
        # Generate hold-out report with permutation p-value
        generate_holdout_report_pipeline(args)
        
        # Generate biomarker report
        generate_biomarker_report(args)
        
        # Check success criteria
        check_success_criteria(args)
        write_success_report(args)
        
        logger.info("Pipeline completed successfully")
        
    except EX_DATA_INTEGRITY as e:
        logger.error(f"Data integrity check failed: {str(e)}")
        log_error_context(e)
        raise
    except EX_POWER_INSUFFICIENT as e:
        logger.error(f"Power check failed: {str(e)}")
        log_error_context(e)
        raise
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        log_error_context(e)
        raise

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Plant Disease Resistance Prediction Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to data manifest file (default: data/data_manifest.yaml)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for artifacts (default: artifacts/)"
    )
    
    parser.add_argument(
        "--train-test-split",
        type=float,
        default=0.8,
        help="Proportion of data to use for training (default: 0.8)"
    )
    
    parser.add_argument(
        "--feature-selection-threshold",
        type=float,
        default=0.05,
        help="Threshold for feature selection (default: 0.05)"
    )
    
    parser.add_argument(
        "--permutation-iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (default: 1000)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # Run the pipeline
    log_pipeline_step("Pipeline Started", "main.py")
    run_pipeline(args)
    log_pipeline_step("Pipeline Completed", "main.py")

if __name__ == "__main__":
    main()