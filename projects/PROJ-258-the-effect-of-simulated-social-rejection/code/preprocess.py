import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import logging
import json
import os
from config import get_path
from data_model import DesignType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning: remove rows with missing critical columns.
    """
    critical_cols = ['ParticipantID', 'Condition', 'Reaction Time', 'Mood']
    available_cols = [c for c in critical_cols if c in df.columns]
    if not available_cols:
        raise ValueError("DataFrame missing critical columns for cleaning.")
    
    # Drop rows where any critical column is NaN
    df_clean = df.dropna(subset=available_cols)
    logger.info(f"Cleaned data: {len(df)} -> {len(df_clean)} rows")
    return df_clean

def normalize_rt(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize reaction times (log transform to handle skew).
    """
    if 'Reaction Time' not in df.columns:
        logger.warning("Reaction Time column missing; skipping normalization.")
        return df
    
    # Add small epsilon to avoid log(0)
    epsilon = 1e-6
    df['Reaction_Time_Log'] = np.log(df['Reaction Time'] + epsilon)
    logger.info("Normalized Reaction Time (log transform).")
    return df

def detect_outliers_iqr(df: pd.DataFrame, group_col: str = 'Condition') -> pd.DataFrame:
    """
    Flag/cap outliers using IQR per Condition group.
    Adds a boolean column 'is_outlier'.
    """
    if group_col not in df.columns or 'Reaction Time' not in df.columns:
        logger.warning("Cannot detect outliers: missing group or RT column.")
        df['is_outlier'] = False
        return df

    df = df.copy()
    df['is_outlier'] = False

    groups = df[group_col].unique()
    for group in groups:
        mask = df[group_col] == group
        group_data = df.loc[mask, 'Reaction Time']
        if len(group_data) < 2:
            continue
        
        q1 = group_data.quantile(0.25)
        q3 = group_data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (df.loc[mask, 'Reaction Time'] < lower_bound) | \
                       (df.loc[mask, 'Reaction Time'] > upper_bound)
        df.loc[mask, 'is_outlier'] = outlier_mask

    outlier_count = df['is_outlier'].sum()
    logger.info(f"Detected {outlier_count} outliers using IQR method.")
    return df

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute mean_rt and avg_mood per participant/condition.
    Returns a dataframe with one row per (ParticipantID, Condition).
    """
    if 'ParticipantID' not in df.columns or 'Condition' not in df.columns:
        raise ValueError("Missing ParticipantID or Condition for feature extraction.")

    agg_dict = {}
    if 'Reaction Time' in df.columns:
        agg_dict['Reaction Time'] = 'mean'
    if 'Mood' in df.columns:
        agg_dict['Mood'] = 'mean'
    
    if not agg_dict:
        logger.warning("No aggregatable columns found for feature extraction.")
        return df

    # Rename for clarity in output
    feature_df = df.groupby(['ParticipantID', 'Condition']).agg(agg_dict).reset_index()
    
    if 'Reaction Time' in feature_df.columns:
        feature_df = feature_df.rename(columns={'Reaction Time': 'mean_rt'})
    if 'Mood' in feature_df.columns:
        feature_df = feature_df.rename(columns={'Mood': 'avg_mood'})
        
    logger.info(f"Extracted features: {len(feature_df)} participant-condition records.")
    return feature_df

def save_preprocessed_data(df: pd.DataFrame, design_type: str) -> str:
    """
    Save intermediate data to data/interim/preprocessed_data.csv with design_type tag.
    """
    output_dir = get_path('interim')
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure design_type is in the dataframe
    if 'design_type' not in df.columns:
        df['design_type'] = design_type
    
    output_path = os.path.join(output_dir, 'preprocessed_data.csv')
    df.to_csv(output_path, index=False)
    logger.info(f"Saved preprocessed data to {output_path} with design_type={design_type}")
    return output_path

def run_preprocessing(design_type: str, input_path: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Main entry point for preprocessing pipeline.
    Loads data, cleans, normalizes, detects outliers, extracts features, and saves.
    """
    if input_path is None:
        input_path = get_path('processed', 'preprocessed_input.csv') # Assumed output of ingest or previous step
        if not os.path.exists(input_path):
            # Fallback to raw if processed doesn't exist (for testing flow)
            input_path = get_path('raw', 'dataset.csv')
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input data file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info("Starting preprocessing pipeline...")
    df = clean_data(df)
    df = normalize_rt(df)
    df = detect_outliers_iqr(df)
    df = extract_features(df)

    if output_path is None:
        output_path = save_preprocessed_data(df, design_type)
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved preprocessed data to {output_path}")

    return output_path
