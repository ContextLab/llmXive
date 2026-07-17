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

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract summary features per participant/condition.
    
    Args:
        df: Input dataframe
        
    Returns:
        DataFrame with extracted features
    """
    if 'Participant ID' not in df.columns:
        # If no participant ID, group by condition only
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
    df = pd.read_csv(input_path)
    
    logging.info("Cleaning data")
    df = clean_data(df)
    
    logging.info("Normalizing reaction times")
    df = normalize_rt(df)
    
    logging.info("Detecting outliers")
    df = detect_outliers_iqr(df)
    
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
