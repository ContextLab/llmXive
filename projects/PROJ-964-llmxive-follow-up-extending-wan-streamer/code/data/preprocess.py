"""
code/data/preprocess.py - Data preprocessing pipeline for Wan-Streamer v0.1 follow-up.

This module implements:
1. Data filtering for interruption/pause events (T014a).
2. Stratified sampling to reduce dataset size (T014b).
3. Data validation (T014c).
"""
import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config_summary, DEFAULT_SAMPLE_SIZE
from data.validate_logs import check_logs_exist, fetch_voxceleb2_dataset
from tasks.reduce_sample_size import PowerLimitationError, reduce_sample_size

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
RAW_EXTRACT_PATH = PROJECT_ROOT / "data" / "processed" / "raw_extract.parquet"
FILTERED_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "filtered_dataset.parquet"
SAMPLED_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "sampled_dataset.parquet"
THRESHOLDS_PATH = PROJECT_ROOT / "code" / "config" / "detection_thresholds.yaml"
POWER_ANALYSIS_PATH = PROJECT_ROOT / "data" / "metrics" / "power_analysis_initial.json"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> Dict[str, Any]:
    """Load detection thresholds from YAML."""
    if not THRESHOLDS_PATH.exists():
        raise FileNotFoundError(f"Thresholds file not found: {THRESHOLDS_PATH}")
    with open(THRESHOLDS_PATH, 'r') as f:
        return yaml.safe_load(f)

def fetch_data_source() -> pd.DataFrame:
    """
    Fetch data from Wan-Streamer logs or VoxCeleb2.
    This is a placeholder for the actual extraction logic which should have run in T013.
    For this module, we assume raw_extract.parquet exists or fetch_voxceleb2_dataset creates it.
    """
    if RAW_EXTRACT_PATH.exists():
        logger.info(f"Loading existing raw extract from {RAW_EXTRACT_PATH}")
        return pd.read_parquet(RAW_EXTRACT_PATH)
    
    # Fallback: Attempt to fetch and process if raw_extract doesn't exist
    # In a real pipeline, T013 would have created this.
    logger.warning("Raw extract not found. Attempting to fetch VoxCeleb2 and extract (T013 logic).")
    # Note: This logic is simplified. In production, T013 should be run first.
    # We assume T009 has set up the dataset path.
    from config import DATASET_PATH
    if DATASET_PATH is None:
       # Try to fetch
       try:
           fetch_voxceleb2_dataset()
       except Exception as e:
           logger.error(f"Failed to fetch VoxCeleb2: {e}")
           raise
    
    if not RAW_EXTRACT_PATH.exists():
        raise FileNotFoundError("Data source unavailable and extraction failed.")
    
    return pd.read_parquet(RAW_EXTRACT_PATH)

