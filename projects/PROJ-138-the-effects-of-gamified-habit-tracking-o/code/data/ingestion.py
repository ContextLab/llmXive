"""
Data ingestion module.
Loads real data if available, otherwise generates synthetic data.
Validates schema and group sizes.
"""
import os
import sys
import pandas as pd
from code.utils.logging import pipeline_logger
from code.data.validation import check_consent, validate_schema
from code.data.synthetic_generator import generate_synthetic_data, OUTPUT_PATH as SYNTHETIC_PATH

REAL_DATA_PATH = "data/raw/habitica_data.csv"
OUTPUT_PATH = "data/processed/ingested_data.csv"

def load_data() -> pd.DataFrame:
    """
    Load data from real source or generate synthetic data.
    
    Returns:
        DataFrame with ingested data.
        
    Raises:
        FileNotFoundError: If real data is missing and synthetic generation fails.
        ValueError: If data validation fails.
    """
    # Step 1: Check Consent
    try:
        check_consent()
    except FileNotFoundError as e:
        pipeline_logger.error(f"Consent check failed: {str(e)}")
        raise

    # Step 2: Determine Source
    if os.path.exists(REAL_DATA_PATH):
        pipeline_logger.info(f"Loading real data from {REAL_DATA_PATH}")
        try:
            df = pd.read_csv(REAL_DATA_PATH)
            # Validate real data schema if needed, though we assume it matches spec
            # For now, we ensure required columns exist
            if "user_id" not in df.columns:
                raise ValueError("Missing 'user_id' column in real dataset.")
            if "adherence_flag" not in df.columns:
                raise ValueError("Missing 'adherence_flag' column in real dataset.")
        except Exception as e:
            pipeline_logger.error(f"Failed to load real data: {str(e)}")
            raise
    else:
        pipeline_logger.info(f"Real data not found at {REAL_DATA_PATH}. Generating synthetic data.")
        # Generate synthetic data
        # Ensure we always generate fresh to guarantee seed consistency for this run
        df = generate_synthetic_data(seed=42)
        os.makedirs(os.path.dirname(SYNTHETIC_PATH), exist_ok=True)
        df.to_csv(SYNTHETIC_PATH, index=False)
        pipeline_logger.info(f"Synthetic data saved to {SYNTHETIC_PATH}")
    
    pipeline_logger.info(f"Loaded {len(df)} records.")
    return df

def validate_group_sizes(df: pd.DataFrame) -> bool:
    """
    Validate that the non-gamified group size is >= 30 and total valid records >= 100.
    
    Args:
        df: DataFrame with 'gamification_status' column.
        
    Returns:
        True if valid, False otherwise.
    """
    if "gamification_status" not in df.columns:
        pipeline_logger.error("Data Insufficiency: Missing 'gamification_status' column.")
        return False

    # Count unique users per group based on their first recorded status
    user_groups = df.groupby("user_id")["gamification_status"].first()
    non_gamified_count = (user_groups == False).sum()
    total_users = len(user_groups)
    
    pipeline_logger.info(f"Total unique users: {total_users}")
    pipeline_logger.info(f"Non-gamified user count: {non_gamified_count}")

    # Check total valid records (users) >= 100
    if total_users < 100:
        pipeline_logger.error(f"Data Insufficiency: Total valid users ({total_users}) < 100.")
        return False

    # Check non-gamified group size >= 30
    if non_gamified_count < 30:
        pipeline_logger.error(f"Group Imbalance: Non-gamified group size ({non_gamified_count}) < 30.")
        return False

    pipeline_logger.info("Group size validation passed.")
    return True

def main():
    """Main entry point for data ingestion."""
    pipeline_logger.info("Starting data ingestion pipeline...")
    
    try:
        # Load data (real or synthetic)
        df = load_data()
        
        # Validate group sizes
        if not validate_group_sizes(df):
            raise ValueError("Data validation failed: Insufficient data or group imbalance.")
        
        # Save ingested data to processed directory
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df.to_csv(OUTPUT_PATH, index=False)
        pipeline_logger.info(f"Ingested data successfully saved to {OUTPUT_PATH}")
        
    except Exception as e:
        pipeline_logger.error(f"Ingestion pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()