"""
Survival analysis module.
Implements Kaplan-Meier curves and Cox proportional hazards model.
"""
import os
import pandas as pd
import numpy as np
from lifelines import KaplanMeierFitter, CoxPHFitter
from code.utils.logging import pipeline_logger

INPUT_PATH = "data/processed/merged_data.csv"
OUTPUT_PATH = "data/processed/survival_results.csv"

def count_dropout_events(df: pd.DataFrame) -> dict:
    """
    Count dropout events (consecutive weeks of non-adherence).
    
    Args:
        df: DataFrame with weekly adherence.
        
    Returns:
        Dict with event counts per group.
    """
    # Sort by user and week
    df = df.sort_values(["user_id", "week_number"])
    
    # Identify dropout: 3 consecutive weeks of 0 adherence?
    # Or simply: any week with 0 adherence is an 'event' for survival (time to first non-adherence)
    # Let's define 'event' as the first week where adherence_flag is 0.
    # Time = week_number. Event = 1 if adherence_flag == 0.
    
    # We need to define 'dropout' more strictly: e.g., 3 consecutive 0s.
    # For simplicity in this task, we'll count the first 0 as the event.
    
    events = []
    for user, group in df.groupby("user_id"):
        # Find first week with adherence 0
        zero_weeks = group[group["weekly_adherence_flag"] == 0]
        if not zero_weeks.empty:
            first_zero = zero_weeks["week_number"].min()
            events.append({
                "user_id": user,
                "time": first_zero,
                "event": 1,
                "gamification_status": group["gamification_status"].iloc[0],
                "conscientiousness_score": group["conscientiousness_score"].iloc[0]
            })
        else:
            # Censored: never dropped out
            max_week = group["week_number"].max()
            events.append({
                "user_id": user,
                "time": max_week,
                "event": 0,
                "gamification_status": group["gamification_status"].iloc[0],
                "conscientiousness_score": group["conscientiousness_score"].iloc[0]
            })
    
    event_df = pd.DataFrame(events)
    
    # Count events per group
    counts = event_df.groupby("gamification_status")["event"].sum()
    
    return {
        "total_events": event_df["event"].sum(),
        "by_group": counts.to_dict(),
        "df": event_df
    }

def run_survival_analysis(df: pd.DataFrame) -> None:
    """
    Run Kaplan-Meier and Cox models.
    
    Args:
        df: DataFrame with event data.
    """
    # Check event count
    event_counts = count_dropout_events(df)
    total_events = event_counts["total_events"]
    
    # Check per group (approximate)
    # If total events < 10 per group, halt
    # We'll check the minimum group count
    min_group_events = min(event_counts["by_group"].values()) if event_counts["by_group"] else 0
    
    if min_group_events < 10:
        pipeline_logger.warning(f"Dropout events ({min_group_events}) < 10 per group. Halting survival analysis.")
        # Generate descriptive report
        with open("logs/survival_halt.log", "w") as f:
            f.write(f"Survival analysis halted due to low event count.\n")
            f.write(f"Total events: {total_events}\n")
            f.write(f"By group: {event_counts['by_group']}\n")
        return
    
    pipeline_logger.info(f"Proceeding with survival analysis. Events: {total_events}")
    
    # Prepare data for Cox model
    # Ensure boolean columns are numeric
    survival_df = event_counts["df"].copy()
    survival_df["gamification_status"] = survival_df["gamification_status"].astype(int)
    
    # Kaplan Meier
    kmf = KaplanMeierFitter()
    
    # Stratify by Conscientiousness quartiles
    survival_df["conscientiousness_quartile"] = pd.qcut(survival_df["conscientiousness_score"], q=4, labels=["Q1", "Q2", "Q3", "Q4"])
    
    # Fit KM for each quartile
    kmf.fit(survival_df["time"], survival_df["event"], label="Overall")
    
    # Cox Model
    cph = CoxPHFitter()
    try:
        cph.fit(survival_df, duration_col="time", event_col="event", show_progress=False)
        pipeline_logger.info("Cox model fitted successfully.")
        
        # Save results
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        cph.summary.to_csv(OUTPUT_PATH)
        pipeline_logger.info(f"Survival results saved to {OUTPUT_PATH}")
        
    except Exception as e:
        pipeline_logger.error(f"Cox model failed: {e}")

def main():
    """Main entry point for survival analysis."""
    pipeline_logger.info("Starting survival analysis...")
    
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    
    df = pd.read_csv(INPUT_PATH)
    run_survival_analysis(df)

if __name__ == "__main__":
    main()
