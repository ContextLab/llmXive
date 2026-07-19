"""
Main analysis pipeline orchestrator.
Implements the flow: Validate -> Clean -> ANOVA -> Report.

Per Spec FR-002 (Amended by T035a) and Constitution Principle VII, 
Repeated Measures ANOVA is used for all metrics. Shapiro-Wilk is run 
for logging only; Levene's test is omitted as inappropriate for paired designs.
"""
import sys
import argparse
import json
import os
from pathlib import Path
import pandas as pd
from utils.logger import get_logger
from analysis.stat_utils import generate_metrics_summary, verify_primary_anova_pvalue
from analysis.data_cleaner import DataCleaner
from analysis.report_generator import ReportGenerator

logger = get_logger(__name__)

def validate_columns(df: pd.DataFrame, required_cols: list) -> bool:
    """
    Validate that the DataFrame contains the required columns with correct types and ranges.
    
    Enforces exact column names:
    - participant_id (str)
    - interface_type (enum: traditional|explainable)
    - completion_time_seconds (float >= 0)
    - error_count (int >= 0)
    - sus_score (int 0-100)
    - explanation_engagement_time_seconds (float >= 0)
    
    Returns False and logs errors on mismatch.
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    
    errors = []
    
    # Validate participant_id (str)
    if 'participant_id' in df.columns:
        if not df['participant_id'].apply(lambda x: isinstance(x, str)).all():
            errors.append("participant_id must be of type string")
    
    # Validate interface_type (enum: traditional|explainable)
    if 'interface_type' in df.columns:
        valid_types = {'traditional', 'explainable'}
        invalid_mask = ~df['interface_type'].isin(valid_types)
        if invalid_mask.any():
            invalid_values = df.loc[invalid_mask, 'interface_type'].unique()
            errors.append(f"interface_type must be one of {list(valid_types)}, found: {invalid_values}")
    
    # Validate completion_time_seconds (float >= 0)
    if 'completion_time_seconds' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['completion_time_seconds']):
            errors.append("completion_time_seconds must be numeric (float)")
        elif (df['completion_time_seconds'] < 0).any():
            errors.append("completion_time_seconds cannot be negative")
    
    # Validate error_count (int >= 0)
    if 'error_count' in df.columns:
        if not pd.api.types.is_integer_dtype(df['error_count']) and not pd.api.types.is_numeric_dtype(df['error_count']):
            errors.append("error_count must be integer")
        elif (df['error_count'] < 0).any():
            errors.append("error_count cannot be negative")
    
    # Validate sus_score (int 0-100)
    if 'sus_score' in df.columns:
        if not pd.api.types.is_integer_dtype(df['sus_score']) and not pd.api.types.is_numeric_dtype(df['sus_score']):
            errors.append("sus_score must be integer")
        elif (df['sus_score'] < 0).any() or (df['sus_score'] > 100).any():
            errors.append("sus_score must be between 0 and 100")
    
    # Validate explanation_engagement_time_seconds (float >= 0)
    if 'explanation_engagement_time_seconds' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['explanation_engagement_time_seconds']):
            errors.append("explanation_engagement_time_seconds must be numeric (float)")
        elif (df['explanation_engagement_time_seconds'] < 0).any():
            errors.append("explanation_engagement_time_seconds cannot be negative")
    
    if errors:
        for err in errors:
            logger.error(err)
        return False
        
    return True

def run_analysis_pipeline(input_path: str, output_dir: str):
    """
    Orchestrates the full analysis pipeline.
    1. Loads and validates cleaned data.
    2. Runs ANOVA and generates metrics_summary.csv.
    3. Generates report.
    """
    logger.info(f"Starting analysis pipeline. Input: {input_path}, Output Dir: {output_dir}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load Data
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        return False

    # 2. Validate
    required_cols = [
        'participant_id', 'interface_type', 'completion_time_seconds',
        'error_count', 'sus_score', 'explanation_engagement_time_seconds'
    ]
    if not validate_columns(df, required_cols):
        logger.error("Data validation failed. Aborting pipeline.")
        return False

    # 3. Run ANOVA (T023a)
    metrics_summary_path = os.path.join(output_dir, 'metrics_summary.csv')
    metrics = ['completion_time_seconds', 'error_count', 'sus_score']
    
    try:
        generate_metrics_summary(df, metrics_summary_path, metrics=metrics)
        logger.info("ANOVA pipeline completed successfully.")
    except Exception as e:
        logger.error(f"ANOVA pipeline failed: {e}")
        return False

    # 4. Verify Primary P-value (T024a)
    verification_path = os.path.join(output_dir, 'primary_test_verification.txt')
    try:
        summary_df = pd.read_csv(metrics_summary_path)
        # Check if any primary metric (e.g., completion_time) has p < 0.05
        completion_row = summary_df[summary_df['metric_name'] == 'completion_time_seconds']
        if not completion_row.empty:
            p_val = completion_row['p_value'].values[0]
            is_sig = verify_primary_anova_pvalue(p_val)
            with open(verification_path, 'w') as f:
                f.write(f"Primary Test (Completion Time) p-value: {p_val}\n")
                f.write(f"Significant (p < 0.05): {is_sig}\n")
            logger.info(f"Primary test verification written to {verification_path}")
        else:
            logger.warning("Completion time metric not found in summary.")
    except Exception as e:
        logger.error(f"Failed to verify primary p-value: {e}")
        return False

    # 5. Generate Report
    report_path = os.path.join(output_dir, 'report_summary.txt')
    try:
        generator = ReportGenerator()
        generator.generate_report(summary_path=metrics_summary_path, output_path=report_path)
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return False

    logger.info("Analysis pipeline completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to cleaned_sessions.csv")
    parser.add_argument("--output", type=str, required=True, help="Output directory for artifacts")
    args = parser.parse_args()

    success = run_analysis_pipeline(args.input, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()