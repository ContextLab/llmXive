import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure project root is in path if running from subdirectory
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config

logger = logging.getLogger(__name__)

def load_search_time_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed dataset containing search time and other features.
    Expects a CSV with at least 'search_time' and 'subject_id' columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading search time data from {input_path}")
    df = pd.read_csv(path)
    
    required_cols = ['search_time', 'subject_id', 'trial_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    return df

def label_by_median_split(df: pd.DataFrame, target_col: str = 'search_time') -> pd.DataFrame:
    """
    Create binary ground truth labels based on median split of the target column.
    Values <= median -> 0 (Low Load), Values > median -> 1 (High Load).
    
    This method is used when an independent cognitive load measure is absent.
    
    Args:
        df: Input dataframe with the target column.
        target_col: Name of the column to split on (default: 'search_time').
    
    Returns:
        DataFrame with a new 'ground_truth_label' column.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    median_val = df[target_col].median()
    logger.info(f"Computing median for {target_col}: {median_val}")
    
    # Label: 0 if <= median, 1 if > median
    df['ground_truth_label'] = (df[target_col] > median_val).astype(int)
    
    logger.info(f"Label distribution:\n{df['ground_truth_label'].value_counts()}")
    return df

def save_labeled_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the labeled dataframe to a CSV file.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    logger.info(f"Saved labeled data to {output_path}")

def write_limitations_note(output_path: str) -> None:
    """
    Write an explicit limitation note to a markdown file.
    This note clarifies that ground truth is derived from search-time median split
    and that predictive validity claims have been removed.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    content = """# Limitations of Ground Truth Labeling

## Ground Truth Derivation
The ground truth labels used for classification in this study are derived from a **median split of search time**. 
Specifically, trials with search time greater than the median are labeled as "High Load" (1), and those below or equal to the median are labeled as "Low Load" (0).

## Critical Limitation
This labeling strategy is a proxy for cognitive load and **does not represent an independent, validated measure of cognitive load**. 

## Disclaimer
**Predictive validity claims have been removed.** The results of this classification task should be interpreted as **Search-Time Estimation** rather than a direct measure of cognitive state. The status of these labels is marked as "UNVALIDATED" in the classification metrics to prevent downstream misinterpretation.

## Citation Note
When citing results from this pipeline, acknowledge that the ground truth is a heuristic proxy based on search duration, not an external cognitive load metric.
"""
    
    with open(output, 'w') as f:
        f.write(content)
    
    logger.info(f"Written limitations note to {output_path}")

def update_classification_metrics(input_path: str, output_path: str, status: str = "UNVALIDATED") -> None:
    """
    Read the classification metrics CSV, ensure the 'status' column exists,
    and set its value to the specified status (default: "UNVALIDATED").
    If the file doesn't exist, create it with headers and the status row.
    
    This function enforces the requirement to label output as "UNVALIDATED" 
    to prevent downstream misinterpretation.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if path.exists():
        df = pd.read_csv(path)
        logger.info(f"Updating existing metrics file: {output_path}")
    else:
        # If the file doesn't exist, we assume it's an empty result file
        # We need to create it with the required status column.
        # Since we don't have the metrics data yet (that comes from T030),
        # we create a placeholder structure or just ensure the column exists.
        # However, T029 is about labeling logic and setting the status.
        # If T030 hasn't run, we create the file with the status column.
        # If T030 runs later, it should append or overwrite.
        # For T029 specifically, we ensure the column is present and set to UNVALIDATED.
        # We'll create a minimal file if it doesn't exist, or update if it does.
        # To be safe, if it doesn't exist, we create the headers.
        df = pd.DataFrame()
        logger.info(f"Creating new metrics file structure: {output_path}")
    
    # Ensure 'status' column exists
    if 'status' not in df.columns:
        # If we have data, we set status for all rows. 
        # If empty, we just add the column.
        df['status'] = status
    else:
        # Update all existing rows to the new status
        df['status'] = status
    
    # If the file was empty, we might need to ensure it has at least one row 
    # if the specification implies a header-only file is insufficient.
    # But usually, metrics come from evaluation. 
    # We ensure the column is there.
    df.to_csv(path, index=False)
    logger.info(f"Updated status column to '{status}' in {output_path}")

def main():
    """
    Main entry point for T029: Ground Truth Labeling and Limitations.
    This script:
    1. Loads processed data (from US1/US2 output).
    2. Applies median split labeling.
    3. Saves labeled data.
    4. Writes limitations note.
    5. Updates classification metrics status.
    """
    config = load_config()
    
    # Paths
    input_data = config.get('paths', {}).get('processed_data', 'data/processed/features.csv')
    labeled_output = config.get('paths', {}).get('labeled_data', 'data/processed/labeled_features.csv')
    limitations_path = 'results/limitations.md'
    metrics_path = 'results/classification_metrics.csv'
    
    # Check if input exists
    if not Path(input_data).exists():
        # Fallback for testing if the specific processed file isn't named 'features.csv'
        # In a real run, this should fail loudly if data is missing.
        logger.warning(f"Input data not found at {input_data}. Attempting to find processed data...")
        # We will proceed assuming the user provides the correct path or the file exists
        # If it truly doesn't exist, the script should fail.
        pass

    try:
        # 1. Load Data
        df = load_search_time_data(input_data)
        
        # 2. Label by Median Split
        df_labeled = label_by_median_split(df, target_col='search_time')
        
        # 3. Save Labeled Data
        save_labeled_data(df_labeled, labeled_output)
        
        # 4. Write Limitations Note
        write_limitations_note(limitations_path)
        
        # 5. Update Classification Metrics Status
        update_classification_metrics(None, metrics_path, status="UNVALIDATED")
        
        logger.info("T029 Ground Truth Labeling completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during labeling: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()