import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_METADATA = PROJECT_ROOT / "data" / "metadata"
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure output directory exists
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def load_features():
    """Load the processed features CSV."""
    features_path = DATA_PROCESSED / "features.csv"
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found at {features_path}. "
                                "Please ensure T022 has been completed successfully.")
    df = pd.read_csv(features_path)
    logger.info(f"Loaded features from {features_path}. Shape: {df.shape}")
    return df

def load_subject_labels():
    """Load the subject labels mapping CSV."""
    labels_path = DATA_METADATA / "subject_labels.csv"
    if not labels_path.exists():
        raise FileNotFoundError(f"Subject labels file not found at {labels_path}. "
                                "Please ensure T015 has been completed successfully.")
    df = pd.read_csv(labels_path)
    logger.info(f"Loaded subject labels from {labels_path}.")
    return df

def load_subject_status():
    """Load the subject status CSV to check for exclusions."""
    status_path = DATA_METADATA / "subject_status.csv"
    if not status_path.exists():
        logger.warning(f"Subject status file not found at {status_path}. "
                       "Assuming no exclusions.")
        return None
    df = pd.read_csv(status_path)
    logger.info(f"Loaded subject status from {status_path}.")
    return df

def compute_summary_statistics(features_df, labels_df, status_df=None):
    """
    Compute mean and std per metric, stratified by diagnostic group.
    
    Args:
        features_df: DataFrame with subject data and metrics.
        labels_df: DataFrame with subject_id and diagnostic_label.
        status_df: DataFrame with subject_id and exclusion status (optional).
    
    Returns:
        dict: Nested dictionary of statistics per group per metric.
        pd.DataFrame: Merged DataFrame for reporting.
    """
    # Merge features with labels
    if 'subject_id' not in features_df.columns or 'subject_id' not in labels_df.columns:
        raise ValueError("Both features and labels DataFrames must contain 'subject_id'.")
    
    merged_df = pd.merge(features_df, labels_df, on='subject_id', how='inner')
    
    # Filter out excluded subjects if status_df is provided
    if status_df is not None:
        if 'excluded' in status_df.columns:
            excluded_subjects = status_df[status_df['excluded'] == True]['subject_id'].tolist()
            merged_df = merged_df[~merged_df['subject_id'].isin(excluded_subjects)]
            logger.info(f"Filtered out {len(excluded_subjects)} excluded subjects.")
        elif 'status' in status_df.columns:
            # Assuming 'status' column indicates inclusion/exclusion logic
            included_subjects = status_df[status_df['status'] == 'included']['subject_id'].tolist()
            merged_df = merged_df[merged_df['subject_id'].isin(included_subjects)]
            logger.info(f"Filtered to {len(included_subjects)} included subjects.")

    if merged_df.empty:
        raise ValueError("No valid subjects found after filtering. Check data integrity.")

    # Identify metric columns (exclude subject_id and diagnostic_label)
    metric_cols = [col for col in merged_df.columns 
                   if col not in ['subject_id', 'diagnostic_label']]
    
    if not metric_cols:
        raise ValueError("No metric columns found in features DataFrame.")

    # Group by diagnostic_label and compute stats
    stats_dict = {}
    report_rows = []

    for label, group in merged_df.groupby('diagnostic_label'):
        stats_dict[label] = {}
        for col in metric_cols:
            mean_val = group[col].mean()
            std_val = group[col].std()
            count = group[col].count()
            stats_dict[label][col] = {
                'mean': mean_val,
                'std': std_val,
                'count': count
            }
            report_rows.append({
                'Group': label,
                'Metric': col,
                'Mean': mean_val,
                'Std': std_val,
                'Count': count
            })
    
    report_df = pd.DataFrame(report_rows)
    return stats_dict, report_df

def generate_markdown_report(stats_dict, report_df, output_path):
    """
    Generate a Markdown report with summary statistics.
    
    Args:
        stats_dict: Nested dictionary of statistics.
        report_df: DataFrame with report rows.
        output_path: Path to save the Markdown file.
    """
    lines = []
    lines.append("# Summary Statistics Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("This report presents the mean and standard deviation of graph metrics, ")
    lines.append("stratified by diagnostic group (e.g., Schizophrenia vs. Control).")
    lines.append("")
    
    # Total subjects per group
    lines.append("### Sample Size")
    lines.append("")
    lines.append("| Group | N |")
    lines.append("|-------|---|")
    for group in report_df['Group'].unique():
        n = report_df[report_df['Group'] == group]['Count'].iloc[0]
        lines.append(f"| {group} | {n} |")
    lines.append("")
    
    # Detailed statistics table
    lines.append("### Metric Statistics by Group")
    lines.append("")
    lines.append("| Group | Metric | Mean | Std | N |")
    lines.append("|-------|--------|------|-----|---|")
    
    for _, row in report_df.iterrows():
        lines.append(f"| {row['Group']} | {row['Metric']} | {row['Mean']:.4f} | {row['Std']:.4f} | {row['Count']} |")
    
    lines.append("")
    lines.append("---")
    lines.append("*Generated by llmXive pipeline (Task T023)*")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Report saved to {output_path}")

def main():
    """Main entry point for the summary statistics generation."""
    try:
        logger.info("Starting summary statistics generation (T023)...")
        
        # Load data
        features_df = load_features()
        labels_df = load_subject_labels()
        status_df = load_subject_status()
        
        # Compute statistics
        stats_dict, report_df = compute_summary_statistics(features_df, labels_df, status_df)
        
        # Generate report
        output_path = DOCS_DIR / "summary_statistics.md"
        generate_markdown_report(stats_dict, report_df, output_path)
        
        logger.info("Task T023 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()