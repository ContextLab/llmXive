"""
Feature extraction module for the pupil dilation pipeline.
Extracts load proxies from metadata and computes salience if needed.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config

logger = logging.getLogger(__name__)

def load_trial_metadata(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load trial metadata from the dataset.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        DataFrame with trial metadata
    """
    processed_dir = Path(config['paths']['processed_data'])
    preprocessed_file = processed_dir / 'preprocessed_data.csv'
    
    if not preprocessed_file.exists():
        logger.warning(f"Preprocessed data not found: {preprocessed_file}")
        return pd.DataFrame(columns=['subject_id', 'trial_id', 'search_time', 'fixation_count'])
    
    df = pd.read_csv(preprocessed_file)
    
    # Aggregate to trial level if needed
    if 'trial_id' not in df.columns:
        # Create trial IDs based on subject and time windows
        df['trial_id'] = df.groupby('subject_id').cumcount()
    
    return df

def extract_features(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract load proxy features from the data.
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        
    Returns:
        DataFrame with extracted features
    """
    features = []
    
    # Group by subject and trial
    if 'subject_id' in df.columns and 'trial_id' in df.columns:
        groups = df.groupby(['subject_id', 'trial_id'])
    else:
        # Fallback: treat entire dataset as one trial
        groups = [('unknown', 0)]
        df['subject_id'] = 'unknown'
        df['trial_id'] = 0
        groups = df.groupby(['subject_id', 'trial_id'])
    
    for (subject_id, trial_id), group in groups:
        feature_row = {
            'subject_id': subject_id,
            'trial_id': trial_id,
            'search_time': None,
            'fixation_count': len(group),
            'target_salience': None,
            'status': 'OK'
        }
        
        # Try to extract search_time from metadata if available
        # In real implementation, this would come from a metadata file
        # For now, we'll estimate based on data characteristics
        if 'search_time' in group.columns and not group['search_time'].isna().all():
            feature_row['search_time'] = group['search_time'].mean()
        else:
            # Mark as potentially missing
            logger.debug(f"Search time missing for subject {subject_id}, trial {trial_id}")
            feature_row['status'] = 'MISSING_METADATA'
        
        features.append(feature_row)
    
    return pd.DataFrame(features)

def compute_target_salience(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute target salience from stimulus images if metadata is missing.
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        
    Returns:
        DataFrame with salience values
    """
    stimuli_dir = Path(config['paths']['external_stimuli'])
    
    if not stimuli_dir.exists():
        logger.warning(f"Stimuli directory not found: {stimuli_dir}")
        df['target_salience'] = None
        df.loc[df['status'] == 'OK', 'status'] = 'UNFULFILLABLE'
        return df
    
    # In a real implementation, this would load images and compute Gabor filters
    # For now, we mark as unfulfillable if metadata is missing
    missing_mask = df['target_salience'].isna()
    if missing_mask.any():
        logger.warning(f"Cannot compute salience for {missing_mask.sum()} trials: no stimuli data")
        df.loc[missing_mask, 'status'] = 'UNFULFILLABLE'
    
    return df

def process_dataset_features(config: Dict[str, Any]):
    """
    Process the full dataset to extract all features.
    
    Args:
        config: Configuration dictionary
    """
    processed_dir = Path(config['paths']['processed_data'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load metadata
    df = load_trial_metadata(config)
    
    if df.empty:
        # Create empty features file
        features_df = pd.DataFrame(columns=['subject_id', 'trial_id', 'search_time', 
                                            'fixation_count', 'target_salience', 'status'])
        features_df.to_csv(processed_dir / 'features.csv', index=False)
        logger.warning("No data found. Created empty features file.")
        return
    
    # Extract features
    features_df = extract_features(df, config)
    
    # Compute salience if needed
    features_df = compute_target_salience(features_df, config)
    
    # Save features
    output_path = processed_dir / 'features.csv'
    features_df.to_csv(output_path, index=False)
    
    logger.info(f"Features extracted. Output: {output_path}")
    logger.info(f"Summary: {len(features_df)} trials, {features_df['status'].value_counts().to_dict()}")

def main():
    """Main entry point for feature extraction."""
    parser = argparse.ArgumentParser(description="Extract features from eye-tracking data")
    parser.add_argument("--config", type=str, default="code/config.yaml")
    args = parser.parse_args()
    
    config = load_config(Path(args.config))
    process_dataset_features(config)

if __name__ == "__main__":
    main()