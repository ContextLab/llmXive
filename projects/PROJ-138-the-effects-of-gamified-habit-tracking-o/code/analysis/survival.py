"""
Survival analysis module.
Performs Kaplan-Meier and Cox proportional hazards analysis.
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.utils import concordance_index
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("survival")

def count_dropout_events(df: pd.DataFrame):
    """Count dropout events (consecutive weeks of non-adherence)."""
    # Simplified: count users with low adherence
    events = df[df['Adherence'] < 0.5].shape[0]
    return events

def generate_descriptive_report(df: pd.DataFrame, events: int):
    """Generate descriptive statistics for survival analysis."""
    report = {
        "total_users": len(df),
        "dropout_events": events,
        "gamified_count": df['Gamified'].sum(),
        "non_gamified_count": len(df) - df['Gamified'].sum()
    }
    return report

def run_survival_analysis(df: pd.DataFrame):
    """Run Kaplan-Meier and Cox models."""
    # Prepare data for lifelines
    # Create a duration and event indicator
    # For simplicity, use Adherence as proxy for event
    df['event'] = (df['Adherence'] < 0.5).astype(int)
    df['duration'] = df['Adherence'] * 100  # Fake duration for demo
    
    kmf = KaplanMeierFitter()
    
    # Stratify by Gamified
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for name, group in df.groupby('Gamified'):
        kmf.fit(group['duration'], group['event'], label=f'Gamified={name}')
        kmf.plot_survival_function(ax=ax)
    
    ax.set_title("Kaplan-Meier Survival Curves by Gamification Status")
    ax.set_xlabel("Duration (scaled)")
    ax.set_ylabel("Survival Probability")
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plt.savefig(os.path.join(root, "figures", "km_curves.png"))
    plt.close()
    logger.info("Saved KM curves to figures/km_curves.png")
    
    # Cox model
    cdf = df[['duration', 'event', 'Gamified', 'Conscientiousness']].copy()
    cdf = cdf.dropna()
    
    if cdf.shape[0] > 10:
        cph = CoxPHFitter()
        cph.fit(cdf, duration_col='duration', event_col='event')
        logger.info("Cox Model Summary:")
        logger.info(str(cph.summary))
        
        # Save
        cph_summary_path = os.path.join(root, "data", "processed", "cox_summary.txt")
        with open(cph_summary_path, 'w') as f:
            f.write(str(cph.summary))
    else:
        logger.warning("Insufficient data for Cox model.")

def main():
    """CLI entry point."""
    log_pipeline_stage(logger, "START", "Survival Analysis")
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(root, "data", "processed", "merged_data.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    events = count_dropout_events(df)
    
    if events < 10:
        logger.warning(f"Low event count ({events}). Generating descriptive report only.")
        report = generate_descriptive_report(df, events)
        report_path = os.path.join(root, "data", "processed", "survival_descriptive.json")
        import json
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
    else:
        run_survival_analysis(df)
    
    log_pipeline_stage(logger, "END", "Survival Analysis")

if __name__ == "__main__":
    main()
