"""
Data aggregation module.
Aggregates daily logs into weekly bins.
"""
import os
import sys
import pandas as pd
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("aggregation")

def aggregate_weekly(df: pd.DataFrame):
    """
    Aggregate daily logs into weekly bins.
    
    Args:
        df: DataFrame with 'User_ID', 'date', 'gamified_status', etc.
    
    Returns:
        DataFrame with weekly aggregations
    """
    df['date'] = pd.to_datetime(df['date'])
    df['week_number'] = df['date'].dt.isocalendar().week
    
    # Adjust week_number to be sequential from 1 within each user's data
    # Or use global week numbers. Let's use global week numbers relative to start.
    min_date = df['date'].min()
    df['week_number'] = ((df['date'] - min_date) / pd.Timedelta(weeks=1)).astype(int) + 1
    
    # Aggregate per user per week
    agg_df = df.groupby(['User_ID', 'week_number']).agg(
        total_events=('event_type', 'count'),
        adherence_count=('event_type', 'count'),
        gamified_status=('gamified_status', 'first'),
        conscientiousness_score=('conscientiousness_score', 'first'),
        need_for_achievement=('need_for_achievement', 'first')
    ).reset_index()
    
    # Binary adherence flag: 1 if any events, 0 otherwise
    agg_df['weekly_adherence_flag'] = (agg_df['adherence_count'] > 0).astype(int)
    
    return agg_df

def main():
    """CLI entry point."""
    log_pipeline_stage(logger, "START", "Data Aggregation")
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(root, "data", "raw", "habitica_data.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    agg_df = aggregate_weekly(df)
    
    output_path = os.path.join(root, "data", "processed", "weekly_aggregated.csv")
    agg_df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated data to {output_path}")
    
    log_pipeline_stage(logger, "END", "Data Aggregation")

if __name__ == "__main__":
    main()
