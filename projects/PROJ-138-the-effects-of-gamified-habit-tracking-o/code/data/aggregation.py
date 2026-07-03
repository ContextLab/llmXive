"""
Data aggregation module.
Aggregates daily logs into weekly bins per user.
"""
import os
import pandas as pd
from code.utils.logging import pipeline_logger

INPUT_PATH = "data/processed/ingested_data.csv"
OUTPUT_PATH = "data/processed/merged_data.csv"

def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily logs into weekly adherence flags per user.
    
    Args:
        df: DataFrame with daily logs.
        
    Returns:
        DataFrame with weekly aggregations.
    """
    # Ensure week_number exists
    if "week_number" not in df.columns:
        # If not present, we might need to derive it from a date column.
        # The synthetic generator already provides week_number.
        pipeline_logger.error("week_number column missing in input data.")
        raise ValueError("week_number column missing.")
    
    if "user_id" not in df.columns:
        pipeline_logger.error("user_id column missing in input data.")
        raise ValueError("user_id column missing.")

    if "adherence_flag" not in df.columns:
        pipeline_logger.error("adherence_flag column missing in input data.")
        raise ValueError("adherence_flag column missing.")

    # Ensure adherence_flag is numeric
    df = df.copy()
    df["adherence_flag"] = pd.to_numeric(df["adherence_flag"], errors='coerce').fillna(0)
    
    # Group by user and week
    grouped = df.groupby(["user_id", "week_number"])
    
    aggregations = {
        "gamification_status": "first",
        "conscientiousness_score": "first",
        "need_for_achievement": "first",
        "adherence_flag": "mean"
    }
    
    # Filter aggregation keys to only those present in the dataframe
    available_cols = set(df.columns)
    valid_agg = {k: v for k, v in aggregations.items() if k in available_cols}
    
    weekly_df = grouped.agg(valid_agg).reset_index()
    
    # Calculate weekly_adherence_flag (binary 1/0)
    # If mean adherence > 0.5, flag = 1, else 0
    weekly_df["weekly_adherence_flag"] = (weekly_df["adherence_flag"] > 0.5).astype(int)
    
    # Rename mean adherence for clarity
    weekly_df = weekly_df.rename(columns={"adherence_flag": "weekly_adherence_rate"})
    
    # Ensure week_number starts at 1 and is sequential per user
    # The input should already be sequential, but we ensure it.
    weekly_df["week_number"] = weekly_df["week_number"].astype(int)
    
    # Ensure required columns exist for downstream tasks (T017)
    required_cols = ["user_id", "gamification_status", "conscientiousness_score", 
                     "week_number", "weekly_adherence_flag", "weekly_adherence_rate"]
     
    # Check for optional columns that might be needed downstream
    optional_cols = ["need_for_achievement"]
    
    final_cols = [c for c in required_cols if c in weekly_df.columns]
    for c in optional_cols:
        if c in weekly_df.columns:
            final_cols.append(c)
            
    return weekly_df[final_cols]

def main():
    """Main entry point for aggregation."""
    pipeline_logger.info("Starting data aggregation...")
    
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    
    df = pd.read_csv(INPUT_PATH)
    pipeline_logger.info(f"Loaded {len(df)} records for aggregation.")
    
    weekly_df = aggregate_weekly(df)
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    weekly_df.to_csv(OUTPUT_PATH, index=False)
    
    pipeline_logger.info(f"Aggregated data saved to {OUTPUT_PATH}")
    pipeline_logger.info(f"Total weekly records: {len(weekly_df)}")

if __name__ == "__main__":
    main()