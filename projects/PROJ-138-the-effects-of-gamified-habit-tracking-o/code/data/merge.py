"""
Merges aggregated weekly data with user traits to produce the final processed dataset.
Implements Task T017.
"""
import os
import sys
import pandas as pd
import json
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("merge")

def merge_datasets(input_aggregated_path: str, input_traits_path: str, output_path: str) -> pd.DataFrame:
    """
    Merges the aggregated weekly adherence data with user trait data.
    
    Args:
        input_aggregated_path: Path to the aggregated weekly data CSV (output of T014).
        input_traits_path: Path to the user traits data CSV (output of synthetic generator/ingestion).
        output_path: Path where the merged CSV will be written.
        
    Returns:
        The merged DataFrame.
    """
    log_pipeline_stage(logger, "Starting merge operation")
    
    if not os.path.exists(input_aggregated_path):
        logger.error(f"Aggregated data file not found: {input_aggregated_path}")
        raise FileNotFoundError(f"Aggregated data file not found: {input_aggregated_path}")
    
    if not os.path.exists(input_traits_path):
        logger.error(f"Traits data file not found: {input_traits_path}")
        raise FileNotFoundError(f"Traits data file not found: {input_traits_path}")

    # Load datasets
    df_agg = pd.read_csv(input_aggregated_path)
    df_traits = pd.read_csv(input_traits_path)

    # Ensure User_ID types match for merging
    df_traits['User_ID'] = df_traits['User_ID'].astype(str)
    df_agg['user_id'] = df_agg['user_id'].astype(str)

    # Rename columns in df_traits to match the expected schema if necessary
    # Expected schema: User_ID, gamified_status, conscientiousness_score, [need_for_achievement], weekly_adherence_flag, week_number
    
    # Map traits columns: 
    # df_traits typically has: User_ID, gamified_status, conscientiousness_score, [need_for_achievement]
    # df_agg typically has: user_id, week_number, weekly_adherence_flag
    
    # Perform merge on user_id / User_ID
    merged_df = pd.merge(
        df_traits,
        df_agg,
        left_on='User_ID',
        right_on='user_id',
        how='inner'
    )

    # Select and order columns to match T017 requirements
    required_columns = ['User_ID', 'gamified_status', 'conscientiousness_score', 'weekly_adherence_flag', 'week_number']
    
    # Check for optional column
    if 'need_for_achievement' in df_traits.columns:
        required_columns.append('need_for_achievement')
        logger.info("Column 'need_for_achievement' included in merged dataset.")
    else:
        logger.info("Column 'need_for_achievement' omitted from merged dataset as it was not present in source.")

    # Filter to required columns only
    final_df = merged_df[required_columns]

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Write output
    final_df.to_csv(output_path, index=False)
    log_pipeline_stage(logger, f"Merge complete. Wrote {len(final_df)} rows to {output_path}")
    
    return final_df

def main():
    """
    Main entry point for the merge script.
    Reads from standard paths defined in the pipeline and writes to data/processed/merged_data.csv.
    """
    # Paths relative to project root
    # T014 output (aggregated) is expected at code/data/aggregated_weekly.csv based on typical pipeline flow
    # However, T013b/T013a-2 writes to data/raw/synthetic_data.csv
    # T014 (aggregation) reads from data/raw and writes to data/processed/aggregated_weekly.csv (assumed standard)
    
    # Let's infer paths based on T014 description: "Aggregate daily logs...". 
    # T013b writes to data/raw/synthetic_data.csv.
    # T014 should read from data/raw and write to data/processed/aggregated_weekly.csv.
    
    # Assuming T014 output is at: data/processed/aggregated_weekly.csv
    # Assuming T013b output (traits) is at: data/raw/synthetic_data.csv
    
    aggregated_path = "data/processed/aggregated_weekly.csv"
    traits_path = "data/raw/synthetic_data.csv"
    output_path = "data/processed/merged_data.csv"

    # If aggregated path doesn't exist, check if it's in code/data (sometimes paths vary)
    if not os.path.exists(aggregated_path):
        # Fallback for local testing if path structure differs slightly
        alt_path = "code/data/aggregated_weekly.csv"
        if os.path.exists(alt_path):
            aggregated_path = alt_path
        else:
            logger.error(f"Aggregated data not found at {aggregated_path} or {alt_path}")
            sys.exit(1)

    try:
        merge_datasets(aggregated_path, traits_path, output_path)
        logger.info("T017 Merge completed successfully.")
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()