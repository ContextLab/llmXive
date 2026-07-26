"""
Data merging module.
Merges aggregated data with user traits for final analysis.
"""
import os
import sys
import pandas as pd
from code.utils.logging import setup_logger, log_pipeline_stage
from code.utils.config import set_random_seed

logger = setup_logger("merge")

def merge_datasets():
    """
    Merge weekly aggregated data with user traits.
    
    Returns:
        DataFrame with all required columns
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    agg_path = os.path.join(root, "data", "processed", "weekly_aggregated.csv")
    
    if not os.path.exists(agg_path):
        logger.error(f"Aggregated data not found: {agg_path}")
        sys.exit(1)
    
    agg_df = pd.read_csv(agg_path)
    
    # Calculate average adherence per user
    user_stats = agg_df.groupby('User_ID').agg(
        avg_adherence=('weekly_adherence_flag', 'mean'),
        total_weeks=('week_number', 'nunique'),
        gamified_status=('gamified_status', 'first'),
        conscientiousness_score=('conscientiousness_score', 'first'),
        need_for_achievement=('need_for_achievement', 'first')
    ).reset_index()
    
    # Rename for final output
    final_df = user_stats.rename(columns={
        'avg_adherence': 'Adherence',
        'gamified_status': 'Gamified',
        'conscientiousness_score': 'Conscientiousness',
        'need_for_achievement': 'Need_for_Achievement'
    })
    
    # Ensure types
    final_df['Gamified'] = final_df['Gamified'].astype(bool)
    final_df['Adherence'] = final_df['Adherence'].round(3)
    
    return final_df

def main():
    """CLI entry point."""
    log_pipeline_stage(logger, "START", "Data Merging")
    
    final_df = merge_datasets()
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(root, "data", "processed", "merged_data.csv")
    
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged data to {output_path}")
    logger.info(f"Total users: {len(final_df)}")
    
    log_pipeline_stage(logger, "END", "Data Merging")

if __name__ == "__main__":
    main()
