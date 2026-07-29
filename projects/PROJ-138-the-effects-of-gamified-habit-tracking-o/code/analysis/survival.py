import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter, CoxPHFitter

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("survival")

def count_dropout_events(df: pd.DataFrame) -> int:
    """
    Count dropout events (consecutive weeks of non-adherence).
    
    Args:
        df: Aggregated data
        
    Returns:
        Number of dropout events
    """
    # Identify users with zero adherence weeks
    zero_adherence = df[df['weekly_adherence_flag'] == 0]
    # This is a simplified count; real implementation would track consecutive weeks
    return len(zero_adherence)

def generate_descriptive_report(df: pd.DataFrame, events: int):
    """Generate descriptive statistics if events < 10."""
    report = {
        "dropout_events": events,
        "total_users": df['User_ID'].nunique(),
        "message": "Insufficient events for survival analysis"
    }
    
    os.makedirs("data/reports", exist_ok=True)
    with open("data/reports/survival_descriptive_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info("Generated descriptive report for low event count.")

def run_survival_analysis(df: pd.DataFrame):
    """
    Run Kaplan-Meier and Cox proportional hazards models.
    
    Args:
        df: Aggregated data
    """
    # Prepare data for survival analysis
    # Create duration and event columns
    # Simplified: duration = weeks observed, event = dropout
    
    # Group by user
    user_stats = df.groupby('User_ID').agg({
        'weekly_adherence_flag': 'sum',
        'week_number': 'max'
    }).reset_index()
    
    user_stats.columns = ['User_ID', 'total_adherence', 'duration']
    user_stats['event'] = (user_stats['total_adherence'] == 0).astype(int)
    
    # Check event count
    events = user_stats['event'].sum()
    if events < 10:
        logger.warning(f"Too few events ({events}) for survival analysis.")
        generate_descriptive_report(df, events)
        return
    
    # Kaplan-Meier
    kmf = KaplanMeierFitter()
    
    # Stratify by gamification status
    for status, group in user_stats.groupby('gamified_status' if 'gamified_status' in df.columns else ['User_ID']):
        kmf.fit(group['duration'], event_observed=group['event'], label=f'Gamified={status}')
        kmf.plot()
    
    plt.title("Kaplan-Meier Survival Curve")
    plt.xlabel("Weeks")
    plt.ylabel("Survival Probability")
    
    output_fig = "figures/km_curve.png"
    os.makedirs(os.path.dirname(output_fig), exist_ok=True)
    plt.savefig(output_fig)
    plt.close()
    logger.info(f"Saved KM curve to {output_fig}")
    
    # Cox PH
    if 'conscientiousness_score' in df.columns:
        cdf = user_stats.copy()
        cdf['conscientiousness_score'] = df.groupby('User_ID')['conscientiousness_score'].first().values
        
        if 'gamified_status' in df.columns:
            cdf['gamified_status'] = df.groupby('User_ID')['gamified_status'].first().values
        
        cdf = cdf.dropna()
        
        cph = CoxPHFitter()
        cph.fit(cdf, duration_col='duration', event_col='event')
        cph.print_summary()
        
        # Save results
        results_path = "data/processed/survival_results.json"
        cph.summary.to_json(results_path)
        logger.info(f"Saved Cox results to {results_path}")

def main():
    parser = argparse.ArgumentParser(description="Run survival analysis")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Survival Analysis")
    
    try:
        # Load data
        input_path = "data/processed/merged_data.csv"
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records for survival analysis")
        
        # Count events
        events = count_dropout_events(df)
        logger.info(f"Dropout events: {events}")
        
        if events < 10:
            generate_descriptive_report(df, events)
        else:
            run_survival_analysis(df)
        
        log_pipeline_stage(logger, "SUCCESS", "Survival Analysis Complete")
        return 0
        
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
  import argparse
  sys.exit(main())
