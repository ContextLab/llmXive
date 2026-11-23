"""
Validate completeness of the dataset after property filtering (T017a).

Task: T017b [US1]
Description: Ensure ≥95% of compositions have all required properties.
Output: data/processed/completeness_check.json

This script loads the filtered dataset (output of T017a), calculates the
percentage of rows that have all required properties (non-null), and
writes a JSON report.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_processed_data_path, ensure_data_directories
from utils.io import load_csv, save_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required properties/descriptors as defined in T009 and T017a
REQUIRED_PROPERTIES = [
    'atomic_radius',
    'electronegativity',
    'vec',  # Valence Electron Concentration
    'size_mismatch',  # Atomic Size Mismatch (δ)
    'mixing_enthalpy',  # Mixing Enthalpy (ΔHmix)
    'electronegativity_diff'
]

def validate_completeness(df: Any) -> Dict[str, Any]:
    """
    Validate that ≥95% of compositions have all required properties.
    
    Args:
        df: Pandas DataFrame containing the dataset.
        
    Returns:
        Dictionary with validation results.
    """
    total_rows = len(df)
    if total_rows == 0:
        logger.warning("Dataset is empty. Cannot validate completeness.")
        return {
            'total_rows': 0,
            'rows_with_all_properties': 0,
            'rows_missing_properties': 0,
            'completeness_percentage': 0.0,
            'threshold': 0.95,
            'status': 'FAIL',
            'message': 'Dataset is empty'
        }

    # Check for required columns
    missing_cols = [col for col in REQUIRED_PROPERTIES if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        # If columns are missing, we can't compute the metric accurately
        # Return a failure state indicating missing schema
        return {
            'total_rows': total_rows,
            'rows_with_all_properties': 0,
            'rows_missing_properties': total_rows,
            'completeness_percentage': 0.0,
            'threshold': 0.95,
            'status': 'FAIL',
            'message': f'Missing required columns: {missing_cols}',
            'missing_columns': missing_cols
        }

    # Count rows with all required properties (non-null)
    rows_with_all = df[REQUIRED_PROPERTIES].dropna().shape[0]
    rows_missing = total_rows - rows_with_all
    
    completeness_pct = (rows_with_all / total_rows) * 100.0
    threshold = 95.0
    
    status = 'PASS' if completeness_pct >= threshold else 'FAIL'
    
    logger.info(f"Total rows: {total_rows}")
    logger.info(f"Rows with all properties: {rows_with_all}")
    logger.info(f"Rows missing properties: {rows_missing}")
    logger.info(f"Completeness: {completeness_pct:.2f}%")
    logger.info(f"Threshold: {threshold}%")
    logger.info(f"Status: {status}")

    return {
        'total_rows': total_rows,
        'rows_with_all_properties': rows_with_all,
        'rows_missing_properties': rows_missing,
        'completeness_percentage': round(completeness_pct, 2),
        'threshold_percentage': threshold,
        'status': status,
        'message': f"Completeness check {'passed' if status == 'PASS' else 'failed'}."
    }

def main():
    """Main entry point for T017b."""
    ensure_data_directories()
    
    # Path to the filtered properties dataset (output of T017a)
    input_path = get_processed_data_path() / "filtered_properties.csv"
    
    if not input_path.exists():
        error_msg = f"Input file not found: {input_path}"
        logger.error(error_msg)
        # Create a failure report
        report = {
            'total_rows': 0,
            'rows_with_all_properties': 0,
            'rows_missing_properties': 0,
            'completeness_percentage': 0.0,
            'threshold_percentage': 95.0,
            'status': 'FAIL',
            'message': f'Input file not found: {input_path}',
            'error': 'FileNotFound'
        }
        output_path = get_processed_data_path() / "completeness_check.json"
        save_json(output_path, report)
        sys.exit(1)
    
    logger.info(f"Loading dataset from: {input_path}")
    try:
        df = load_csv(input_path)
    except Exception as e:
        error_msg = f"Failed to load dataset: {e}"
        logger.error(error_msg)
        report = {
            'total_rows': 0,
            'rows_with_all_properties': 0,
            'rows_missing_properties': 0,
            'completeness_percentage': 0.0,
            'threshold_percentage': 95.0,
            'status': 'FAIL',
            'message': f'Failed to load dataset: {e}',
            'error': str(e)
        }
        output_path = get_processed_data_path() / "completeness_check.json"
        save_json(output_path, report)
        sys.exit(1)

    # Validate completeness
    result = validate_completeness(df)
    
    # Save results
    output_path = get_processed_data_path() / "completeness_check.json"
    logger.info(f"Saving completeness check report to: {output_path}")
    save_json(output_path, result)
    
    # Exit with appropriate code
    if result['status'] == 'FAIL':
        logger.error("Completeness check failed. Pipeline should halt or trigger fallback.")
        sys.exit(2)
    else:
        logger.info("Completeness check passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()