"""
Validation logic to exclude samples with missing performance metrics.

This module implements US-1 Scenario 3: validation logic to exclude samples
with missing performance metrics and log warnings with specific sample IDs.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required performance metrics columns as defined in the data model
REQUIRED_PERFORMANCE_COLUMNS = [
    'PCE',    # Power Conversion Efficiency
    'J_sc',   # Short-circuit current density
    'V_oc'    # Open-circuit voltage
]


def identify_missing_metrics(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Identify samples with missing performance metrics.

    Args:
        df: Input DataFrame containing sample data with performance metrics.
        required_columns: List of column names to check for missing values.
                         Defaults to REQUIRED_PERFORMANCE_COLUMNS.

    Returns:
        Tuple containing:
        - valid_df: DataFrame with only samples that have all required metrics
        - missing_sample_ids: List of sample IDs with missing metrics
        - missing_columns_per_sample: List of strings describing which columns
                                    are missing for each excluded sample
    """
    if required_columns is None:
        required_columns = REQUIRED_PERFORMANCE_COLUMNS

    # Check which required columns exist in the DataFrame
    existing_columns = [col for col in required_columns if col in df.columns]
    missing_columns_in_schema = set(required_columns) - set(existing_columns)

    if missing_columns_in_schema:
        logger.warning(
            f"Required columns missing from schema: {missing_columns_in_schema}. "
            f"Only checking available columns: {existing_columns}"
        )

    if not existing_columns:
        raise ValueError(
            f"No required performance metric columns found in DataFrame. "
            f"Expected at least one of: {required_columns}"
        )

    # Identify rows with any missing values in the required columns
    mask = df[existing_columns].isna().any(axis=1)
    missing_sample_ids = df.loc[mask, 'sample_id'].tolist()

    # Build detailed description of missing columns per sample
    missing_columns_per_sample = []
    for sample_id in missing_sample_ids:
        sample_row = df[df['sample_id'] == sample_id].iloc[0]
        missing_cols = [
            col for col in existing_columns
            if pd.isna(sample_row[col])
        ]
        missing_columns_per_sample.append(
            f"Sample {sample_id}: missing {', '.join(missing_cols)}"
        )

    # Log warnings for each excluded sample
    for sample_id in missing_sample_ids:
        sample_row = df[df['sample_id'] == sample_id].iloc[0]
        missing_cols = [
            col for col in existing_columns
            if pd.isna(sample_row[col])
        ]
        logger.warning(
            f"Excluding sample '{sample_id}' due to missing performance metrics: "
            f"{', '.join(missing_cols)}"
        )

    # Return filtered DataFrame (samples with all required metrics)
    valid_df = df.loc[~mask].copy()

    return valid_df, missing_sample_ids, missing_columns_per_sample


def validate_and_filter_metrics(
    input_path: str,
    output_path: str,
    required_columns: Optional[List[str]] = None
) -> dict:
    """
    Load dataset, validate performance metrics, and write filtered output.

    This is the main entry point for the validation task. It reads the unified
    dataset, identifies and excludes samples with missing performance metrics,
    logs warnings with specific sample IDs, and writes the filtered dataset.

    Args:
        input_path: Path to the input CSV file (unified dataset)
        output_path: Path to write the filtered CSV output
        required_columns: Optional list of columns to validate

    Returns:
        Dictionary with validation statistics:
        - total_samples: Total number of samples in input
        - valid_samples: Number of samples after filtering
        - excluded_count: Number of excluded samples
        - excluded_sample_ids: List of excluded sample IDs
    """
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} samples")

    valid_df, missing_ids, missing_details = identify_missing_metrics(
        df, required_columns
    )

    excluded_count = len(missing_ids)
    valid_count = len(valid_df)

    logger.info(f"Validation complete: {valid_count} valid, {excluded_count} excluded")

    if excluded_count > 0:
        logger.warning(
            f"Excluded {excluded_count} samples due to missing metrics. "
            f"Excluded IDs: {missing_ids}"
        )

    # Write filtered dataset
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    valid_df.to_csv(output_path, index=False)
    logger.info(f"Wrote filtered dataset to {output_path}")

    return {
        'total_samples': len(df),
        'valid_samples': valid_count,
        'excluded_count': excluded_count,
        'excluded_sample_ids': missing_ids,
        'missing_details': missing_details
    }


def main():
    """
    Main entry point for command-line execution.

    Expected to be called from the pipeline with paths to input and output files.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate and filter samples with missing performance metrics'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input unified dataset CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to output filtered dataset CSV'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level.upper()))

    stats = validate_and_filter_metrics(
        input_path=args.input,
        output_path=args.output
    )

    logger.info(f"Validation summary: {stats}")

    # Return non-zero exit code if any samples were excluded
    if stats['excluded_count'] > 0:
        logger.warning(
            f"Pipeline warning: {stats['excluded_count']} samples were excluded "
            f"due to missing performance metrics."
        )

    return 0


if __name__ == '__main__':
    main()
