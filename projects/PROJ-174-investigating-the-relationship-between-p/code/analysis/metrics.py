"""
Pupil metrics extraction module.
Computes peak, mean, and quantile statistics from pupil time-series data.
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

def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load preprocessed pupil data."""
    processed_dir = Path(config['paths']['processed_data'])
    features_file = processed_dir / 'features.csv'
    
    if not features_file.exists():
        logger.error(f"Features file not found: {features_file}")
        return pd.DataFrame()
    
    return pd.read_csv(features_file)

def extract_pupil_metrics(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract pupil metrics from the data.
    
    Args:
        df: Input DataFrame with pupil data
        config: Configuration dictionary
        
    Returns:
        DataFrame with extracted metrics
    """
    if df.empty:
        return df
    
    # Ensure we have pupil data
    if 'pupil_diameter' not in df.columns:
        logger.warning("No pupil_diameter column found")
        df['pupil_peak'] = np.nan
        df['pupil_mean'] = np.nan
        df['pupil_q25'] = np.nan
        df['pupil_q50'] = np.nan
        df['pupil_q75'] = np.nan
        return df
    
    # Group by subject and trial if available
    if 'subject_id' in df.columns and 'trial_id' in df.columns:
        groups = df.groupby(['subject_id', 'trial_id'])
    else:
        groups = [(0, 0), df]
    
    metrics_list = []
    
    for (subject_id, trial_id), group in groups:
        pupil_data = group['pupil_diameter'].dropna()
        
        if len(pupil_data) == 0:
            metrics_list.append({
                'subject_id': subject_id,
                'trial_id': trial_id,
                'pupil_peak': np.nan,
                'pupil_mean': np.nan,
                'pupil_q25': np.nan,
                'pupil_q50': np.nan,
                'pupil_q75': np.nan
            })
            continue
        
        metrics_list.append({
            'subject_id': subject_id,
            'trial_id': trial_id,
            'pupil_peak': pupil_data.max(),
            'pupil_mean': pupil_data.mean(),
            'pupil_q25': np.percentile(pupil_data, 25),
            'pupil_q50': np.percentile(pupil_data, 50),
            'pupil_q75': np.percentile(pupil_data, 75)
        })
    
    metrics_df = pd.DataFrame(metrics_list)
    
    # Merge back with original features if available
    if 'search_time' in df.columns or 'fixation_count' in df.columns:
        # Use the first row's metadata as representative
        first_row = df.iloc[0]
        for col in ['search_time', 'fixation_count', 'target_salience', 'status']:
            if col in first_row.index:
                metrics_df[col] = first_row[col]
    
    return metrics_df

def save_metrics(metrics_df: pd.DataFrame, config: Dict[str, Any]):
    """Save metrics to the features file."""
    processed_dir = Path(config['paths']['processed_data'])
    features_file = processed_dir / 'features.csv'
    
    if features_file.exists():
        existing = pd.read_csv(features_file)
        # Merge metrics with existing features
        merged = existing.merge(
            metrics_df[['subject_id', 'trial_id', 'pupil_peak', 'pupil_mean', 
                       'pupil_q25', 'pupil_q50', 'pupil_q75']],
            on=['subject_id', 'trial_id'],
            how='left'
        )
        merged.to_csv(features_file, index=False)
    else:
        metrics_df.to_csv(features_file, index=False)
    
    logger.info(f"Metrics saved to {features_file}")

def run_metrics_pipeline(config: Dict[str, Any]):
    """Run the full metrics extraction pipeline."""
    processed_dir = Path(config['paths']['processed_data'])
    preprocessed_file = processed_dir / 'preprocessed_data.csv'
    
    if not preprocessed_file.exists():
        logger.warning("No preprocessed data found. Creating empty metrics.")
        features_df = pd.DataFrame(columns=['subject_id', 'trial_id', 'pupil_peak', 
                                            'pupil_mean', 'pupil_q25', 'pupil_q50', 'pupil_q75'])
        save_metrics(features_df, config)
        return
    
    df = pd.read_csv(preprocessed_file)
    metrics_df = extract_pupil_metrics(df, config)
    save_metrics(metrics_df, config)
    
    logger.info("Metrics pipeline completed")

def main():
    """Main entry point for metrics extraction."""
    parser = argparse.ArgumentParser(description="Extract pupil metrics")
    parser.add_argument("--config", type=str, default="code/config.yaml")
    args = parser.parse_args()
    
    config = load_config(Path(args.config))
    run_metrics_pipeline(config)

if __name__ == "__main__":
    main()