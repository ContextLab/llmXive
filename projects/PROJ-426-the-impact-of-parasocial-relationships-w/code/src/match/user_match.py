"""
User Matching Module for Parasocial Relationships Research

This module handles the matching of users between the loneliness dataset
and Pushshift logs by hashing usernames to create deterministic, anonymized IDs.
"""
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd
from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context

logger = get_logger(__name__)


def hash_username(username: str) -> str:
    """
    Hash a raw username using SHA-256 (UTF-8 encoded, no salt) to produce
    a deterministic anonymized ID.

    Args:
        username: The raw username string to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.
    """
    if not isinstance(username, str) or not username.strip():
        raise ValueError(f"Invalid username provided: {username}")
    
    return hashlib.sha256(username.encode('utf-8')).hexdigest()


def load_and_validate_loneliness_data(
    input_path: Path,
    required_fields: Tuple[str, ...] = ('username',)
) -> pd.DataFrame:
    """
    Load the loneliness dataset from a Parquet file and validate required fields.

    Args:
        input_path: Path to the input Parquet file.
        required_fields: Tuple of column names that must exist in the dataset.

    Returns:
        DataFrame containing the loaded and validated loneliness data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required fields are missing.
    """
    logger.info(f"Loading loneliness dataset from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows from loneliness dataset")
    
    # Validate required fields
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        raise ValueError(f"Missing required fields in loneliness dataset: {missing_fields}")
    
    # Validate non-empty usernames
    if 'username' in df.columns:
        invalid_count = df['username'].isna().sum() + (df['username'] == '').sum()
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} rows with invalid/empty usernames. Dropping them.")
            df = df.dropna(subset=['username'])
            df = df[df['username'].astype(str).str.strip() != '']
            logger.info(f"Remaining {len(df)} rows after cleaning")
    
    return df


def load_pushshift_data(
    input_path: Path,
    id_column: str = 'author_hash'
) -> pd.DataFrame:
    """
    Load Pushshift logs from a Parquet file.
    
    Note: In the actual pipeline, Pushshift data is fetched AFTER matching.
    This function is provided for testing and future integration when Pushshift
    data becomes available.

    Args:
        input_path: Path to the Pushshift logs Parquet file.
        id_column: Name of the column containing hashed author IDs.

    Returns:
        DataFrame containing the Pushshift logs.
    """
    logger.info(f"Loading Pushshift data from {input_path}")
    
    if not input_path.exists():
        # Return empty DataFrame with expected structure for testing
        logger.warning(f"Pushshift data file not found: {input_path}. Returning empty DataFrame.")
        return pd.DataFrame(columns=[id_column])
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows from Pushshift data")
    
    if id_column not in df.columns:
        raise ValueError(f"Pushshift data missing required column: {id_column}")
    
    return df


def perform_matching(
    loneliness_df: pd.DataFrame,
    pushshift_df: pd.DataFrame,
    loneliness_user_col: str = 'username',
    pushshift_id_col: str = 'author_hash'
) -> pd.DataFrame:
    """
    Perform matching between loneliness dataset and Pushshift logs.
    
    1. Hash usernames in the loneliness dataset to create anonymized IDs.
    2. Join with Pushshift logs on the hashed ID.
    3. Drop unmatched rows (users with no Pushshift logs).

    Args:
        loneliness_df: DataFrame containing the loneliness dataset.
        pushshift_df: DataFrame containing the Pushshift logs.
        loneliness_user_col: Column name for usernames in loneliness dataset.
        pushshift_id_col: Column name for hashed IDs in Pushshift data.

    Returns:
        DataFrame containing matched users with anonymized IDs.
    """
    logger.info(f"Starting matching process between {len(loneliness_df)} loneliness users and {len(pushshift_df)} Pushshift logs")
    
    # Create anonymized ID column in loneliness dataset
    loneliness_df = loneliness_df.copy()
    loneliness_df['user_id'] = loneliness_df[loneliness_user_col].apply(hash_username)
    
    logger.info(f"Created anonymized IDs for {len(loneliness_df)} users")
    
    # Perform inner join to keep only matched users
    if pushshift_df.empty:
        logger.warning("Pushshift data is empty. Returning empty matched dataset.")
        return pd.DataFrame(columns=['user_id', loneliness_user_col])
    
    matched_df = loneliness_df.merge(
        pushshift_df[[pushshift_id_col]].drop_duplicates(),
        left_on='user_id',
        right_on=pushshift_id_col,
        how='inner'
    )
    
    # Drop the duplicate column from Pushshift
    if pushshift_id_col in matched_df.columns and pushshift_id_col != 'user_id':
        matched_df = matched_df.drop(columns=[pushshift_id_col])
    
    # Keep only necessary columns
    matched_df = matched_df.drop(columns=[loneliness_user_col])
    
    logger.info(f"Matching complete: {len(matched_df)} users matched out of {len(loneliness_df)} total")
    
    return matched_df


def main():
    """
    Main entry point for the user matching pipeline.
    
    This function:
    1. Loads the loneliness dataset from data/raw/loneliness_dataset.parquet
    2. Loads Pushshift data (placeholder for now, will be filled by T013)
    3. Performs matching
    4. Saves the result to data/processed/matched_users.parquet
    """
    log_stage_start("User Matching")
    
    try:
        # Define paths
        base_dir = Path(__file__).resolve().parent.parent.parent
        loneliness_input = base_dir / "data" / "raw" / "loneliness_dataset.parquet"
        pushshift_input = base_dir / "data" / "processed" / "pushshift_logs_refined.parquet"
        output_path = base_dir / "data" / "processed" / "matched_users.parquet"
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load loneliness data
        loneliness_df = load_and_validate_loneliness_data(loneliness_input)
        
        # Load Pushshift data (will be populated by T013)
        # For now, we handle the case where it doesn't exist yet
        if pushshift_input.exists():
            pushshift_df = load_pushshift_data(pushshift_input)
        else:
            logger.warning(f"Pushshift data not yet available at {pushshift_input}. "
                         "This is expected if T013 has not run. "
                         "Creating empty matched dataset.")
            pushshift_df = pd.DataFrame(columns=['author_hash'])
        
        # Perform matching
        matched_df = perform_matching(loneliness_df, pushshift_df)
        
        # Save results
        matched_df.to_parquet(output_path, index=False)
        logger.info(f"Saved {len(matched_df)} matched users to {output_path}")
        
        # Log match statistics
        match_rate = len(matched_df) / len(loneliness_df) if len(loneliness_df) > 0 else 0.0
        logger.info(f"Match rate: {match_rate:.2%} ({len(matched_df)}/{len(loneliness_df)})")
        
        log_stage_end("User Matching", success=True)
        return matched_df
        
    except Exception as e:
        log_error_context("User Matching", e)
        raise
    
    finally:
        log_stage_end("User Matching", success=False)


if __name__ == "__main__":
    main()
