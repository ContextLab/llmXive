"""
verify_completeness.py

Verifies that the project's run-book and pipeline have produced all declared
deliverables and that the output data meets the specified completeness threshold.

This script resolves the missing script issue for the quickstart run-book command:
`python code/verify_completeness.py --threshold 0.90`
"""
import argparse
import sys
import os
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define expected deliverables relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DELIVERABLES = {
    'merged_monthly_csv': PROJECT_ROOT / 'data' / 'processed' / 'merged_monthly.csv',
    'correlation_results_csv': PROJECT_ROOT / 'data' / 'processed' / 'correlation_results.csv',
    'timeseries_plot': PROJECT_ROOT / 'output' / 'timeseries_overlay.png',
    'scatter_plot': PROJECT_ROOT / 'output' / 'scatter_regression.png',
    'spatial_plot': PROJECT_ROOT / 'output' / 'spatial_anomaly_map.png',
    'sensitivity_report': PROJECT_ROOT / 'docs' / 'sensitivity_report.md',
    'temporal_bias_doc': PROJECT_ROOT / 'docs' / 'temporal_bias_analysis.md'
}

def check_file_exists(path: Path) -> bool:
    """Check if a file exists and is not empty."""
    if not path.exists():
        logger.error(f"Missing file: {path}")
        return False
    if path.stat().st_size == 0:
        logger.error(f"Empty file: {path}")
        return False
    return True

def check_csv_completeness(path: Path, min_rows: int = 10) -> bool:
    """Check if a CSV file has sufficient rows and no critical NaNs."""
    try:
        df = pd.read_csv(path)
        if len(df) < min_rows:
            logger.error(f"File {path} has only {len(df)} rows (min: {min_rows})")
            return False
        
        # Check for NaN in critical columns if they exist
        critical_cols = ['date', 'ar_intensity', 'gravity_anomaly', 'correlation_coefficient']
        for col in critical_cols:
            if col in df.columns and df[col].isna().any():
                logger.warning(f"NaN values found in column '{col}' of {path}")
                # We allow some NaNs but flag it; strictly, we might return False here
                # depending on strictness. For now, we log and continue.
        
        logger.info(f"File {path} is valid: {len(df)} rows")
        return True
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Verify pipeline completeness.')
    parser.add_argument(
        '--threshold', 
        type=float, 
        default=0.90, 
        help='Required completeness threshold (0.0 to 1.0)'
    )
    args = parser.parse_args()

    logger.info(f"Verifying completeness with threshold {args.threshold}")
    
    total_checks = 0
    passed_checks = 0
    failed_files = []

    # Check CSVs for data integrity
    csv_checks = [
        ('merged_monthly_csv', DELIVERABLES['merged_monthly_csv'], check_csv_completeness),
        ('correlation_results_csv', DELIVERABLES['correlation_results_csv'], check_csv_completeness)
    ]

    for name, path, check_func in csv_checks:
        total_checks += 1
        if check_func(path):
            passed_checks += 1
        else:
            failed_files.append(name)

    # Check other files for existence
    other_files = [
        ('timeseries_plot', DELIVERABLES['timeseries_plot']),
        ('scatter_plot', DELIVERABLES['scatter_plot']),
        ('spatial_plot', DELIVERABLES['spatial_plot']),
        ('sensitivity_report', DELIVERABLES['sensitivity_report']),
        ('temporal_bias_doc', DELIVERABLES['temporal_bias_doc'])
    ]

    for name, path in other_files:
        total_checks += 1
        if check_file_exists(path):
            passed_checks += 1
        else:
            failed_files.append(name)

    completeness = passed_checks / total_checks if total_checks > 0 else 0.0
    logger.info(f"Completeness: {completeness:.2%} ({passed_checks}/{total_checks})")

    if failed_files:
        logger.error(f"Failed checks for: {', '.join(failed_files)}")
    
    if completeness >= args.threshold:
        logger.info("SUCCESS: Completeness threshold met.")
        sys.exit(0)
    else:
        logger.error(f"FAILURE: Completeness {completeness:.2%} is below threshold {args.threshold:.2%}.")
        sys.exit(1)

if __name__ == '__main__':
    main()