"""
Main entry point for the cognitive flexibility prediction pipeline.

This script orchestrates the entire pipeline from data ingestion to
final results generation and validation.
"""
import os
import sys
import logging
import argparse
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.config import set_seed, get_config
from code.data.paths import get_processed_path, get_results_path, ensure_dir
from code.data.download import run_download_pipeline
from code.data.preprocess import run_preprocessing_pipeline
from code.data.merge import run_merge_pipeline
from code.utils.motion import run_motion_filtering_pipeline
from code.data.validation import run_validation_pipeline, validate_final_results_file
from code.utils.logging import init_logging, log_error, log_warning, log_info

logger = logging.getLogger(__name__)

def run_pipeline(subject_ids: Optional[list] = None, force_redownload: bool = False) -> Dict[str, Any]:
    """
    Run the complete data processing and validation pipeline.
    
    Args:
        subject_ids: Optional list of specific subject IDs to process.
                    If None, processes all available subjects.
        force_redownload: If True, re-downloads data even if it exists.
        
    Returns:
        Dictionary with pipeline execution results
    """
    config = get_config()
    set_seed(config.get('seed', 42))
    
    logger.info("Starting cognitive flexibility prediction pipeline")
    logger.info(f"Configuration: window={config.get('window', 60)}, "
               f"step={config.get('step', 1)}, fd_threshold={config.get('FD_threshold', 0.2)}")
    
    results = {
        'download': None,
        'preprocessing': None,
        'merge': None,
        'motion_filtering': None,
        'validation': None,
        'success': False,
        'errors': []
    }
    
    try:
        # Step 1: Download data
        logger.info("Step 1: Downloading HCP data...")
        results['download'] = run_download_pipeline(subject_ids=subject_ids, force=force_redownload)
        if not results['download'].get('success', False):
            raise Exception("Download pipeline failed")
        
        # Step 2: Preprocess data
        logger.info("Step 2: Preprocessing data...")
        results['preprocessing'] = run_preprocessing_pipeline(subject_ids=subject_ids)
        if not results['preprocessing'].get('success', False):
            raise Exception("Preprocessing pipeline failed")
        
        # Step 3: Merge datasets
        logger.info("Step 3: Merging datasets...")
        results['merge'] = run_merge_pipeline()
        if not results['merge'].get('success', False):
            raise Exception("Merge pipeline failed")
        
        # Step 4: Apply motion filtering
        logger.info("Step 4: Applying motion filtering...")
        results['motion_filtering'] = run_motion_filtering_pipeline()
        if not results['motion_filtering'].get('success', False):
            raise Exception("Motion filtering pipeline failed")
        
        # Step 5: Validate final results
        logger.info("Step 5: Validating final results...")
        final_results_path = os.path.join(get_processed_path(), 'final_results.csv')
        
        # Check if file exists first
        if not os.path.exists(final_results_path):
            log_warning(f"Final results file not found at {final_results_path}. "
                       "This may indicate the pipeline did not complete successfully.")
            results['validation'] = {
                'valid': False,
                'errors': [f"File not found: {final_results_path}"],
                'row_count': 0
            }
            raise Exception("Final results file not found")
        
        results['validation'] = run_validation_pipeline(final_results_path)
        
        if not results['validation'].get('valid', False):
            error_msg = "Validation failed: " + "; ".join(results['validation'].get('errors', []))
            raise Exception(error_msg)
        
        logger.info(f"Pipeline completed successfully. Validated {results['validation']['row_count']} subjects.")
        results['success'] = True
        
    except Exception as e:
        log_error(f"Pipeline failed: {str(e)}")
        results['errors'].append(str(e))
        results['success'] = False
        
    return results

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Run the cognitive flexibility prediction pipeline')
    parser.add_argument('--subjects', type=str, nargs='+', help='Specific subject IDs to process')
    parser.add_argument('--force', action='store_true', help='Force re-download of data')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing results')
    
    args = parser.parse_args()
    
    init_logging()
    
    subject_ids = None
    if args.subjects:
        subject_ids = args.subjects
        logger.info(f"Processing specific subjects: {subject_ids}")
    
    if args.validate_only:
        logger.info("Running validation only...")
        final_results_path = os.path.join(get_processed_path(), 'final_results.csv')
        if os.path.exists(final_results_path):
            is_valid, errors, count = validate_final_results_file(final_results_path)
            if is_valid:
                print(f"Validation passed: {count} unique subjects found.")
                sys.exit(0)
            else:
                print(f"Validation failed:")
                for err in errors:
                    print(f"  - {err}")
                sys.exit(1)
        else:
            print(f"Validation file not found: {final_results_path}")
            sys.exit(1)
    
    results = run_pipeline(subject_ids=subject_ids, force_redownload=args.force)
    
    if results['success']:
        print("Pipeline completed successfully.")
        print(f"Validated {results['validation']['row_count']} unique subjects.")
        sys.exit(0)
    else:
        print("Pipeline failed.")
        for err in results['errors']:
            print(f"Error: {err}")
        sys.exit(1)

if __name__ == '__main__':
    main()