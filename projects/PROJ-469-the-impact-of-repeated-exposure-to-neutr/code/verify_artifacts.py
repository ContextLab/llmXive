"""
Verification script for T032: Ensure all artifacts are written to results/ directory
with correct filenames and constraints (PDF <= 5 MB).

This script validates:
1. All expected result files exist in the results/ directory.
2. The generated PDF report exists and is <= 5 MB.
3. All CSV files are non-empty and readable.
4. File naming conventions are respected.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config_manager import get_results_path, get_config
from logging_config import setup_logging, get_logger

# Define expected artifacts based on the pipeline
EXPECTED_ARTIFACTS = {
    # Power Analysis
    'power_design.csv': {'type': 'csv', 'max_size_mb': None},
    'power_analysis.csv': {'type': 'csv', 'max_size_mb': None},
    
    # Model Results
    'model_summary.csv': {'type': 'csv', 'max_size_mb': None},
    'diagnostics.csv': {'type': 'csv', 'max_size_mb': None},
    'binary_model.csv': {'type': 'csv', 'max_size_mb': None},
    
    # Robustness Metrics
    'robustness_metrics.csv': {'type': 'csv', 'max_size_mb': None},
    'alpha_sweep.csv': {'type': 'csv', 'max_size_mb': None},
    
    # Report
    'report.pdf': {'type': 'pdf', 'max_size_mb': 5.0},
}

def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.exists()

def check_file_size(file_path: Path, max_size_mb: float) -> Tuple[bool, float]:
    """Check if file size is within limits."""
    if not file_path.exists():
        return False, 0.0
    
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    if max_size_mb is not None and size_mb > max_size_mb:
        return False, size_mb
    return True, size_mb

def check_csv_readable(file_path: Path) -> bool:
    """Check if a CSV file is readable and non-empty."""
    if not file_path.exists():
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        return len(df) > 0
    except Exception as e:
        logging.warning(f"Error reading CSV {file_path}: {e}")
        return False

def validate_artifacts(results_dir: Path) -> Dict[str, Any]:
    """Validate all expected artifacts in the results directory."""
    validation_results = {
        'total_artifacts': len(EXPECTED_ARTIFACTS),
        'passed': 0,
        'failed': 0,
        'details': []
    }

    for filename, constraints in EXPECTED_ARTIFACTS.items():
        file_path = results_dir / filename
        file_status = {
            'filename': filename,
            'exists': False,
            'size_mb': 0.0,
            'size_ok': False,
            'content_ok': False,
            'passed': False,
            'error': None
        }

        # Check existence
        if check_file_exists(file_path):
            file_status['exists'] = True
            
            # Check size
            size_ok, size_mb = check_file_size(file_path, constraints['max_size_mb'])
            file_status['size_mb'] = size_mb
            file_status['size_ok'] = size_ok
            
            # Check content based on type
            if constraints['type'] == 'csv':
                content_ok = check_csv_readable(file_path)
                file_status['content_ok'] = content_ok
            elif constraints['type'] == 'pdf':
                # For PDF, just check if it's not empty (basic check)
                if file_path.stat().st_size > 0:
                    file_status['content_ok'] = True
            
            # Overall pass
            file_status['passed'] = file_status['exists'] and file_status['size_ok'] and file_status['content_ok']
        else:
            file_status['error'] = "File does not exist"
        
        validation_results['details'].append(file_status)
        
        if file_status['passed']:
            validation_results['passed'] += 1
        else:
            validation_results['failed'] += 1

    return validation_results

def main():
    """Main entry point for artifact verification."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting artifact verification for T032...")
    
    # Get results directory
    config = get_config()
    results_dir = get_results_path()
    
    logger.info(f"Checking artifacts in: {results_dir}")
    
    # Validate artifacts
    results = validate_artifacts(results_dir)
    
    # Log results
    logger.info(f"Validation complete: {results['passed']}/{results['total_artifacts']} artifacts passed")
    
    if results['failed'] > 0:
        logger.error("The following artifacts failed validation:")
        for detail in results['details']:
            if not detail['passed']:
                logger.error(f"  - {detail['filename']}: {detail.get('error', 'Unknown error')}")
                if detail['size_mb'] > 0:
                    logger.error(f"    Size: {detail['size_mb']:.2f} MB")
        return 1
    else:
        logger.info("All artifacts validated successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
