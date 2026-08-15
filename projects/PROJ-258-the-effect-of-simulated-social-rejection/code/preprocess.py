import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import logging
import json
import os

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the data by removing rows with missing critical values.
    
    Args:
        df: Input dataframe
        
    Returns:
        Cleaned dataframe
    """
    # Remove rows with missing critical columns
    critical_columns = ['Condition', 'Reaction Time', 'Mood']
    df = df.dropna(subset=critical_columns)
    
    # Remove rows with negative reaction times
    df = df[df['Reaction Time'] >= 0]
    
    return df.reset_index(drop=True)

def normalize_rt(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize reaction times within each condition.
    
    Args:
        df: Input dataframe
        
    Returns:
        DataFrame with normalized reaction times
    """
    df = df.copy()
    
    def z_score_normalize(group):
        rt = group['Reaction Time']
        mean_rt = rt.mean()
        std_rt = rt.std()
        if std_rt > 0:
            group['RT_normalized'] = (rt - mean_rt) / std_rt
        else:
            group['RT_normalized'] = 0
        return group
    
    df = df.groupby('Condition', group_keys=False).apply(z_score_normalize)
    return df

def detect_outliers_iqr(df: pd.DataFrame, group_col: str = 'Condition', multiplier: float = 1.5) -> pd.DataFrame:
    """
    Detect outliers using the IQR method per condition group.
    
    Args:
        df: Input dataframe
        group_col: Column to group by
        multiplier: IQR multiplier for outlier detection
        
    Returns:
        DataFrame with outlier flags
    """
    df = df.copy()
    df['is_outlier'] = False
    
    def flag_outliers(group):
        rt = group['Reaction Time']
        q1 = rt.quantile(0.25)
        q3 = rt.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        group['is_outlier'] = (rt < lower_bound) | (rt > upper_bound)
        return group
    
    df = df.groupby(group_col, group_keys=False).apply(flag_outliers)
    return df

def normalize_and_flag_outliers(df: pd.DataFrame, group_col: str = 'Condition') -> pd.DataFrame:
    """
    Normalize reaction times AND flag outliers using the Interquartile Range (IQR) method
    calculated per Condition group (FR-002).
    
    This function combines normalization and outlier detection into a single pipeline step.
    It adds 'RT_normalized' and 'is_outlier' columns to the dataframe.
    
    Args:
        df: Input dataframe
        group_col: Column to group by for IQR calculation (default: 'Condition')
        
    Returns:
        DataFrame with normalized reaction times and outlier flags.
        Does NOT remove rows; only flags them.
    """
    # First normalize the reaction times
    df = normalize_rt(df)
    
    # Then flag outliers based on the original Reaction Time column per group
    df = detect_outliers_iqr(df, group_col=group_col)
    
    return df

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract summary features per participant/condition.
    
    Computes mean Reaction Time and average Mood for each unique combination of
    Participant ID and Condition. If 'Participant ID' is missing, aggregates only by Condition.
    
    Args:
        df: Input dataframe (preprocessed, must contain 'Condition', 'Reaction Time', 'Mood')
        
    Returns:
        DataFrame with extracted features: ['Participant ID', 'Condition', 'mean_rt', 'avg_mood']
        or ['Condition', 'mean_rt', 'avg_mood'] if no participant ID.
    """
    if 'Participant ID' not in df.columns:
        # Fallback: group by condition only if participant ID is missing
        logging.warning("Column 'Participant ID' not found. Aggregating by Condition only.")
        features = df.groupby('Condition').agg({
            'Reaction Time': 'mean',
            'Mood': 'mean'
        }).reset_index()
        features.columns = ['Condition', 'mean_rt', 'avg_mood']
    else:
        features = df.groupby(['Participant ID', 'Condition']).agg({
            'Reaction Time': 'mean',
            'Mood': 'mean'
        }).reset_index()
        features.columns = ['Participant ID', 'Condition', 'mean_rt', 'avg_mood']
    
    return features

def save_preprocessed_data(df: pd.DataFrame, output_path: str, design_type: str):
    """Save preprocessed data to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    # Save design type metadata
    metadata = {
        'design_type': design_type,
        'n_rows': len(df),
        'n_columns': len(df.columns)
    }
    
    metadata_path = output_path.replace('.csv', '_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def run_preprocessing(input_path: str, output_path: str, design_type: str):
    """Run the full preprocessing pipeline."""
    logging.info(f"Loading data from {input_path}")
    
    # Handle directory input (common for raw data ingestion) vs file input
    if os.path.isdir(input_path):
        # Look for CSV files in the directory
        csv_files = [f for f in os.listdir(input_path) if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {input_path}")
        # Assume the first valid CSV is the target, or combine if needed.
        # For this pipeline, we assume a single consolidated CSV or the first one found.
        input_file = os.path.join(input_path, csv_files[0])
        logging.info(f"Found input file: {input_file}")
    else:
        input_file = input_path
    
    df = pd.read_csv(input_file)
    
    logging.info("Cleaning data")
    df = clean_data(df)
    
    logging.info("Normalizing reaction times and flagging outliers")
    # T021 Implementation: Use the combined function
    df = normalize_and_flag_outliers(df, group_col='Condition')
    
    logging.info("Extracting features")
    features = extract_features(df)
    
    logging.info(f"Saving preprocessed data to {output_path}")
    save_preprocessed_data(features, output_path, design_type)
    
    return features

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python preprocess.py <input_path> <output_path> <design_type>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    design_type = sys.argv[3]
    
    run_preprocessing(input_path, output_path, design_type)
