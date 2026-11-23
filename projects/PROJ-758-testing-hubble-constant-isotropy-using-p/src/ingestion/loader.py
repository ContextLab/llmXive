"""
Data ingestion module for the Pantheon+ supernova dataset.

This module handles loading raw CSV data, applying quality cuts (redshift < 0.15,
quality flags), and verifying data integrity using checksums.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

from src.utils.logger import get_logger, log_data_filtering, log_error
from src.utils.data_integrity import compute_checksum, verify_checksum, validate_raw_data
from src.utils.config import get_project_paths

logger = get_logger(__name__)


def load_raw_data(raw_data_path: Path) -> pd.DataFrame:
    """
    Load the raw Pantheon+ CSV dataset from disk.

    Args:
        raw_data_path: Path to the raw CSV file (e.g., data/raw/pantheon_plus.csv).

    Returns:
        DataFrame containing the raw supernova data.

    Raises:
        FileNotFoundError: If the raw data file does not exist.
        ValueError: If the file is empty or cannot be parsed.
    """
    logger.info(f"Loading raw data from {raw_data_path}")

    if not raw_data_path.exists():
        log_error(logger, f"Raw data file not found: {raw_data_path}")
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")

    try:
        df = pd.read_csv(raw_data_path)
        if df.empty:
            log_error(logger, "Loaded DataFrame is empty.")
            raise ValueError("Loaded DataFrame is empty.")
        
        # Verify basic integrity (non-null counts, etc.)
        validate_raw_data(df, logger)
        
        logger.info(f"Successfully loaded {len(df)} rows from {raw_data_path}")
        return df
    except Exception as e:
        log_error(logger, f"Failed to parse CSV: {e}")
        raise


def apply_redshift_cut(df: pd.DataFrame, max_z: float = 0.15) -> Tuple[pd.DataFrame, int]:
    """
    Apply a redshift cut to the dataset.

    Filters out supernovae with redshift >= max_z.

    Args:
        df: Input DataFrame.
        max_z: Maximum redshift threshold (default 0.15).

    Returns:
        Tuple of (filtered DataFrame, count of removed rows).
    """
    initial_count = len(df)
    if 'z' not in df.columns:
        log_error(logger, "Column 'z' (redshift) not found in DataFrame.")
        raise ValueError("Column 'z' (redshift) not found in DataFrame.")

    mask = df['z'] < max_z
    filtered_df = df[mask].copy()
    removed_count = initial_count - len(filtered_df)

    log_data_filtering(
        logger, 
        "redshift_cut", 
        f"z < {max_z}", 
        initial_count, 
        len(filtered_df), 
        removed_count
    )
    
    return filtered_df, removed_count


def apply_quality_flags(df: pd.DataFrame, quality_col: str = 'quality_flag') -> Tuple[pd.DataFrame, int]:
    """
    Filter the dataset based on quality flags.

    Keeps only rows where the quality flag indicates valid data.
    Assuming valid data is represented by 1 or 'valid' (adjust based on actual schema).
    If the column is missing, we assume all data is valid and log a warning.

    Args:
        df: Input DataFrame.
        quality_col: Name of the quality flag column.

    Returns:
        Tuple of (filtered DataFrame, count of removed rows).
    """
    initial_count = len(df)

    if quality_col not in df.columns:
        logger.warning(f"Quality column '{quality_col}' not found. Skipping quality filter.")
        log_data_filtering(
            logger, 
            "quality_filter", 
            f"Column '{quality_col}' missing", 
            initial_count, 
            initial_count, 
            0, 
            note="Column missing, no rows removed"
        )
        return df, 0

    # Assuming 1 indicates valid quality. Adjust logic if schema differs (e.g., string 'valid').
    # We keep rows where quality_flag is 1 or 'valid'.
    valid_values = [1, 'valid', '1']
    mask = df[quality_col].isin(valid_values)
    filtered_df = df[mask].copy()
    removed_count = initial_count - len(filtered_df)

    log_data_filtering(
        logger, 
        "quality_filter", 
        f"{quality_col} in {valid_values}", 
        initial_count, 
        len(filtered_df), 
        removed_count
    )

    return filtered_df, removed_count


def verify_data_integrity(df: pd.DataFrame, checksum_path: Optional[Path] = None) -> bool:
    """
    Verify the integrity of the processed data using checksums.

    If a checksum_path is provided, it verifies against that stored checksum.
    Otherwise, it computes a checksum for the current state to be stored later.

    Args:
        df: The DataFrame to verify.
        checksum_path: Optional path to a file containing the expected checksum.

    Returns:
        True if verification passes (or if no checksum path provided).
        
    Raises:
        ValueError: If verification fails against the provided checksum.
    """
    logger.info("Verifying data integrity...")
    
    # Compute checksum of the current DataFrame (serialized as CSV in memory)
    current_checksum = compute_checksum(df)
    logger.debug(f"Computed checksum for current data: {current_checksum}")

    if checksum_path and checksum_path.exists():
        expected_checksum = verify_checksum(checksum_path, logger)
        if expected_checksum is None:
            logger.warning("Could not read expected checksum. Skipping comparison.")
            return True
        
        if current_checksum != expected_checksum:
            log_error(logger, f"Checksum mismatch! Expected: {expected_checksum}, Got: {current_checksum}")
            raise ValueError(f"Data integrity check failed: Checksum mismatch.")
        
        logger.info("Data integrity verified successfully against stored checksum.")
    else:
        logger.info("No checksum file provided or found. Skipping comparison.")
        
    return True


def load_and_clean_data(
    raw_path: Path, 
    output_path: Optional[Path] = None,
    max_z: float = 0.15,
    quality_col: str = 'quality_flag',
    verify_checksum_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main entry point to load, clean, and verify the Pantheon+ dataset.

    1. Loads raw CSV.
    2. Applies redshift cut (z < max_z).
    3. Applies quality flag filter.
    4. Verifies data integrity.
    5. Optionally saves the cleaned data.

    Args:
        raw_path: Path to the raw input CSV.
        output_path: Optional path to save the cleaned CSV/Parquet.
        max_z: Redshift threshold.
        quality_col: Name of the quality column.
        verify_checksum_path: Optional path to checksum file for verification.

    Returns:
        Cleaned DataFrame.
    """
    # 1. Load
    df = load_raw_data(raw_path)

    # 2. Redshift Cut
    df, _ = apply_redshift_cut(df, max_z=max_z)

    # 3. Quality Filter
    df, _ = apply_quality_flags(df, quality_col=quality_col)

    # 4. Integrity Check
    verify_data_integrity(df, verify_checksum_path)

    # 5. Save if requested
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Save as CSV for transparency, or parquet for efficiency. 
        # Task description implies saving to processed, let's save as parquet if extension matches, else csv.
        if str(output_path).endswith('.parquet'):
            df.to_parquet(output_path, index=False)
            logger.info(f"Cleaned data saved to {output_path} (Parquet)")
        else:
            df.to_csv(output_path, index=False)
            logger.info(f"Cleaned data saved to {output_path} (CSV)")

    return df


def main():
    """
    Script entry point to run the data ingestion pipeline.
    Reads paths from environment or config, processes data, and saves to data/processed.
    """
    logger.info("Starting Pantheon+ data ingestion pipeline (T015).")
    
    try:
        paths = get_project_paths()
        raw_path = paths['data_raw'] / 'pantheon_plus.csv'
        output_path = paths['data_processed'] / 'pantheon_plus_cleaned.csv'
        
        # Note: T014 is responsible for downloading and checksumming the raw file.
        # We assume it exists here.
        
        if not raw_path.exists():
            log_error(logger, f"Raw data file missing: {raw_path}. Did T014 run?")
            raise FileNotFoundError(f"Raw data file missing: {raw_path}")

        cleaned_df = load_and_clean_data(
            raw_path=raw_path,
            output_path=output_path,
            max_z=0.15,
            quality_col='quality_flag'
        )

        logger.info(f"Ingestion complete. Rows remaining: {len(cleaned_df)}")
        
    except Exception as e:
        log_error(logger, f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()