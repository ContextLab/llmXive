"""
Memory-optimized version of preprocess.py for large dataset handling.
Uses streaming and chunked processing to stay within memory constraints.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

# Import from existing modules
from utils.config import get_config_summary, set_seed
from utils.memory_optimizer import (
    get_memory_usage_mb,
    force_gc,
    chunked_dataframe_reader,
    optimize_dataframe_dtypes,
    stream_process_large_dataset,
    validate_memory_constraints
)
from config import get_config_summary as get_main_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 50000  # Rows per chunk for streaming
MAX_MEMORY_MB = 7000


class EventDataset(Dataset):
    """Memory-efficient dataset wrapper for event data."""
    
    def __init__(self, parquet_path: str, chunk_size: int = CHUNK_SIZE):
        self.parquet_path = Path(parquet_path)
        self.chunk_size = chunk_size
        self.file_size = self.parquet_path.stat().st_size
        self.total_rows = len(pd.read_parquet(parquet_path, columns=['timestamp']))
        
    def __len__(self):
        return self.total_rows
    
    def __getitem__(self, idx):
        # Read only the required chunk containing this index
        start = (idx // self.chunk_size) * self.chunk_size
        end = min(start + self.chunk_size, self.total_rows)
        
        df = pd.read_parquet(self.parquet_path, 
                           columns=['timestamp', 'semantic_feature', 'prosodic_feature', 
                                   'latent_delta_magnitude', 'turn_label', 'priority'])
        chunk = df.iloc[start:end]
        
        row_in_chunk = idx % self.chunk_size
        item = {
            'timestamp': chunk.iloc[row_in_chunk]['timestamp'],
            'semantic_feature': chunk.iloc[row_in_chunk]['semantic_feature'],
            'prosodic_feature': chunk.iloc[row_in_chunk]['prosodic_feature'],
            'latent_delta_magnitude': chunk.iloc[row_in_chunk]['latent_delta_magnitude'],
            'turn_label': chunk.iloc[row_in_chunk]['turn_label'],
            'priority': chunk.iloc[row_in_chunk]['priority']
        }
        
        del df, chunk
        return item


def load_config() -> Dict[str, Any]:
    """Load configuration from config.py."""
    return get_main_config()


def fetch_data_source() -> str:
    """Determine data source from config."""
    config = load_config()
    return config.get('data_source', 'voxceleb2')


def filter_events(chunk: pd.DataFrame, thresholds: Dict[str, float]) -> pd.DataFrame:
    """Filter for interruption/pause events using thresholds."""
    audio_energy_col = 'audio_energy' if 'audio_energy' in chunk.columns else 'prosodic_feature'
    
    if 'interruption_threshold' in thresholds:
        interruption_mask = chunk[audio_energy_col] > thresholds['interruption_threshold']
        chunk = chunk[interruption_mask]
    
    if 'pause_threshold' in thresholds:
        pause_mask = chunk[audio_energy_col] < thresholds['pause_threshold']
        chunk = chunk[pause_mask]
    
    return chunk


def compute_latent_deltas(chunk: pd.DataFrame) -> pd.DataFrame:
    """Compute latent delta magnitudes."""
    if 'latent_delta_magnitude' not in chunk.columns:
        semantic = chunk['semantic_feature'].astype(float)
        prosodic = chunk['prosodic_feature'].astype(float)
        chunk['latent_delta_magnitude'] = np.abs(semantic - prosodic)
    return chunk


def apply_stratified_sampling(
    chunk: pd.DataFrame,
    target_size: int,
    power_analysis: Dict[str, Any]
) -> pd.DataFrame:
    """Apply stratified sampling to preserve distribution."""
    if len(chunk) <= target_size:
        return chunk
    
    # Stratify by turn_label and priority
    strata = ['turn_label', 'priority']
    available_strata = [s for s in strata if s in chunk.columns]
    
    if not available_strata:
        return chunk.sample(n=target_size, random_state=42)
    
    # Calculate sampling fraction
    sampling_fraction = target_size / len(chunk)
    
    sampled_chunks = []
    for name, group in chunk.groupby(available_strata, dropna=False):
        sample_size = max(1, int(len(group) * sampling_fraction))
        sampled = group.sample(n=min(sample_size, len(group)), random_state=42)
        sampled_chunks.append(sampled)
    
    result = pd.concat(sampled_chunks, ignore_index=True)
    return result


def label_priority(chunk: pd.DataFrame, thresholds: Dict[str, float]) -> pd.DataFrame:
    """Label events as high-priority or low-priority."""
    if 'priority' not in chunk.columns:
        chunk['priority'] = 'low-priority'
    
    audio_energy_col = 'audio_energy' if 'audio_energy' in chunk.columns else 'prosodic_feature'
    
    if 'interruption_threshold' in thresholds:
        high_priority_mask = chunk[audio_energy_col] > thresholds['interruption_threshold']
        chunk.loc[high_priority_mask, 'priority'] = 'high-priority'
    
    return chunk


def log_priority_counts(chunk: pd.DataFrame) -> None:
    """Log counts of high/low priority events."""
    if 'priority' in chunk.columns:
        counts = chunk['priority'].value_counts()
        logger.info(f"Priority distribution: {counts.to_dict()}")


def validate_output(chunk: pd.DataFrame) -> bool:
    """Validate that required columns are present and non-null."""
    required_cols = ['timestamp', 'semantic_feature', 'prosodic_feature', 
                    'latent_delta_magnitude', 'turn_label', 'priority']
    
    for col in required_cols:
        if col not in chunk.columns:
            logger.error(f"Missing required column: {col}")
            return False
        if chunk[col].isnull().any():
            logger.warning(f"Column {col} contains null values")
    
    return True


def process_chunk(chunk: pd.DataFrame, thresholds: Dict[str, float], 
                 power_analysis: Dict[str, Any]) -> pd.DataFrame:
    """Process a single chunk through the pipeline."""
    chunk = filter_events(chunk, thresholds)
    chunk = compute_latent_deltas(chunk)
    chunk = label_priority(chunk, thresholds)
    log_priority_counts(chunk)
    chunk = validate_output(chunk)
    
    if not chunk.empty:
        return chunk
    return pd.DataFrame()


def main():
    """Main entry point for memory-optimized preprocessing."""
    parser = argparse.ArgumentParser(description="Memory-optimized data preprocessing")
    parser.add_argument('--input', type=str, required=True, 
                      help='Input parquet file path')
    parser.add_argument('--output', type=str, required=True,
                      help='Output parquet file path')
    parser.add_argument('--target-size', type=int, default=1000000,
                      help='Target dataset size in rows')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE,
                      help='Chunk size for processing')
    args = parser.parse_args()
    
    set_seed(42)
    
    # Load configuration
    config = load_config()
    thresholds = config.get('detection_thresholds', {
        'interruption_threshold': 20.0,
        'pause_threshold': 5.0
    })
    
    power_analysis = {
        'min_sample_size': config.get('min_sample_size', 10000),
        'expected_variance': config.get('expected_variance', 1.0),
        'effect_size': config.get('effect_size', 0.2)
    }
    
    logger.info(f"Starting memory-optimized preprocessing")
    logger.info(f"Input: {args.input}, Output: {args.output}")
    logger.info(f"Target size: {args.target_size:,} rows")
    
    # Validate memory constraints
    if not validate_memory_constraints(MAX_MEMORY_MB):
        logger.error("Memory constraints exceeded before processing")
        sys.exit(1)
    
    # Process in chunks
    def process_wrapper(df):
        return process_chunk(df, thresholds, power_analysis)
    
    stream_process_large_dataset(
        args.input, 
        args.output, 
        process_wrapper,
        chunk_size=args.chunk_size
    )
    
    # Optimize final output
    logger.info("Optimizing output file dtypes...")
    df_final = pd.read_parquet(args.output)
    df_optimized = optimize_dataframe_dtypes(df_final)
    df_optimized.to_parquet(args.output, index=False)
    
    final_size = get_memory_usage_mb()
    logger.info(f"Preprocessing completed. Final memory usage: {final_size:.2f} MB")


if __name__ == '__main__':
    main()
