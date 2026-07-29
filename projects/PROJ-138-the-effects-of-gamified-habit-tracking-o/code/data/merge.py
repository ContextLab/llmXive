"""
Merge aggregated weekly data with user traits to produce the final processed dataset.

This script implements Task T017: Generate merged CSV in `data/processed/merged_data.csv`
with all required columns.

Dependencies:
- code/data/aggregation.py (must have run to produce weekly aggregates)
- code/data/user_traits.py (must have run to produce user traits)
"""
import os
import sys
import pandas as pd
from code.utils.logging import setup_logger, log_pipeline_stage
from code.utils.config import set_random_seed

# Setup logger
logger = setup_logger("merge")

REQUIRED_COLUMNS = [
    'User_ID',
    'gamified_status',
    'conscientiousness_score',
    'weekly_adherence_flag',
    'week_number'
]

def merge_datasets():
    """
    Merge aggregated weekly data with user traits.
    
    Returns:
        pd.DataFrame: Merged dataset with required columns.
    """
    log_pipeline_stage(logger, "Starting merge of aggregated data and user traits")
    
    # Define paths
    aggregated_path = "data/processed/weekly_aggregates.csv"
    traits_path = "data/processed/user_traits.csv"
    
    # Check if input files exist
    if not os.path.exists(aggregated_path):
        logger.error(f"Aggregated data not found at {aggregated_path}. Run aggregation.py first.")
        raise FileNotFoundError(f"Missing aggregated data: {aggregated_path}")
    
    if not os.path.exists(traits_path):
        logger.error(f"User traits not found at {traits_path}. Run user_traits.py first.")
        raise FileNotFoundError(f"Missing user traits: {traits_path}")
    
    # Load data
    df_agg = pd.read_csv(aggregated_path)
    df_traits = pd.read_csv(traits_path)
    
    logger.info(f"Loaded {len(df_agg)} rows from aggregated data")
    logger.info(f"Loaded {len(df_traits)} rows from user traits")
    
    # Merge on User_ID
    merged_df = pd.merge(df_traits, df_agg, on='User_ID', how='inner')
    
    logger.info(f"Merged dataset has {len(merged_df)} rows")
    
    # Ensure required columns exist
    for col in REQUIRED_COLUMNS:
        if col not in merged_df.columns:
            logger.error(f"Required column '{col}' missing from merged dataset")
            raise ValueError(f"Missing required column: {col}")
    
    # Handle optional 'need_for_achievement' column
    if 'need_for_achievement' in merged_df.columns:
        logger.info("Column 'need_for_achievement' included in merged dataset")
        # Keep it in the output
        final_columns = REQUIRED_COLUMNS + ['need_for_achievement']
    else:
        logger.info("Column 'need_for_achievement' omitted from merged dataset as it was not present in source.")
        final_columns = REQUIRED_COLUMNS
    
    # Select and order columns
    result_df = merged_df[final_columns]
    
    return result_df

def main():
    """Main entry point for the merge script."""
    log_pipeline_stage(logger, "Starting merge process (Task T017)")
    
    try:
        # Ensure output directory exists
        output_dir = "data/processed"
        os.makedirs(output_dir, exist_ok=True)
        
        # Set random seed for reproducibility
        set_random_seed(42)
        
        # Perform merge
        merged_df = merge_datasets()
        
        # Write to output file
        output_path = os.path.join(output_dir, "merged_data.csv")
        merged_df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully wrote merged data to {output_path}")
        logger.info(f"Output columns: {list(merged_df.columns)}")
        
        # Verification
        assert os.path.exists(output_path), "Output file was not created"
        assert len(merged_df) > 0, "Output dataframe is empty"
        
        # Verify required columns
        for col in REQUIRED_COLUMNS:
            assert col in merged_df.columns, f"Missing required column: {col}"
        
        log_pipeline_stage(logger, "Merge process completed successfully")
        
    except Exception as e:
        logger.error(f"Merge process failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
