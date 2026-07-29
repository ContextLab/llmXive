import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("aggregation")

def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily logs into weekly bins.
    
    Args:
        df: DataFrame with columns: User_ID, date, event_type, week_number, gamified_status, conscientiousness_score, need_for_achievement
        
    Returns:
        DataFrame with weekly aggregations
    """
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Ensure week_number is integer
    if 'week_number' not in df.columns:
        # Calculate week number from date
        # Assuming data starts from a known base date
        min_date = df['date'].min()
        df['week_number'] = ((df['date'] - min_date).dt.days // 7) + 1
    
    # Group by user and week
    weekly_agg = df.groupby(['User_ID', 'week_number']).agg({
        'event_type': 'count',
        'gamified_status': 'first',
        'conscientiousness_score': 'first',
        'need_for_achievement': 'first' if 'need_for_achievement' in df.columns else None
    }).reset_index()
    
    # Rename columns
    weekly_agg = weekly_agg.rename(columns={'event_type': 'daily_event_count'})
    
    # Calculate weekly adherence flag (1 if any adherence event, 0 otherwise)
    # For simplicity, we assume any event is an adherence event
    weekly_agg['weekly_adherence_flag'] = (weekly_agg['daily_event_count'] > 0).astype(int)
    
    # Sort by user and week
    weekly_agg = weekly_agg.sort_values(['User_ID', 'week_number'])
    
    return weekly_agg

def main():
    parser = argparse.ArgumentParser(description="Aggregate daily logs to weekly")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Data Aggregation")
    
    try:
        # Load raw data
        input_path = "data/raw/synthetic_data.csv"
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records for aggregation")
        
        # Aggregate
        weekly_df = aggregate_weekly(df)
        
        # Save output
        output_path = "data/processed/merged_data.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        weekly_df.to_csv(output_path, index=False)
        logger.info(f"Written aggregated data to {output_path}")
        
        log_pipeline_stage(logger, "SUCCESS", "Data Aggregation Complete")
        return 0
        
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
  import argparse
  sys.exit(main())
