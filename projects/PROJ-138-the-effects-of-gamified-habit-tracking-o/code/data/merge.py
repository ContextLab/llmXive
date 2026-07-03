import os
import pandas as pd
from code.utils.logging import pipeline_logger
from code.utils.config import set_random_seed

# Output path as specified in tasks.md
OUTPUT_PATH = "data/processed/merged_data.csv"

def merge_datasets():
    """
    Loads the aggregated data from T014 and merges it with user-level attributes
    (Gamified status, Conscientiousness, Need for Achievement) to produce the
    final processed dataset for analysis.

    Expected input from T013b/T014:
    - data/processed/weekly_aggregated.csv (contains User_ID, week_number, weekly_adherence_flag)
    
    Expected input from T013a (synthetic_generator):
    - data/raw/synthetic_data.csv (contains User_ID, gamified_status, conscientiousness_score, need_for_achievement)

    Output:
    - data/processed/merged_data.csv with columns:
      User_ID, Gamified, Adherence, Conscientiousness_Score, Need_for_Achievement
    """
    set_random_seed(42)
    
    # Define paths
    raw_data_path = "data/raw/synthetic_data.csv"
    agg_data_path = "data/processed/weekly_aggregated.csv"
    
    if not os.path.exists(raw_data_path):
        raise FileNotFoundError(f"Required input file not found: {raw_data_path}. Run T013a first.")
    
    if not os.path.exists(agg_data_path):
        raise FileNotFoundError(f"Required input file not found: {agg_data_path}. Run T014 first.")
    
    pipeline_logger.info(f"Loading raw user data from {raw_data_path}")
    raw_df = pd.read_csv(raw_data_path)
    
    pipeline_logger.info(f"Loading aggregated weekly data from {agg_data_path}")
    agg_df = pd.read_csv(agg_data_path)
    
    # Ensure column name consistency based on spec.md and T013a output
    # T013a generates: User_ID, gamified_status, conscientiousness_score, need_for_achievement
    # T014 generates: User_ID, week_number, weekly_adherence_flag
    
    # Rename columns to match the required output format for merged_data.csv
    # Target columns: User_ID, Gamified, Adherence, Personality Scores
    
    # Map raw user attributes
    user_df = raw_df[["User_ID", "gamified_status", "conscientiousness_score", "need_for_achievement"]].copy()
    user_df.rename(columns={
        "gamified_status": "Gamified",
        "conscientiousness_score": "Conscientiousness_Score",
        "need_for_achievement": "Need_for_Achievement"
    }, inplace=True)
    
    # Aggregate adherence: Calculate mean adherence per user across weeks
    # The task asks for "Adherence" (singular) in the merged CSV. 
    # We compute the mean weekly adherence rate per user to represent their overall adherence.
    user_agg = agg_df.groupby("User_ID").agg({
        "weekly_adherence_flag": "mean"
    }).reset_index()
    user_agg.rename(columns={"weekly_adherence_flag": "Adherence"}, inplace=True)
    
    # Merge user attributes with aggregated adherence
    merged_df = pd.merge(user_df, user_agg, on="User_ID", how="inner")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Save to disk
    merged_df.to_csv(OUTPUT_PATH, index=False)
    
    pipeline_logger.info(f"Merged dataset saved to {OUTPUT_PATH}")
    pipeline_logger.info(f"Final shape: {merged_df.shape}")
    pipeline_logger.info(f"Columns: {list(merged_df.columns)}")
    
    return merged_df

def main():
    """Entry point for the merge script."""
    try:
        merge_datasets()
        pipeline_logger.info("T017 Merge task completed successfully.")
    except Exception as e:
        pipeline_logger.error(f"T017 Merge task failed: {e}")
        raise

if __name__ == "__main__":
    main()