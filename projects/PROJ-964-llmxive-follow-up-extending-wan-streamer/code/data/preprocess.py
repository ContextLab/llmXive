"""
Preprocessing pipeline for Wan-Streamer v0.1 logs.
Implements data extraction, filtering, stratified sampling, and power-limitation handling.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import psutil
import gc

# Project relative imports
from config import get_config_summary
from utils.config import set_seed
from tasks.reduce_sample_size import reduce_sample_size, PowerLimitationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_THRESHOLD_MB = 6500  # 6.5 GB threshold for graceful degradation
MIN_SAMPLE_SIZE = 10000  # Minimum frames required for valid analysis
RANDOM_STATE = 42

def load_config() -> Dict[str, Any]:
    """Load configuration from config.py."""
    return get_config_summary()

def fetch_data_source(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Fetch data from the configured source (Wan-Streamer logs or VoxCeleb2).
    Returns a DataFrame with raw frames.
    """
    # Placeholder for actual data loading logic
    # In a real implementation, this would load from logs or fetch VoxCeleb2
    # For now, we assume the data is already prepared by validate_logs.py
    data_path = Path(config.get('data_path', 'data/processed/raw_frames.parquet'))
    if not data_path.exists():
        raise FileNotFoundError(f"Data source not found: {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)
    return df

def filter_events(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter for interruption and pause events based on configured thresholds.
    """
    audio_threshold = config.get('audio_energy_threshold_db', -20.0)
    pause_threshold = config.get('pause_duration_threshold_sec', 0.5)
    
    # Filter based on audio energy and duration
    # Assuming columns: 'audio_energy_db', 'duration_sec', 'event_type'
    mask = (
        (df['audio_energy_db'] > audio_threshold) |
        (df['event_type'].isin(['interruption', 'pause']))
    )
    
    filtered_df = df[mask].copy()
    logger.info(f"Filtered events: {len(filtered_df)} events remaining")
    return filtered_df

def compute_latent_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute latent delta magnitudes between consecutive frames.
    """
    if 'latent_vector' not in df.columns:
        raise ValueError("DataFrame missing 'latent_vector' column")
    
    # Calculate delta magnitude
    df['latent_delta_magnitude'] = df['latent_vector'].apply(
        lambda x: np.linalg.norm(x) if isinstance(x, np.ndarray) else 0.0
    )
    
    # Compute deltas between consecutive frames
    df['latent_delta'] = df['latent_delta_magnitude'].diff().fillna(0.0)
    df['latent_delta_magnitude'] = df['latent_delta'].abs()
    
    return df

def apply_stratified_sampling(
    df: pd.DataFrame, 
    target_size_mb: float, 
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Apply stratified sampling to reduce dataset to target size while preserving distribution.
    """
    # Define stratification columns
    stratify_cols = ['turn_label']
    if 'priority' in df.columns:
        stratify_cols.append('priority')
    
    # Calculate current size
    current_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.info(f"Current dataset size: {current_size_mb:.2f} MB")
    
    if current_size_mb <= target_size_mb:
        logger.info("Dataset already within target size")
        return df
    
    # Calculate sampling fraction
    sampling_fraction = target_size_mb / current_size_mb
    logger.info(f"Applying stratified sampling with fraction: {sampling_fraction:.4f}")
    
    # Apply stratified sampling
    sampled_df = df.groupby(stratify_cols, group_keys=False).apply(
        lambda x: x.sample(frac=sampling_fraction, random_state=RANDOM_STATE)
    ).reset_index(drop=True)
    
    logger.info(f"Sampled dataset size: {sampled_df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
    return sampled_df

def label_priority(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Label events as high-priority or low-priority based on criteria.
    """
    high_priority_threshold = config.get('high_priority_delta_threshold', 0.5)
    
    # Label based on latent delta magnitude
    df['priority'] = np.where(
        df['latent_delta_magnitude'] > high_priority_threshold,
        'high',
        'low'
    )
    
    # Count priorities
    priority_counts = df['priority'].value_counts()
    logger.info(f"Priority distribution:\n{priority_counts}")
    
    return df

def validate_output(df: pd.DataFrame, config: Dict[str, Any]) -> bool:
    """
    Validate that all required columns are present and non-null.
    """
    required_columns = [
        'timestamp', 'semantic_feature', 'prosodic_feature',
        'latent_delta_magnitude', 'turn_label', 'priority'
    ]
    
    # Check for required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for null values
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        logger.error(f"Null values found in required columns:\n{null_counts[null_counts > 0]}")
        return False
    
    # Check data types
    expected_types = {
        'timestamp': 'datetime64[ns]',
        'latent_delta_magnitude': 'float64',
        'turn_label': 'object',
        'priority': 'object'
    }
    
    for col, expected_type in expected_types.items():
        if str(df[col].dtype) != expected_type:
            logger.warning(f"Column '{col}' has dtype {df[col].dtype}, expected {expected_type}")
    
    logger.info("Output validation passed")
    return True

def get_current_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def handle_power_limitation(
    df: pd.DataFrame, 
    target_size_mb: float, 
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, bool]:
    """
    Enforce graceful degradation if memory limits are approached.
    Calls reduce_sample_size module to reduce dataset size.
    Returns (reduced_df, success_flag).
    """
    current_memory = get_current_memory_usage_mb()
    logger.info(f"Current memory usage: {current_memory:.2f} MB (Threshold: {MEMORY_THRESHOLD_MB} MB)")
    
    if current_memory < MEMORY_THRESHOLD_MB:
        logger.info("Memory usage within safe limits")
        return df, True
    
    logger.warning(f"Memory threshold exceeded ({current_memory:.2f} MB > {MEMORY_THRESHOLD_MB} MB)")
    logger.info("Attempting to reduce sample size via T016 module...")
    
    try:
        # Calculate new target size (reduce by 20% each iteration)
        reduction_factor = 0.8
        new_target_size = target_size_mb * reduction_factor
        min_size = MIN_SAMPLE_SIZE  # Minimum valid sample size
        
        # Attempt reduction
        reduced_df = reduce_sample_size(
            df=df,
            target_size_mb=new_target_size,
            min_sample_size=min_size,
            config=config
        )
        
        # Verify reduction was successful
        reduced_memory = get_current_memory_usage_mb()
        logger.info(f"Reduced dataset size: {reduced_df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
        logger.info(f"New memory usage: {reduced_memory:.2f} MB")
        
        if reduced_memory < MEMORY_THRESHOLD_MB:
            logger.info("Memory pressure relieved successfully")
            return reduced_df, True
        else:
            logger.warning("Memory still above threshold after reduction")
            # Try one more time with more aggressive reduction
            new_target_size = target_size_mb * (reduction_factor ** 2)
            reduced_df = reduce_sample_size(
                df=reduced_df,
                target_size_mb=new_target_size,
                min_sample_size=min_size,
                config=config
            )
            
            reduced_memory = get_current_memory_usage_mb()
            if reduced_memory < MEMORY_THRESHOLD_MB:
                logger.info("Memory pressure relieved after second reduction attempt")
                return reduced_df, True
            else:
                logger.error("Failed to relieve memory pressure after multiple reduction attempts")
                return reduced_df, False
                
    except PowerLimitationError as e:
        logger.error(f"Power limitation error: {str(e)}")
        logger.error("Cannot maintain minimum valid sample size")
        return df, False
    except Exception as e:
        logger.error(f"Unexpected error during power limitation handling: {str(e)}")
        return df, False

def main():
    """Main preprocessing pipeline with power limitation handling."""
    parser = argparse.ArgumentParser(description='Preprocess Wan-Streamer v0.1 logs')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--output', type=str, default='data/processed/preprocessed.parquet', help='Output path')
    parser.add_argument('--target-size-mb', type=float, default=900, help='Target dataset size in MB')
    args = parser.parse_args()
    
    # Set seed for reproducibility
    set_seed(RANDOM_STATE)
    
    # Load configuration
    config = load_config()
    
    # Fetch data
    try:
        df = fetch_data_source(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Filter events
    df = filter_events(df, config)
    
    # Compute latent deltas
    df = compute_latent_deltas(df)
    
    # Label priorities
    df = label_priority(df, config)
    
    # Check memory and apply power limitation handling if needed
    df, success = handle_power_limitation(df, args.target_size_mb, config)
    
    if not success:
        logger.error("Power limitation error: Cannot maintain minimum valid sample size")
        # Apply final stratified sampling to meet target size
        df = apply_stratified_sampling(df, args.target_size_mb, config)
        
        # If still too large, fail gracefully
        current_size = df.memory_usage(deep=True).sum() / (1024 * 1024)
        if current_size > args.target_size_mb:
            logger.error(f"Dataset size {current_size:.2f} MB exceeds target {args.target_size_mb} MB after all reductions")
            sys.exit(1)
    
    # Apply stratified sampling to ensure target size
    df = apply_stratified_sampling(df, args.target_size_mb, config)
    
    # Validate output
    if not validate_output(df, config):
        logger.error("Output validation failed")
        sys.exit(1)
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Preprocessing complete. Output saved to {output_path}")
    logger.info(f"Final dataset size: {df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
    logger.info(f"Total samples: {len(df)}")

if __name__ == '__main__':
    main()