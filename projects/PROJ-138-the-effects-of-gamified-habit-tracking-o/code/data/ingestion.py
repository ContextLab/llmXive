"""
Data ingestion module for the habit tracking study.
Handles loading real data or generating synthetic data if real data is missing.
Validates schema and group sizes according to project requirements.
"""
import os
import sys
import pandas as pd
from code.utils.logging import pipeline_logger
from code.data.validation import check_consent, validate_schema
from code.data.synthetic_generator import generate_synthetic_data, OUTPUT_PATH as SYNTHETIC_PATH

# Constants
REAL_DATA_PATH = "data/raw/habitica_data.csv"
OUTPUT_PATH = "data/processed/ingested_data.csv"
MIN_TOTAL_RECORDS = 100
MIN_NON_GAMIFIED_USERS = 30

def load_data() -> pd.DataFrame:
    """
    Load data from real source or generate synthetic data.
    
    Returns:
        DataFrame with ingested data.
        
    Raises:
        ValueError: If data validation fails or insufficient data is found.
        FileNotFoundError: If real data path is specified but not found and synthetic generation fails.
    """
    # Step 1: Check consent
    pipeline_logger.info("Checking consent status...")
    check_consent()
    
    # Step 2: Try to load real data
    if os.path.exists(REAL_DATA_PATH):
        pipeline_logger.info(f"Loading real data from {REAL_DATA_PATH}")
        try:
            df = pd.read_csv(REAL_DATA_PATH)
            pipeline_logger.info(f"Successfully loaded {len(df)} records from real data")
        except Exception as e:
            pipeline_logger.error(f"Failed to load real data: {str(e)}")
            raise
    else:
        pipeline_logger.info(f"Real data not found at {REAL_DATA_PATH}. Generating synthetic data...")
        # Generate synthetic data with seed=42 as per task requirement
        df = generate_synthetic_data(seed=42)
        pipeline_logger.info(f"Generated {len(df)} synthetic records")
    
    # Step 3: Validate schema
    pipeline_logger.info("Validating data schema...")
    validate_schema(df)
    
    # Step 4: Validate gamified_app_usage tags (FR-001a)
    # Check that the column exists and contains only valid values (0 or 1)
    if "gamified_app_usage" not in df.columns:
        error_msg = "Missing required column 'gamified_app_usage'. Data does not comply with FR-001a."
        pipeline_logger.error(error_msg)
        raise ValueError(error_msg)
        
    valid_usage_values = {0, 1}
    invalid_values = set(df["gamified_app_usage"].unique()) - valid_usage_values
    if invalid_values:
        error_msg = f"Invalid values found in 'gamified_app_usage': {invalid_values}. Expected only 0 or 1 (FR-001a)."
        pipeline_logger.error(error_msg)
        raise ValueError(error_msg)
        
    pipeline_logger.info("gamified_app_usage validation passed (FR-001a)")
    
    # Step 5: Validate group sizes (FR-008)
    # Ensure non-gamified group size >= 30
    non_gamified_count = df[df["gamified_app_usage"] == 0]["user_id"].nunique()
    total_records = len(df)
    total_users = df["user_id"].nunique()
    
    pipeline_logger.info(f"Total records: {total_records}, Total users: {total_users}, Non-gamified users: {non_gamified_count}")
    
    if total_records < MIN_TOTAL_RECORDS:
        error_msg = f"Data Insufficiency: Total valid records ({total_records}) < {MIN_TOTAL_RECORDS}. Halting pipeline."
        pipeline_logger.error(error_msg)
        raise ValueError(error_msg)
        
    if non_gamified_count < MIN_NON_GAMIFIED_USERS:
        error_msg = f"Group Imbalance: Non-gamified group size ({non_gamified_count}) < {MIN_NON_GAMIFIED_USERS}. Halting pipeline."
        pipeline_logger.error(error_msg)
        raise ValueError(error_msg)
        
    pipeline_logger.info("Group size validation passed (FR-008)")
    
    return df

def validate_group_sizes(df: pd.DataFrame) -> bool:
    """
    Validate that the dataset meets minimum group size requirements.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        True if validation passes.
        
    Raises:
        ValueError: If validation fails.
    """
    non_gamified_count = df[df["gamified_app_usage"] == 0]["user_id"].nunique()
    total_records = len(df)
    
    if total_records < MIN_TOTAL_RECORDS:
        raise ValueError(f"Data Insufficiency: Total records ({total_records}) < {MIN_TOTAL_RECORDS}")
        
    if non_gamified_count < MIN_NON_GAMIFIED_USERS:
        raise ValueError(f"Group Imbalance: Non-gamified users ({non_gamified_count}) < {MIN_NON_GAMIFIED_USERS}")
        
    return True

def main():
    """Main entry point for data ingestion."""
    pipeline_logger.info("Starting data ingestion process...")
    
    try:
        # Load and validate data
        df = load_data()
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        
        # Save ingested data
        df.to_csv(OUTPUT_PATH, index=False)
        pipeline_logger.info(f"Ingested data saved to {OUTPUT_PATH}")
        
        # Log summary statistics
        pipeline_logger.info(f"Summary: {len(df)} records, {df['user_id'].nunique()} users")
        pipeline_logger.info(f"  - Gamified users: {df[df['gamified_app_usage'] == 1]['user_id'].nunique()}")
        pipeline_logger.info(f"  - Non-gamified users: {df[df['gamified_app_usage'] == 0]['user_id'].nunique()}")
        
    except Exception as e:
        pipeline_logger.error(f"Data ingestion failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()