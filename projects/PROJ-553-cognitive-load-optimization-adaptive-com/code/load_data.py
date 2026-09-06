"""
Data Loading Module for Cognitive Load Optimization Project.

This module handles fetching public datasets (ASSISTments, OULAD) via HuggingFace,
verifying the presence of required semantic features (latency, errors, hints),
and saving the processed data to disk.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

import pandas as pd
from datasets import load_dataset

# Configure logging
logger = logging.getLogger(__name__)

# Latency feature candidates (semantic equivalents)
LATENCY_FEATURES = [
    'response_timestamp',
    'answer_start_timestamp',
    'answer_end_timestamp',
    'time_spent',
    'response_time',
    'latency',
    'duration_ms',
    'duration',
    'elapsed_time',
    'reaction_time',
    'time_on_task'
]

# Timestamp pair candidates for derivation
TIMESTAMP_PAIRS = [
    ('answer_start_timestamp', 'answer_end_timestamp'),
    ('start_time', 'end_time'),
    ('timestamp_start', 'timestamp_end'),
    ('response_start', 'response_end'),
    ('start_ts', 'end_ts')
]

# Error feature candidates
ERROR_FEATURES = [
    'is_error',
    'correct',
    'correctness',
    'error',
    'mistake',
    'wrong',
    'accuracy',
    'outcome'
]

# Hint feature candidates
HINT_FEATURES = [
    'hint',
    'hint_count',
    'num_hints',
    'hint_requested',
    'hint_used',
    'request_hint',
    'scaffold',
    'help_requested'
]

def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the module."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def ensure_directories() -> Path:
    """Ensure required data directories exist."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    return processed_dir

def load_assistments_dataset(split: str = 'train', streaming: bool = False) -> Optional[pd.DataFrame]:
    """
    Load ASSISTments dataset from HuggingFace.

    Args:
        split: Dataset split to load ('train', 'test', 'validation')
        streaming: If True, stream the dataset instead of loading fully into memory

    Returns:
        DataFrame with ASSISTments data or None if not available
    """
    try:
        # Try the main ASSISTments dataset
        dataset_name = 'mercer/assistments2017'
        logger.info(f"Attempting to load dataset: {dataset_name}")

        if streaming:
            ds = load_dataset(dataset_name, split=split, streaming=True)
            # Convert to list for schema inspection if needed, but iterate for processing
            # For schema check, we need to peek at a few rows
            sample = next(iter(ds))
            df = pd.DataFrame([sample])
            # If we need more data, we'd iterate and accumulate, but for schema check this suffices
            logger.info(f"Streamed sample from {dataset_name}: {list(sample.keys())}")
        else:
            ds = load_dataset(dataset_name, split=split)
            df = ds.to_pandas()
            logger.info(f"Loaded {len(df)} rows from {dataset_name}")

        return df

    except Exception as e:
        logger.warning(f"Failed to load {dataset_name}: {e}")
        return None

def load_oulad_dataset(split: str = 'train', streaming: bool = False) -> Optional[pd.DataFrame]:
    """
    Load OULAD (Open University Learning Analytics Dataset) from HuggingFace.

    Args:
        split: Dataset split to load
        streaming: If True, stream the dataset

    Returns:
        DataFrame with OULAD data or None if not available
    """
    try:
        dataset_name = 'oulearn/oulad'
        logger.info(f"Attempting to load dataset: {dataset_name}")

        if streaming:
            ds = load_dataset(dataset_name, split=split, streaming=True)
            sample = next(iter(ds))
            df = pd.DataFrame([sample])
            logger.info(f"Streamed sample from {dataset_name}: {list(sample.keys())}")
        else:
            ds = load_dataset(dataset_name, split=split)
            df = ds.to_pandas()
            logger.info(f"Loaded {len(df)} rows from {dataset_name}")

        return df

    except Exception as e:
        logger.warning(f"Failed to load {dataset_name}: {e}")
        return None

def find_latency_feature(df: pd.DataFrame) -> Optional[str]:
    """
    Find a latency feature in the DataFrame by checking known column names.

    Args:
        df: DataFrame to check

    Returns:
        Name of the latency feature column or None
    """
    columns = set(df.columns)

    # Check direct matches
    for feature in LATENCY_FEATURES:
        if feature in columns:
            logger.info(f"Found latency feature: {feature}")
            return feature

    # Check for timestamp pairs that can be derived
    for start_col, end_col in TIMESTAMP_PAIRS:
        if start_col in columns and end_col in columns:
            logger.info(f"Found timestamp pair for derivation: {start_col}, {end_col}")
            return f"{start_col}_to_{end_col}"  # Marker for derivation

    return None

def find_error_feature(df: pd.DataFrame) -> Optional[str]:
    """
    Find an error/correctness feature in the DataFrame.

    Args:
        df: DataFrame to check

    Returns:
        Name of the error feature column or None
    """
    columns = set(df.columns)

    for feature in ERROR_FEATURES:
        if feature in columns:
            logger.info(f"Found error feature: {feature}")
            return feature

    return None

def find_hint_feature(df: pd.DataFrame) -> Optional[str]:
    """
    Find a hint feature in the DataFrame.

    Args:
        df: DataFrame to check

    Returns:
        Name of the hint feature column or None
    """
    columns = set(df.columns)

    for feature in HINT_FEATURES:
        if feature in columns:
            logger.info(f"Found hint feature: {feature}")
            return feature

    return None

