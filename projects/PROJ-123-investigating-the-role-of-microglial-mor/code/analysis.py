import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from code.config import get_path
from code.logging_utils import get_logger

logger = get_logger(__name__)

def exclude_missing_cognitive_scores(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude subjects missing cognitive scores with log entry.
    """
    initial_count = len(dataset)
    # Assuming 'cognitive_score' is the target column name based on context
    if 'cognitive_score' not in dataset.columns:
        logger.warning("Column 'cognitive_score' not found in dataset. Skipping exclusion.")
        return dataset

    missing_mask = dataset['cognitive_score'].isna()
    if missing_mask.any():
        count = missing_mask.sum()
        logger.info(f"Excluding {count} subjects missing cognitive scores.")
        return dataset[~missing_mask].reset_index(drop=True)
    
    logger.info("No subjects missing cognitive scores.")
    return dataset

def load_morphological_metrics(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load morphological metrics from the processed CSV.
    """
    if filepath is None:
        filepath = get_path("data/processed/morphological_metrics.csv")
    
    if not pd.io.common.file_exists(filepath):
        raise FileNotFoundError(f"Morphological metrics file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df

def prepare_analysis_dataset(metrics_df: pd.DataFrame, metadata_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge morphological metrics with metadata for analysis.
    """
    # Ensure common keys exist for merging
    if 'subject_id' not in metrics_df.columns:
        raise ValueError("Metrics DataFrame missing 'subject_id' column.")
    if 'subject_id' not in metadata_df.columns:
        raise ValueError("Metadata DataFrame missing 'subject_id' column.")

    merged = pd.merge(metrics_df, metadata_df, on='subject_id', how='inner')
    logger.info(f"Prepared analysis dataset with {len(merged)} subjects.")
    return merged

def normalize_cognitive_scores_zscore(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Z-score normalize cognitive scores per cohort.
    Assumes a 'cohort' column exists for grouping.
    """
    if 'cognitive_score' not in dataset.columns:
        raise ValueError("Dataset missing 'cognitive_score' column for normalization.")
    if 'cohort' not in dataset.columns:
        logger.warning("No 'cohort' column found. Normalizing globally instead of per cohort.")
        dataset['cognitive_score_z'] = (dataset['cognitive_score'] - dataset['cognitive_score'].mean()) / dataset['cognitive_score'].std()
        return dataset

    def zscore_func(group):
        mean = group['cognitive_score'].mean()
        std = group['cognitive_score'].std()
        if std == 0:
            return pd.Series(0.0, index=group.index)
        return (group['cognitive_score'] - mean) / std

    dataset['cognitive_score_z'] = dataset.groupby('cohort').apply(zscore_func).reset_index(level=0, drop=True)
    logger.info("Z-score normalization completed per cohort.")
    return dataset

def classify_early_ad_dynamic(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Implement dynamic 'Early AD' classification logic (FR-010).
    
    Logic:
    1. If 'pathology_status' (or similar label column) is present and contains 'Early AD', 
       use existing labels directly.
    2. If labels are missing or not fully populated:
       a. Identify the 'control' group (e.g., pathology_status == 'Control').
       b. Calculate the 75th percentile of the amyloid-beta load for the control group.
       c. Classify subjects as 'Early AD' if their amyloid-beta load exceeds this threshold.
       d. Log the specific threshold used.
    
    Assumptions:
    - Column 'pathology_status' holds labels like 'Control', 'AD', 'Early AD'.
    - Column 'amyloid_beta_load' holds the numeric load values.
    """
    df = dataset.copy()
    
    # Determine if we have existing 'Early AD' labels
    has_early_ad_label = False
    if 'pathology_status' in df.columns:
        has_early_ad_label = df['pathology_status'].str.contains('Early AD', na=False).any()
    
    if has_early_ad_label:
        logger.info("Existing 'Early AD' labels detected. Using direct labels.")
        return df
    
    logger.warning("No 'Early AD' labels found. Calculating dynamic threshold.")
    
    if 'amyloid_beta_load' not in df.columns:
        raise ValueError("Cannot perform dynamic classification: 'amyloid_beta_load' column missing.")
    
    # Identify control group
    control_mask = df['pathology_status'] == 'Control'
    if not control_mask.any():
        # Fallback: if no explicit control label, assume lowest quartile or raise error?
        # Per spec, we need a control group to establish the baseline.
        raise ValueError("Cannot calculate dynamic threshold: No 'Control' group found in 'pathology_status'.")
    
    control_loads = df.loc[control_mask, 'amyloid_beta_load']
    if control_loads.empty:
        raise ValueError("Control group has no amyloid-beta load data.")
    
    threshold = control_loads.quantile(0.75)
    logger.info(f"Dynamic 'Early AD' threshold calculated (75th percentile of Control): {threshold:.4f}")
    
    # Apply classification
    # Logic: Classify 'Early AD' if amyloid-beta load > threshold
    # We will create a new column or update existing. Let's update 'pathology_status' 
    # for those who meet the criteria but aren't already labeled 'AD' or 'Early AD'.
    # To be safe and non-destructive to 'AD' labels, we only classify ambiguous or control-high cases.
    # However, the spec says "Classify 'Early AD' if...". 
    # We will create a derived status or update the column. Let's update the column for subjects 
    # that are currently 'Control' but exceed the threshold, or have no status.
    
    def classify_row(row):
        if row.get('pathology_status') in ['Early AD', 'AD']:
            return row['pathology_status']
        if pd.isna(row['amyloid_beta_load']):
            return row.get('pathology_status', 'Unknown')
        
        if row['amyloid_beta_load'] > threshold:
            return 'Early AD'
        return row.get('pathology_status', 'Unknown')

    df['pathology_status'] = df.apply(classify_row, axis=1)
    
    logger.info(f"Applied dynamic classification. New 'Early AD' count: {df['pathology_status'].str.contains('Early AD').sum()}")
    return df

def run_analysis_pipeline(metrics_path: str, metadata_path: str) -> pd.DataFrame:
    """
    Orchestrates the data preparation and classification steps.
    """
    metrics_df = load_morphological_metrics(metrics_path)
    # Assuming metadata is loaded separately or passed in. 
    # For this task, we focus on the classification logic which requires amyloid data.
    # We assume metadata contains amyloid_beta_load and pathology_status.
    if not pd.io.common.file_exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    metadata_df = pd.read_csv(metadata_path)
    
    dataset = prepare_analysis_dataset(metrics_df, metadata_df)
    dataset = exclude_missing_cognitive_scores(dataset)
    dataset = classify_early_ad_dynamic(dataset)
    dataset = normalize_cognitive_scores_zscore(dataset)
    
    return dataset