"""
Exclusion logic for low-reliability EBSD samples.

Implements the logic to flag and exclude samples where >50% of points
are filtered out during preprocessing, ensuring only high-quality data
is used for training.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger
from config import get_reductions

logger = get_logger(__name__)

# Threshold for exclusion: if more than 50% of points are filtered, mark as low reliability
RELIABILITY_THRESHOLD = 0.50

def calculate_reliability_metrics(
    df: pd.DataFrame,
    sample_id_col: str = "sample_id",
    filtered_col: str = "is_filtered",
    original_count_col: str = "original_point_count",
    filtered_count_col: str = "filtered_point_count"
) -> pd.DataFrame:
    """
    Calculate reliability metrics for each sample.

    Computes the ratio of filtered points to original points for each sample.
    Samples with a ratio > RELIABILITY_THRESHOLD are flagged as "low_reliability".

    Args:
        df: DataFrame containing EBSD data with sample identifiers and filter status.
            Expected columns: sample_id_col, filtered_col, original_count_col, filtered_count_col.
            If original_count_col or filtered_count_col are missing, they are derived
            by counting rows per sample.
        sample_id_col: Name of the column containing unique sample IDs.
        filtered_col: Name of the column indicating if a point was filtered (True/False).
        original_count_col: Name of the column with the original point count per sample.
        filtered_count_col: Name of the column with the filtered point count per sample.

    Returns:
        DataFrame with added columns:
            - reliability_ratio: Fraction of points filtered (0.0 to 1.0)
            - is_low_reliability: Boolean flag (True if ratio > threshold)
            - status: "low_reliability" or "valid"
    """
    logger.info(f"Calculating reliability metrics for {len(df)} rows...")

    # Ensure we have the necessary counts
    # If the count columns are not present, derive them from the data
    if original_count_col not in df.columns or filtered_count_col not in df.columns:
        logger.info("Deriving point counts from raw data...")
        # Count total points per sample
        total_counts = df.groupby(sample_id_col).size().reset_index(name='total_points')
        
        # Count filtered points per sample
        filtered_counts = df[df[filtered_col] == True].groupby(sample_id_col).size().reset_index(name='filtered_points')
        
        # Merge back
        df = df.merge(total_counts, on=sample_id_col, how='left')
        df = df.merge(filtered_counts, on=sample_id_col, how='left')
        
        # Fill NaN with 0 (for samples with no filtered points)
        df['filtered_points'] = df['filtered_points'].fillna(0)
        
        # Update column names to match expected interface if needed
        if original_count_col not in df.columns:
            df[original_count_col] = df['total_points']
        if filtered_count_col not in df.columns:
            df[filtered_count_col] = df['filtered_points']

    # Calculate reliability ratio
    # Avoid division by zero
    df['reliability_ratio'] = df[filtered_count_col] / df[original_count_col].replace(0, 1)
    
    # Apply threshold
    df['is_low_reliability'] = df['reliability_ratio'] > RELIABILITY_THRESHOLD
    df['status'] = df['is_low_reliability'].map({True: 'low_reliability', False: 'valid'})

    logger.info(f"Reliability calculation complete. "
                f"Samples flagged: {df['is_low_reliability'].sum()}, "
                f"Total samples: {df[sample_id_col].nunique()}")

    return df

def apply_exclusion_logic(
    df: pd.DataFrame,
    sample_id_col: str = "sample_id",
    reliability_col: str = "is_low_reliability",
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Apply exclusion logic to remove low-reliability samples.

    Filters the DataFrame to exclude samples flagged as "low_reliability".
    Logs the excluded samples and writes a summary report if output_path is provided.

    Args:
        df: DataFrame with reliability metrics calculated (must contain reliability_col).
        sample_id_col: Column name for sample IDs.
        reliability_col: Column name for the low reliability flag.
        output_path: Optional path to write a summary report of excluded samples.

    Returns:
        DataFrame containing only valid (high-reliability) samples.
    """
    logger.info("Applying exclusion logic...")

    if reliability_col not in df.columns:
        raise ValueError(f"Column '{reliability_col}' not found in DataFrame. "
                         f"Run calculate_reliability_metrics first.")

    valid_samples = df[~df[reliability_col]]
    excluded_samples = df[df[reliability_col]]

    excluded_count = excluded_samples[sample_id_col].nunique()
    valid_count = valid_samples[sample_id_col].nunique()
    total_count = df[sample_id_col].nunique()

    logger.info(f"Exclusion complete: {excluded_count} samples excluded, "
                f"{valid_count} samples retained (out of {total_count} total).")

    if excluded_count > 0:
        logger.warning(f"The following samples were excluded due to >{RELIABILITY_THRESHOLD*100}% "
                       f"filtered points:")
        excluded_list = excluded_samples[sample_id_col].unique().tolist()
        for sid in excluded_list:
            logger.warning(f"  - {sid}")

    if output_path:
        _write_exclusion_report(excluded_samples, valid_samples, output_path)

    return valid_samples

