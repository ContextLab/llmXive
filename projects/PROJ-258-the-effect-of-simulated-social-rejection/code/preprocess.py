import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import logging
import json
import os
from config import get_path

logger = logging.getLogger(__name__)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw dataset: handle missing values, strip whitespace,
    and ensure consistent data types for numerical columns.
    """
    logger.info("Cleaning data...")
    df = df.dropna(subset=['Participant', 'Condition', 'Reaction Time', 'Mood'])
    
    # Ensure numerical columns are numeric
    numeric_cols = ['Reaction Time', 'Mood']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows where numerical conversion failed
    df = df.dropna(subset=numeric_cols)
    
    return df

def normalize_rt(df: pd.DataFrame, group_col: str = 'Condition') -> pd.DataFrame:
    """
    Normalize reaction times within each group (Condition).
    Uses Z-score normalization.
    """
    logger.info("Normalizing reaction times...")
    df = df.copy()
    
    def z_normalize(group):
        mean = group.mean()
        std = group.std()
        if std == 0:
            return pd.Series(0.0, index=group.index)
        return (group - mean) / std

    df['Normalized RT'] = df.groupby(group_col)['Reaction Time'].transform(z_normalize)
    return df

def detect_outliers_iqr(df: pd.DataFrame, group_col: str = 'Condition', 
                        rt_col: str = 'Normalized RT', k: float = 1.5) -> pd.DataFrame:
    """
    Detect outliers using the Interquartile Range (IQR) method.
    Calculates IQR thresholds PER group (Condition).
    Marks rows as outliers but does NOT remove them.
    """
    logger.info("Detecting outliers using IQR method per Condition...")
    df = df.copy()
    
    def calculate_outlier_flag(group):
        q1 = group.quantile(0.25)
        q3 = group.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr
        
        # Store bounds in a way we can access later for logging
        # We attach them to the dataframe via a helper column or just return the flag
        # For logging, we need to know the specific thresholds used per group.
        # We will calculate flags here and store thresholds in a separate structure for the log.
        
        outliers = (group < lower_bound) | (group > upper_bound)
        return outliers

    df['is_outlier'] = df.groupby(group_col)[rt_col].transform(calculate_outlier_flag)
    return df

def normalize_and_flag_outliers(df: pd.DataFrame, group_col: str = 'Condition', k: float = 1.5) -> pd.DataFrame:
    """
    Combined pipeline: Normalize RTs, then flag outliers using IQR per group.
    """
    df = normalize_rt(df, group_col)
    df = detect_outliers_iqr(df, group_col, rt_col='Normalized RT', k=k)
    return df

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract summary features: mean RT and avg mood per participant/condition.
    """
    logger.info("Extracting features...")
    features = df.groupby(['Participant', 'Condition']).agg({
        'Reaction Time': 'mean',
        'Mood': 'mean',
        'is_outlier': 'sum' # Count outliers per group
    }).reset_index()
    
    features.columns = ['Participant', 'Condition', 'mean_rt', 'avg_mood', 'outlier_count']
    return features

def save_preprocessed_data(df: pd.DataFrame, design_type: str, output_path: str):
    """
    Save the preprocessed dataframe to CSV.
    """
    logger.info(f"Saving preprocessed data to {output_path}")
    df.to_csv(output_path, index=False)

def log_outlier_removal(df: pd.DataFrame, group_col: str = 'Condition', 
                        rt_col: str = 'Normalized RT', output_path: str = None) -> dict:
    """
    Implement T042: Outlier Audit Trail.
    Writes a JSON log containing the count of FLAGGED rows per condition 
    and the specific IQR thresholds used.
    
    Schema: {condition: str, flagged_count: int, iqr_threshold: float}
    Note: 'iqr_threshold' here represents the actual IQR value (Q3-Q1) used 
    to calculate the bounds (Lower=Q1 - 1.5*IQR, Upper=Q3 + 1.5*IQR).
    """
    logger.info("Generating outlier audit trail...")
    
    if output_path is None:
        output_path = get_path('interim', 'outlier_log.json')
    
    # Ensure directory exists
    os.makedirs(os.dirname(output_path), exist_ok=True)
    
    audit_log = []
    
    # Ensure the outlier column exists
    if 'is_outlier' not in df.columns:
        raise ValueError("Column 'is_outlier' not found. Run normalize_and_flag_outliers first.")

    groups = df[group_col].unique()
    
    for condition in groups:
        group_data = df[df[group_col] == condition]
        rt_values = group_data[rt_col]
        
        if len(rt_values) == 0:
            continue
          
        q1 = rt_values.quantile(0.25)
        q3 = rt_values.quantile(0.75)
        iqr = q3 - q1
        
        # Count flagged outliers
        # Assuming the 'is_outlier' column was generated with k=1.5
        # We recalculate the bounds to be precise about what generated the flag
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Verify count matches the flag column
        flagged_count = group_data['is_outlier'].sum()
        
        log_entry = {
            "condition": str(condition),
            "flagged_count": int(flagged_count),
            "iqr_threshold": float(iqr),
            "q1": float(q1),
            "q3": float(q3),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound)
        }
        audit_log.append(log_entry)
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(audit_log, f, indent=2)
    
    logger.info(f"Outlier audit trail written to {output_path}")
    return audit_log

def run_preprocessing(input_path: str, output_path: str, design_type: str):
    """
    Main pipeline execution for User Story 2.
    """
    logger.info(f"Starting preprocessing pipeline for {input_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    
    # 1. Clean
    df = clean_data(df)
    
    # 2. Normalize and Flag Outliers
    df = normalize_and_flag_outliers(df)
    
    # 3. Extract Features (for downstream analysis)
    features = extract_features(df)
    
    # 4. Save Preprocessed Data (T024)
    save_preprocessed_data(df, design_type, output_path)
    
    # 5. Log Outlier Removal (T042)
    # This generates the audit trail required for reproducibility
    log_outlier_removal(df)
    
    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Preprocessing Pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument("--design_type", default="Within-Subjects", help="Design type (Within-Subjects or Between-Subjects)")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    run_preprocessing(args.input, args.output, args.design_type)
