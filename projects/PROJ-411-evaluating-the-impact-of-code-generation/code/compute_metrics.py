"""
compute_metrics.py

Phase 2 script: Computes reviewer-effort metrics from classified pull requests.
Writes the Single Source of Truth (SSoT) dataset: data/processed/processed_prs.csv.

Metrics:
- review_duration_seconds: merged_at - created_at
- review_active_seconds: merged_at - first_comment_timestamp (fallback to duration)
- comment_density: comment_count / lines_changed
- issue_severity: mapped from labels to {bug, enhancement, documentation, other}
- severity_score: numeric mapping of severity
- creation_period: calendar quarter of created_at
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Severity mapping configuration
SEVERITY_KEYWORDS = {
    "bug": ["bug", "fix", "critical", "error", "issue"],
    "enhancement": ["enhancement", "feature", "improve", "add", "new"],
    "documentation": ["docs", "documentation", "readme", "wiki"],
}

SEVERITY_SCORE_MAP = {
    "bug": 3,
    "enhancement": 2,
    "documentation": 1,
    "other": 0
}

def map_severity(labels_val) -> str:
    """Maps PR labels to a categorical severity level (FR-012)."""
    if pd.isna(labels_val) or not labels_val:
        return "other"
    
    text = str(labels_val).lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return severity
    return "other"

def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Performs the metric computations required for the SSoT."""
    # 1. Timestamp conversion
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    df['merged_at'] = pd.to_datetime(df['merged_at'], errors='coerce')
    
    # Check for first_comment_timestamp (FR-016)
    has_first_comment = 'first_comment_timestamp' in df.columns
    if has_first_comment:
        df['first_comment_timestamp'] = pd.to_datetime(df['first_comment_timestamp'], errors='coerce')
    else:
        log.warning("Field 'first_comment_timestamp' is absent. review_active_seconds will fall back to review_duration_seconds (FR-015/FR-016).")

    # 2. Review Durations
    # review_duration_seconds (creation -> merge)
    df['review_duration_seconds'] = (df['merged_at'] - df['created_at']).dt.total_seconds()
    
    # review_active_seconds (first comment -> merge)
    if has_first_comment:
        df['review_active_seconds'] = (df['merged_at'] - df['first_comment_timestamp']).dt.total_seconds()
        # Fallback where first_comment_timestamp is NaN
        df['review_active_seconds'] = df['review_active_seconds'].fillna(df['review_duration_seconds'])
    else:
        df['review_active_seconds'] = df['review_duration_seconds']

    # 3. Code and Comment Metrics
    df['lines_changed'] = df['additions'].fillna(0).astype(int) + df['deletions'].fillna(0).astype(int)
    
    # comment_density = comments / lines (handle division by zero)
    df['comment_density'] = np.where(
        df['lines_changed'] > 0,
        df['comment_count'].fillna(0) / df['lines_changed'],
        0.0
    )

    # 4. Severity Mapping (FR-012)
    # Using 'issue_label_ids' as the source for labels
    label_col = 'issue_label_ids' if 'issue_label_ids' in df.columns else None
    if label_col:
        df['issue_severity'] = df[label_col].apply(map_severity)
    else:
        log.warning("Label column 'issue_label_ids' not found. Setting all severity to 'other'.")
        df['issue_severity'] = "other"
    
    df['severity_score'] = df['issue_severity'].map(SEVERITY_SCORE_MAP)

    # 5. Temporal Covariate
    # creation_period (calendar quarter)
    df['creation_period'] = df['created_at'].dt.to_period('Q').astype(str)

    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        # If the previous step failed to produce the file, this script should fail loudly.
        raise FileNotFoundError(f"Input file {input_path} not found. Ensure classify_provenance.py ran successfully.")

    log.info(f"Loading classified PRs from {input_path}")
    df = pd.read_csv(input_path)

    if df.empty:
        log.error("Input dataset is empty. Cannot compute metrics.")
        # Create an empty file with correct headers to avoid breaking downstream scripts, 
        # but the analysis will effectively be empty.
        # However, per constraints, we should fail loudly if we can't produce results.
        raise RuntimeError("Input dataset is empty.")

    log.info("Computing review metrics...")
    processed_df = compute_metrics(df)

    # Define the SSoT columns based on processed_prs.schema.yaml
    # Plus the extra quantitative columns requested by the task
    ssot_columns = [
        "pr_id", 
        "repo_name", 
        "lines_changed", 
        "comment_count", 
        "review_active_seconds", 
        "comment_density", 
        "issue_severity", 
        "provenance_label",
        "severity_score",
        "creation_period",
        "review_duration_seconds"
    ]
    
    # Ensure all required columns exist (fill with NaN if missing for some reason)
    for col in ssot_columns:
        if col not in processed_df.columns:
            processed_df[col] = np.nan

    final_df = processed_df[ssot_columns].copy()
    
    # Cast types to match schema
    final_df['pr_id'] = final_df['pr_id'].fillna(0).astype(int)
    final_df['lines_changed'] = final_df['lines_changed'].fillna(0).astype(int)
    final_df['comment_count'] = final_df['comment_count'].fillna(0).astype(int)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    log.info(f"SSoT processed dataset saved to {output_path}")

if __name__ == "__main__":
    main()