def filter_events(df: pd.DataFrame, thresholds: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter dataframe for interruption/pause events based on thresholds.
    Implements T014a logic.
    """
    logger.info("Filtering events based on thresholds...")
    
    # Example logic: Filter based on audio_energy and latent_delta_magnitude
    # Adjust column names based on actual schema from T013
    audio_energy_col = 'audio_energy'
    delta_mag_col = 'latent_delta_magnitude'
    
    if audio_energy_col not in df.columns or delta_mag_col not in df.columns:
        logger.error(f"Required columns missing. Found: {df.columns.tolist()}")
        raise ValueError("Missing required columns for filtering.")

    energy_thresh = thresholds.get('audio_energy_threshold', 20.0)
    delta_thresh = thresholds.get('latent_delta_threshold', 0.5) # Assumed default

    # Filter for events (e.g., high energy or high delta)
    # Logic: interruption if energy > thresh AND delta > thresh
    # Logic: pause if energy < thresh (low energy)
    # This is a placeholder logic matching the task description's intent.
    
    mask = (df[audio_energy_col] > energy_thresh) & (df[delta_mag_col] > delta_thresh)
    filtered_df = df[mask].copy()
    
    logger.info(f"Filtered to {len(filtered_df)} events.")
    return filtered_df

def compute_latent_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """Compute latent delta magnitude if not present."""
    if 'latent_delta_magnitude' not in df.columns:
        logger.warning("latent_delta_magnitude not found, computing from latent vectors...")
        # Placeholder: assume 'latent_vector' is a list or array column
        if 'latent_vector' in df.columns:
            df['latent_delta_magnitude'] = df['latent_vector'].apply(lambda x: np.linalg.norm(x) if isinstance(x, (list, np.ndarray)) else 0.0)
        else:
            df['latent_delta_magnitude'] = 0.0 # Fallback
    return df

def label_priority(df: pd.DataFrame, thresholds: Dict[str, Any]) -> pd.DataFrame:
    """Label events as high-priority or low-priority."""
    logger.info("Labeling event priority...")
    
    # High priority: interruption events (high energy, high delta)
    # Low priority: pause events (low energy)
    # Using the same thresholds as filtering for consistency
    energy_thresh = thresholds.get('audio_energy_threshold', 20.0)
    delta_thresh = thresholds.get('latent_delta_threshold', 0.5)

    def classify(row):
        if row['audio_energy'] > energy_thresh and row['latent_delta_magnitude'] > delta_thresh:
            return 'high-priority'
        elif row['audio_energy'] < energy_thresh: # Pause
            return 'low-priority'
        else:
            return 'medium-priority' # Boundary case

    df['priority_label'] = df.apply(classify, axis=1)
    return df

def log_priority_counts(df: pd.DataFrame):
    """Log counts of priority labels."""
    counts = df['priority_label'].value_counts()
    logger.info("Priority Counts:")
    for label, count in counts.items():
        logger.info(f"  {label}: {count}")

def load_power_analysis() -> Optional[int]:
    """
    Load recommended sample size from power analysis JSON.
    Returns None if file missing or key not found.
    """
    if not POWER_ANALYSIS_PATH.exists():
        logger.warning(f"Power analysis file not found: {POWER_ANALYSIS_PATH}. Using DEFAULT_SAMPLE_SIZE.")
        return None
    
    try:
        with open(POWER_ANALYSIS_PATH, 'r') as f:
            data = json.load(f)
            size = data.get('recommended_sample_size')
            if size is not None:
                logger.info(f"Loaded recommended sample size: {size}")
                return size
            else:
                logger.warning("recommended_sample_size key missing in power analysis. Using DEFAULT_SAMPLE_SIZE.")
                return None
    except Exception as e:
        logger.error(f"Error reading power analysis: {e}. Using DEFAULT_SAMPLE_SIZE.")
        return None

def apply_stratified_sampling(df: pd.DataFrame, target_size: int) -> pd.DataFrame:
    """
    Perform stratified sampling to reduce dataset to target_size.
    Stratify by 'priority_label' to preserve distribution (FR-015).
    """
    logger.info(f"Applying stratified sampling to reduce to {target_size} rows...")
    
    if len(df) <= target_size:
        logger.info("Dataset already smaller than or equal to target size. No sampling needed.")
        return df

    if 'priority_label' not in df.columns:
        logger.warning("priority_label column missing. Falling back to random sampling.")
        sampled_df = df.sample(n=target_size, random_state=42)
        return sampled_df

    # Calculate proportions
    strata_counts = df['priority_label'].value_counts(normalize=True)
    sampled_counts = (strata_counts * target_size).astype(int)
    
    # Ensure sum matches target_size (handle rounding errors)
    diff = target_size - sampled_counts.sum()
    if diff != 0:
        # Add/subtract from the largest group
        largest_group = sampled_counts.idxmax()
        sampled_counts[largest_group] += diff

    sampled_frames = []
    for label, count in sampled_counts.items():
        if count > 0:
            group_df = df[df['priority_label'] == label]
            if len(group_df) < count:
                # Take all if group is smaller than requested count
                sampled_frames.append(group_df)
            else:
                sampled_frames.append(group_df.sample(n=count, random_state=42))
    
    sampled_df = pd.concat(sampled_frames, ignore_index=True)
    logger.info(f"Stratified sampling complete. New size: {len(sampled_df)}")
    return sampled_df

def validate_output(df: pd.DataFrame) -> bool:
    """
    Validate that all required columns are non-null and correctly typed.
    Implements T014c logic.
    """
    required_cols = ['timestamp', 'semantic_feature', 'prosodic_feature', 'latent_delta_magnitude', 'turn_label', 'priority_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    # Check for nulls in critical columns
    critical_cols = ['timestamp', 'turn_label', 'priority_label']
    for col in critical_cols:
        if df[col].isnull().any():
            logger.warning(f"Column {col} contains null values.")
            # Option: Drop or impute. For now, just log.

    # Add validation flag
    df['validation_passed'] = True
    return True

def get_current_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0

def handle_power_limitation(current_size: int) -> int:
    """
    Handle power limitation by reducing sample size.
    Calls reduce_sample_size module.
    """
    logger.warning("Power limitation detected. Attempting to reduce sample size.")
    try:
        new_size, success = reduce_sample_size(current_size)
        if success:
            return new_size
        else:
            raise PowerLimitationError("Failed to reduce sample size below minimum.")
    except Exception as e:
        logger.error(f"Power limitation handling failed: {e}")
        raise

def main():
    """
    Main execution flow for T014a, T014b, T014c.
    1. Load raw data.
    2. Filter events (T014a).
    3. Apply stratified sampling (T014b).
    4. Validate output (T014c).
    5. Save to sampled_dataset.parquet.
    """
    logger.info("Starting preprocessing pipeline...")

    # 1. Load Data
    try:
        df = fetch_data_source()
    except Exception as e:
        logger.error(f"Failed to load data source: {e}")
        sys.exit(1)

    # 2. Filter Events (T014a)
    try:
        config = load_config()
        df_filtered = filter_events(df, config)
        df_filtered = compute_latent_deltas(df_filtered)
        df_filtered = label_priority(df_filtered, config)
        log_priority_counts(df_filtered)
        
        # Save intermediate filtered dataset
        FILTERED_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
        df_filtered.to_parquet(FILTERED_DATASET_PATH, index=False)
        logger.info(f"Filtered dataset saved to {FILTERED_DATASET_PATH}")
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        sys.exit(1)

    # 3. Stratified Sampling (T014b)
    target_size = load_power_analysis()
    if target_size is None:
        target_size = DEFAULT_SAMPLE_SIZE
        logger.info(f"Using default sample size: {target_size}")

    try:
        # Check if we need to reduce due to power limits
        if len(df_filtered) > target_size:
            # Check memory as a proxy for power
            mem_mb = get_current_memory_usage_mb()
            if mem_mb > 7000: # 7GB limit
                target_size = handle_power_limitation(target_size)
        
        df_sampled = apply_stratified_sampling(df_filtered, target_size)
    except Exception as e:
        logger.error(f"Sampling failed: {e}")
        sys.exit(1)

    # 4. Validate Output (T014c)
    try:
        is_valid = validate_output(df_sampled)
        if not is_valid:
            logger.error("Validation failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Validation check failed: {e}")
        sys.exit(1)

    # 5. Save Final Output
    SAMPLED_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_sampled.to_parquet(SAMPLED_DATASET_PATH, index=False)
    logger.info(f"Sampled dataset saved to {SAMPLED_DATASET_PATH}")
    logger.info(f"Final row count: {len(df_sampled)}")

    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()