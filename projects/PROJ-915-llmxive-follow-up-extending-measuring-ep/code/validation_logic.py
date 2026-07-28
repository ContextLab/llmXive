"""
Validation logic for Task T015: Flagging prompts with undefined imperative ratio.

This module implements data validation logic to identify prompts where the
'imperative ratio' is undefined due to zero total sentences. This is a critical
data quality check before downstream statistical modeling.
"""

import os
import csv
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import pandas as pd

from config import get_config
from validation import validate_data_integrity

logger = logging.getLogger(__name__)

def flag_undefined_imperative_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag prompts where the imperative ratio is undefined (zero total sentences).

    The imperative ratio is calculated as:
        imperative_count / total_sentences

    If total_sentences is 0, the ratio is undefined. This function adds a
    boolean column 'undefined_imperative_ratio' to the dataframe.

    Args:
        df: DataFrame containing feature data with columns:
            - 'imperative_count': Number of imperative sentences
            - 'total_sentences': Total number of sentences

    Returns:
        DataFrame with added 'undefined_imperative_ratio' column
    """
    if df.empty:
        logger.warning("Empty dataframe provided to flag_undefined_imperative_ratio")
        df['undefined_imperative_ratio'] = False
        return df

    # Ensure required columns exist
    required_cols = ['imperative_count', 'total_sentences']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for imperative ratio calculation: {missing_cols}")

    # Flag rows where total_sentences is 0
    df['undefined_imperative_ratio'] = df['total_sentences'] == 0

    # Log statistics
    undefined_count = df['undefined_imperative_ratio'].sum()
    total_count = len(df)
    logger.info(f"Found {undefined_count} prompts with undefined imperative ratio out of {total_count} total prompts")

    return df

def validate_features_for_imperative_ratio(df: pd.DataFrame) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate features for imperative ratio issues.

    This function checks for:
    1. Prompts with zero total sentences (undefined ratio)
    2. Negative sentence counts (data integrity issue)
    3. Non-integer sentence counts

    Args:
        df: DataFrame containing feature data

    Returns:
        Tuple of (is_valid, list of validation issues)
    """
    issues = []
    is_valid = True

    if df.empty:
        issues.append({
            'issue_type': 'empty_dataframe',
            'severity': 'critical',
            'message': 'Feature dataframe is empty'
        })
        return False, issues

    # Check for required columns
    required_cols = ['imperative_count', 'total_sentences']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        issues.append({
            'issue_type': 'missing_columns',
            'severity': 'critical',
            'message': f'Missing required columns: {missing_cols}'
        })
        return False, issues

    # Check for zero total sentences
    zero_sentences = df[df['total_sentences'] == 0]
    if not zero_sentences.empty:
        issues.append({
            'issue_type': 'undefined_imperative_ratio',
            'severity': 'warning',
            'count': len(zero_sentences),
            'prompt_ids': zero_sentences['prompt_id'].tolist() if 'prompt_id' in zero_sentences.columns else [],
            'message': f"Found {len(zero_sentences)} prompts with zero total sentences (undefined imperative ratio)"
        })
        # This is a warning, not a failure - we can still proceed with other features
        is_valid = True  # Still valid, just flagged

    # Check for negative sentence counts
    negative_sentences = df[df['total_sentences'] < 0]
    if not negative_sentences.empty:
        issues.append({
            'issue_type': 'negative_sentence_count',
            'severity': 'critical',
            'count': len(negative_sentences),
            'message': f"Found {len(negative_sentences)} prompts with negative sentence counts"
        })
        is_valid = False

    # Check for non-integer sentence counts
    non_integer_sentences = df[~df['total_sentences'].apply(lambda x: isinstance(x, (int, float)) and x == int(x))]
    if not non_integer_sentences.empty:
        issues.append({
            'issue_type': 'non_integer_sentence_count',
            'severity': 'warning',
            'count': len(non_integer_sentences),
            'message': f"Found {len(non_integer_sentences)} prompts with non-integer sentence counts"
        })

    return is_valid, issues

def run_t015_validation_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run the T015 validation pipeline.

    This function:
    1. Loads the feature data from data/processed/features.csv
    2. Flags prompts with undefined imperative ratio
    3. Validates the data for imperative ratio issues
    4. Generates a validation report

    Args:
        config: Optional configuration dictionary. If None, uses default config.

    Returns:
        Dictionary containing validation results and report path
    """
    logger.info("Starting T015 validation pipeline")

    # Get configuration
    if config is None:
        config = get_config()

    # Define paths
    feature_path = Path(config['paths']['processed_features'])
    report_path = Path(config['paths']['validation_reports']) / 't015_validation_report.json'

    # Ensure report directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate data integrity first
    if not validate_data_integrity(feature_path):
        error_msg = f"Feature data integrity check failed for {feature_path}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'report_path': str(report_path)
        }

    # Load feature data
    try:
        df = pd.read_csv(feature_path)
        logger.info(f"Loaded {len(df)} rows from {feature_path}")
    except Exception as e:
        error_msg = f"Failed to load feature data from {feature_path}: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'report_path': str(report_path)
        }

    # Flag undefined imperative ratios
    df_flagged = flag_undefined_imperative_ratio(df)

    # Validate features
    is_valid, issues = validate_features_for_imperative_ratio(df_flagged)

    # Generate report
    report = {
        'task_id': 'T015',
        'status': 'completed' if is_valid else 'completed_with_issues',
        'timestamp': pd.Timestamp.now().isoformat(),
        'total_prompts': len(df),
        'undefined_imperative_ratio_count': int(df_flagged['undefined_imperative_ratio'].sum()),
        'validation_issues': issues,
        'is_valid': is_valid,
        'flagged_prompt_ids': df_flagged[df_flagged['undefined_imperative_ratio']]['prompt_id'].tolist() if 'prompt_id' in df_flagged.columns else []
    }

    # Save report
    try:
        with open(report_path, 'w') as f:
            import json
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {report_path}")
    except Exception as e:
        logger.error(f"Failed to save validation report: {str(e)}")

    # Save flagged dataframe
    flagged_output_path = Path(config['paths']['processed_features']).parent / 'features_flagged.csv'
    try:
        df_flagged.to_csv(flagged_output_path, index=False)
        logger.info(f"Flagged features saved to {flagged_output_path}")
        report['flagged_features_path'] = str(flagged_output_path)
    except Exception as e:
        logger.error(f"Failed to save flagged features: {str(e)}")

    logger.info(f"T015 validation pipeline completed. Issues found: {len(issues)}")
    return report

def main():
    """Main entry point for T015 validation pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        result = run_t015_validation_pipeline()
        if result['success']:
            print(f"T015 Validation completed successfully")
            print(f"Report saved to: {result['report_path']}")
            if 'flagged_features_path' in result:
                print(f"Flagged features saved to: {result['flagged_features_path']}")
            print(f"Undefined imperative ratio count: {result.get('undefined_imperative_ratio_count', 0)}")
        else:
            print(f"T015 Validation failed: {result.get('error', 'Unknown error')}")
            exit(1)
    except Exception as e:
        logger.exception("Unexpected error in T015 validation pipeline")
        print(f"Unexpected error: {str(e)}")
        exit(1)

if __name__ == '__main__':
    main()
