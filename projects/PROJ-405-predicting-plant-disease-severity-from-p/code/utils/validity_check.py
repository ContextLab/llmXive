"""
Validity check utilities for the plant disease severity pipeline.

This module provides functions to validate the quality and integrity
of the processed data and model outputs.
"""
import logging
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from config import get_path
from utils.reporting import load_results, save_results

logger = logging.getLogger(__name__)

VALIDITY_CHECK_SAMPLE_SIZE = 50
CORRELATION_THRESHOLD = 0.5


def run_validity_check(dataset_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run validity checks on a random subset of the unified dataset.
    
    Since this is an observational study with no ground truth (per spec assumptions),
    this function logs "Associational Only" and skips correlation checks against
    expert scores. It validates data integrity and logs any issues found.
    
    Args:
        dataset_path: Path to the unified analysis CSV. If None, uses default path.
        
    Returns:
        Dictionary containing validity check results and flags.
    """
    if dataset_path is None:
        dataset_path = get_path('unified_analysis.csv')
    
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    # Load dataset
    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded dataset with {len(df)} records for validity check")
    
    # Sample random subset
    sample_size = min(VALIDITY_CHECK_SAMPLE_SIZE, len(df))
    random.seed(42)  # For reproducibility
    sample_indices = random.sample(range(len(df)), sample_size)
    sample_df = df.iloc[sample_indices]
    
    results = {
        'sample_size': sample_size,
        'total_records': len(df),
        'missing_values': {},
        'data_types_valid': True,
        'outliers_detected': [],
        'associational_only': True,  # Per spec assumption
        'correlation_check_skipped': True,
        'issues_found': []
    }
    
    # Check for missing values in key columns
    key_columns = [
        'lesion_area_ratio', 'necrosis_color_index', 'texture_entropy',
        'mean_temp', 'mean_humidity', 'total_precipitation'
    ]
    
    for col in key_columns:
        if col in sample_df.columns:
            missing_count = sample_df[col].isnull().sum()
            if missing_count > 0:
                results['missing_values'][col] = missing_count
                results['issues_found'].append(
                    f"Missing {missing_count} values in {col}"
                )
    
    # Validate data types
    numeric_columns = [
        'lesion_area_ratio', 'necrosis_color_index', 'texture_entropy',
        'mean_temp', 'mean_humidity', 'total_precipitation',
        'location_lat', 'location_lon'
    ]
    
    for col in numeric_columns:
        if col in sample_df.columns:
            if not pd.api.types.is_numeric_dtype(sample_df[col]):
                results['data_types_valid'] = False
                results['issues_found'].append(
                    f"Column {col} is not numeric"
                )
    
    # Check for outliers (simple IQR method)
    for col in numeric_columns:
        if col in sample_df.columns:
            q1 = sample_df[col].quantile(0.25)
            q3 = sample_df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = sample_df[
                (sample_df[col] < lower_bound) | (sample_df[col] > upper_bound)
            ]
            
            if len(outliers) > 0:
                results['outliers_detected'].append({
                    'column': col,
                    'count': len(outliers),
                    'percentage': f"{len(outliers)/len(sample_df)*100:.1f}%"
                })
    
    # Log results
    logger.info(f"Validity check completed: {len(results['issues_found'])} issues found")
    for issue in results['issues_found']:
        logger.warning(f"Validity issue: {issue}")
    
    # Since no ground truth exists, flag as associational only
    logger.info("Associational Only: No ground truth available for correlation check")
    
    return results


def update_results_with_validity_flag(validity_results: Dict[str, Any]) -> None:
    """
    Update the main results.json with validity check findings.
    
    Args:
        validity_results: Dictionary from run_validity_check()
    """
    results = load_results()
    
    # Add validity check section
    results['data_quality'] = {
        'associational_only': validity_results['associational_only'],
        'correlation_check_skipped': validity_results['correlation_check_skipped'],
        'sample_size_checked': validity_results['sample_size'],
        'total_records': validity_results['total_records'],
        'missing_values': validity_results['missing_values'],
        'data_types_valid': validity_results['data_types_valid'],
        'outliers_detected': validity_results['outliers_detected'],
        'issues_count': len(validity_results['issues_found']),
        'issues_summary': validity_results['issues_found']
    }
    
    # Flag study type
    if validity_results['associational_only']:
        results['study_type'] = 'observational_associational'
        results['hypothesis_test']['null_result_flag'] = results['hypothesis_test'].get(
            'p_value', 1.0
        ) >= 0.05
    
    save_results(results)
    logger.info("Validity check results updated in results.json")


def main():
    """Main entry point for validity check."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Starting validity check...")
    
    try:
        # Run validity check
        validity_results = run_validity_check()
        
        # Update results
        update_results_with_validity_flag(validity_results)
        
        # Summary
        logger.info("=" * 50)
        logger.info("Validity Check Summary")
        logger.info("=" * 50)
        logger.info(f"Sample size: {validity_results['sample_size']}")
        logger.info(f"Total records: {validity_results['total_records']}")
        logger.info(f"Issues found: {len(validity_results['issues_found'])}")
        logger.info(f"Associational only: {validity_results['associational_only']}")
        
        if validity_results['outliers_detected']:
            logger.info("Outliers detected:")
            for outlier in validity_results['outliers_detected']:
                logger.info(f"  - {outlier['column']}: {outlier['count']} "
                          f"({outlier['percentage']})")
        
        logger.info("Validity check completed successfully")
        
    except Exception as e:
        logger.error(f"Validity check failed: {str(e)}", exc_info=True)
        raise


if __name__ == '__main__':
    main()