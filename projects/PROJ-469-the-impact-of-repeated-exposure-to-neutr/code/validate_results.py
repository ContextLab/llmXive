"""
Helper script to ensure all pipeline outputs are correctly written to results/
and meet size constraints. This script is called by main.py after pipeline execution.
"""
import os
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config_manager import get_results_path, get_config
from logging_config import get_logger

def ensure_results_directory():
    """Ensure the results directory exists."""
    results_dir = get_results_path()
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def validate_pdf_size(file_path: Path, max_size_mb: float = 5.0) -> bool:
    """Validate that a PDF file is within the size limit."""
    if not file_path.exists():
        logging.error(f"PDF file not found: {file_path}")
        return False
    
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    if size_mb > max_size_mb:
        logging.error(f"PDF file {file_path.name} exceeds size limit: {size_mb:.2f} MB > {max_size_mb} MB")
        return False
    
    logging.info(f"PDF file {file_path.name} is within size limit: {size_mb:.2f} MB")
    return True

def validate_csv_files(results_dir: Path) -> bool:
    """Validate that all expected CSV files exist and are non-empty."""
    expected_csv_files = [
        'power_design.csv',
        'power_analysis.csv',
        'model_summary.csv',
        'diagnostics.csv',
        'binary_model.csv',
        'robustness_metrics.csv',
        'alpha_sweep.csv'
    ]
    
    all_valid = True
    
    for csv_file in expected_csv_files:
        file_path = results_dir / csv_file
        
        if not file_path.exists():
            logging.error(f"Expected CSV file not found: {csv_file}")
            all_valid = False
            continue
        
        if file_path.stat().st_size == 0:
            logging.error(f"CSV file is empty: {csv_file}")
            all_valid = False
            continue
        
        # Try to read the CSV to ensure it's valid
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            if len(df) == 0:
                logging.error(f"CSV file has no data rows: {csv_file}")
                all_valid = False
            else:
                logging.info(f"CSV file validated: {csv_file} ({len(df)} rows)")
        except Exception as e:
            logging.error(f"Error reading CSV file {csv_file}: {e}")
            all_valid = False
    
    return all_valid

def run_validation():
    """Run all validation checks for results artifacts."""
    logger = get_logger(__name__)
    logger.info("Running results validation...")
    
    results_dir = ensure_results_directory()
    
    # Check PDF
    pdf_path = results_dir / 'report.pdf'
    pdf_valid = validate_pdf_size(pdf_path) if pdf_path.exists() else False
    
    # Check CSVs
    csv_valid = validate_csv_files(results_dir)
    
    # Overall result
    if pdf_valid and csv_valid:
        logger.info("All results validation checks passed!")
        return True
    else:
        logger.error("Some results validation checks failed.")
        return False

def main():
    """Main entry point."""
    success = run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())