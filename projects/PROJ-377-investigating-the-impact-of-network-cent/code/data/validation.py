"""
Validation module for data quality checks.
Implements retention rate validation and behavioral data integrity checks.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from utils.logging import setup_logger
from utils.config import get_config, get_min_retention_rate

logger = setup_logger(__name__)

def validate_retention_and_behavioral_data(
    processed_data_path: Path,
    retention_threshold: Optional[float] = None
) -> Tuple[bool, dict]:
    """
    Validates subject retention rate and checks for missing behavioral data.
    
    Args:
        processed_data_path: Path to the processed behavioral data CSV
        retention_threshold: Minimum required retention rate (default from config)
        
    Returns:
        Tuple of (is_valid, validation_report)
        
    Raises:
        ValueError: If retention rate is below threshold or critical behavioral data is missing
    """
    if retention_threshold is None:
        config = get_config()
        retention_threshold = get_min_retention_rate()
    
    if not processed_data_path.exists():
        error_msg = f"Processed data file not found: {processed_data_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        df = pd.read_csv(processed_data_path)
    except Exception as e:
        error_msg = f"Failed to read processed data file: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Calculate retention metrics
    total_subjects_expected = df.get('total_subjects_expected', len(df))
    total_subjects_actual = len(df)
    
    # Check for missing critical behavioral columns
    required_columns = ['subject_id', 'pre_score', 'post_score', 'improvement']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"Missing required behavioral columns: {missing_columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for missing values in critical columns
    behavioral_missing = df[required_columns].isnull().sum()
    if behavioral_missing.any():
        missing_info = {col: int(count) for col, count in behavioral_missing.items() if count > 0}
        error_msg = f"Missing values in behavioral data: {missing_info}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Calculate retention rate
    retention_rate = total_subjects_actual / total_subjects_expected if total_subjects_expected > 0 else 0.0
    
    validation_report = {
        'total_subjects_expected': int(total_subjects_expected),
        'total_subjects_actual': int(total_subjects_actual),
        'retention_rate': float(retention_rate),
        'retention_threshold': float(retention_threshold),
        'retention_passed': retention_rate >= retention_threshold,
        'missing_columns': missing_columns,
        'missing_values': {col: int(count) for col, count in behavioral_missing.items()},
        'excluded_subjects': int(total_subjects_expected - total_subjects_actual)
    }
    
    logger.info(f"Retention rate: {retention_rate:.2%} (threshold: {retention_threshold:.2%})")
    logger.info(f"Subjects included: {total_subjects_actual}/{total_subjects_expected}")
    
    if not validation_report['retention_passed']:
        error_msg = (
            f"Retention rate {retention_rate:.2%} is below threshold {retention_threshold:.2%}. "
            f"Only {total_subjects_actual} subjects retained out of {total_subjects_expected}. "
            "Pipeline cannot proceed with insufficient data."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if missing_columns or any(behavioral_missing > 0):
        error_msg = "Critical behavioral data is missing or incomplete."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Validation passed: sufficient retention and complete behavioral data.")
    return True, validation_report

def main():
    """
    Main entry point for validation script.
    Runs validation checks on processed behavioral data.
    """
    config = get_config()
    output_paths = config.output_paths
    
    processed_data_path = output_paths.processed_behavioral_csv
    
    logger.info(f"Starting validation for: {processed_data_path}")
    
    try:
        is_valid, report = validate_retention_and_behavioral_data(processed_data_path)
        
        # Save validation report
        report_path = output_paths.validation_report_json
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to: {report_path}")
        logger.info("Validation completed successfully.")
        
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise

if __name__ == "__main__":
    main()