def _write_exclusion_report(
    excluded_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Write a detailed report of excluded and valid samples to a CSV file.

    Args:
        excluded_df: DataFrame of excluded samples.
        valid_df: DataFrame of valid samples.
        output_path: Path to write the report CSV.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = []

    # Process excluded
    if not excluded_df.empty:
        excluded_summary = excluded_df.groupby('sample_id').agg({
            'reliability_ratio': 'first',
            'original_point_count': 'first',
            'filtered_point_count': 'first'
        }).reset_index()
        excluded_summary['status'] = 'excluded'
        report_data.append(excluded_summary)

    # Process valid
    if not valid_df.empty:
        valid_summary = valid_df.groupby('sample_id').agg({
            'reliability_ratio': 'first',
            'original_point_count': 'first',
            'filtered_count': 'first' # Fallback if column name varies
        }).reset_index()
        # Ensure column consistency
        if 'filtered_count' in valid_summary.columns and 'filtered_point_count' not in valid_summary.columns:
            valid_summary = valid_summary.rename(columns={'filtered_count': 'filtered_point_count'})
        
        valid_summary['status'] = 'valid'
        report_data.append(valid_summary)

    if report_data:
        full_report = pd.concat(report_data, ignore_index=True)
        full_report.to_csv(output_path, index=False)
        logger.info(f"Exclusion report written to {output_path}")
    else:
        logger.warning("No samples to report in exclusion summary.")

def main():
    """
    Main entry point for the exclusion module.
    Reads processed data, applies reliability checks, and outputs the clean dataset.
    """
    logger.info("Starting exclusion logic execution...")

    # Configuration
    # Assuming processed data is in data/interim/ or data/processed/
    # We look for the output of the preprocessing step
    input_dir = Path("data/interim")
    if not input_dir.exists():
        input_dir = Path("data/processed")
    
    # Find the most recent parquet or csv file with EBSD data
    # This is a heuristic; in a real pipeline, paths might be passed via config or CLI
    ebsd_files = list(input_dir.glob("*.parquet")) + list(input_dir.glob("*.csv"))
    
    if not ebsd_files:
        logger.error("No processed EBSD data files found in data/interim or data/processed. "
                     "Please ensure T012 (preprocess) has run successfully.")
        return

    # Sort by modification time, take newest
    ebsd_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_file = ebsd_files[0]
    
    logger.info(f"Processing file: {latest_file}")

    if latest_file.suffix == '.parquet':
        df = pd.read_parquet(latest_file)
    else:
        df = pd.read_csv(latest_file)

    if df.empty:
        logger.error("Input file is empty.")
        return

    # Ensure required columns exist (preprocessing should have added 'is_filtered')
    if 'is_filtered' not in df.columns:
        logger.error("Column 'is_filtered' not found in data. "
                     "Ensure T012 (preprocess) added this column.")
        return

    # Calculate metrics
    df_with_metrics = calculate_reliability_metrics(df)

    # Apply exclusion
    clean_df = apply_exclusion_logic(
        df_with_metrics,
        output_path=Path("data/processed/exclusion_report.csv")
    )

    # Save the clean dataset
    output_file = Path("data/processed/cleaned_ebsd.parquet")
    clean_df.to_parquet(output_file, index=False)
    logger.info(f"Clean dataset saved to {output_file}")

    return clean_df

if __name__ == "__main__":
    main()