def verify_features(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """
    Verify the presence of required semantic features in the dataset.

    Args:
        df: DataFrame to verify
        dataset_name: Name of the dataset for logging

    Returns:
        Dictionary with verification results

    Raises:
        ValueError: If required latency features are missing
    """
    logger.info(f"Verifying features for {dataset_name}")

    result = {
        'dataset': dataset_name,
        'rows': len(df),
        'columns': list(df.columns),
        'latency_feature': None,
        'error_feature': None,
        'hint_feature': None,
        'valid': False
    }

    # Check for latency features (CRITICAL)
    latency_feature = find_latency_feature(df)
    if latency_feature:
        result['latency_feature'] = latency_feature
    else:
        error_msg = (
            f"Schema Missing: Required latency features not found in {dataset_name}. "
            f"Checked: {', '.join(LATENCY_FEATURES)}. "
            f"Columns present: {list(df.columns)}. "
            f"Cannot proceed."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check for error features (Optional but recommended)
    error_feature = find_error_feature(df)
    result['error_feature'] = error_feature

    # Check for hint features (Optional but recommended)
    hint_feature = find_hint_feature(df)
    result['hint_feature'] = hint_feature

    # If we have latency, we consider the dataset valid for our purposes
    result['valid'] = True
    logger.info(f"Verification complete for {dataset_name}: {result['valid']}")

    return result

def derive_latency(df: pd.DataFrame, latency_feature: str) -> pd.DataFrame:
    """
    Derive latency from timestamp pairs if needed.

    Args:
        df: Input DataFrame
        latency_feature: Name of the latency feature (may be a derived marker)

    Returns:
        DataFrame with derived 'latency' column if applicable
    """
    if latency_feature.endswith('_to_'):
        # This is a derived feature marker
        parts = latency_feature.split('_to_')
        if len(parts) == 2:
            start_col = parts[0]
            end_col = parts[1]
            if start_col in df.columns and end_col in df.columns:
                try:
                    # Ensure columns are numeric or datetime
                    if pd.api.types.is_datetime64_any_dtype(df[start_col]) and \
                       pd.api.types.is_datetime64_any_dtype(df[end_col]):
                        df['latency'] = (df[end_col] - df[start_col]).dt.total_seconds()
                    else:
                        # Assume numeric difference
                        df['latency'] = df[end_col] - df[start_col]
                    logger.info(f"Derived latency from {start_col} and {end_col}")
                except Exception as e:
                    logger.warning(f"Failed to derive latency: {e}")
    return df

def save_dataset(df: pd.DataFrame, filename: str, output_dir: Path) -> Path:
    """
    Save dataset to disk.

    Args:
        df: DataFrame to save
        filename: Output filename
        output_dir: Output directory

    Returns:
        Path to saved file
    """
    output_path = output_dir / filename
    df.to_csv(output_path, index=False)
    logger.info(f"Saved dataset to {output_path}")
    return output_path

def load_and_verify_datasets(streaming: bool = False) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load and verify both ASSISTments and OULAD datasets.

    Args:
        streaming: If True, stream datasets to save memory

    Returns:
        Tuple of (assistments_df, oulad_df) - may be None if loading failed
    """
    assistments_df = None
    oulad_df = None

    # Try ASSISTments first
    assistments_df = load_assistments_dataset(streaming=streaming)
    if assistments_df is not None:
        try:
            verify_features(assistments_df, "ASSISTments")
            # Derive latency if needed
            latency_feat = find_latency_feature(assistments_df)
            if latency_feat:
                assistments_df = derive_latency(assistments_df, latency_feat)
        except ValueError as e:
            logger.error(f"ASSISTments verification failed: {e}")
            assistments_df = None

    # Try OULAD
    oulad_df = load_oulad_dataset(streaming=streaming)
    if oulad_df is not None:
        try:
            verify_features(oulad_df, "OULAD")
            # Derive latency if needed
            latency_feat = find_latency_feature(oulad_df)
            if latency_feat:
                oulad_df = derive_latency(oulad_df, latency_feat)
        except ValueError as e:
            logger.error(f"OULAD verification failed: {e}")
            oulad_df = None

    if assistments_df is None and oulad_df is None:
        raise RuntimeError(
            "Failed to load and verify any dataset. "
            "Both ASSISTments and OULAD failed verification or loading."
        )

    return assistments_df, oulad_df

def validate_golden_set(filepath: Path) -> bool:
    """
    Validate the presence and basic structure of the golden set.

    Args:
        filepath: Path to the golden set CSV

    Returns:
        True if valid, False otherwise
    """
    if not filepath.exists():
        logger.error(f"Golden set file not found: {filepath}")
        return False

    try:
        df = pd.read_csv(filepath)
        if 'expert_load_score' not in df.columns:
            logger.error("Golden set missing 'expert_load_score' column")
            return False

        if len(df) < 50:
            logger.warning(f"Golden set has only {len(df)} rows (recommended >= 50)")

        logger.info(f"Golden set validated: {len(df)} rows")
        return True
    except Exception as e:
        logger.error(f"Error reading golden set: {e}")
        return False

def main():
    """Main entry point for data loading and verification."""
    setup_logging()
    logger.info("Starting data loading and verification process")

    output_dir = ensure_directories()

    try:
        assistments_df, oulad_df = load_and_verify_datasets(streaming=True)

        # Save valid datasets
        if assistments_df is not None:
            save_dataset(assistments_df, 'assistments_raw.csv', output_dir)
        if oulad_df is not None:
            save_dataset(oulad_df, 'oulad_raw.csv', output_dir)

        logger.info("Data loading and verification completed successfully")

        # Validate golden set if it exists
        golden_set_path = output_dir / 'golden_set.csv'
        if golden_set_path.exists():
            validate_golden_set(golden_set_path)

    except Exception as e:
        logger.error(f"Data loading process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()