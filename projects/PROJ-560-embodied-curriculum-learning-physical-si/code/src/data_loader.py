import csv
import json
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd

try:
    from .synthetic_gen import SyntheticDataGenerator
    from .logging_config import write_skipped_record_jsonl
except ImportError:
    import synthetic_gen
    import logging_config
    from synthetic_gen import SyntheticDataGenerator
    from logging_config import write_skipped_record_jsonl

logger = logging.getLogger(__name__)

def log_skipped_record(reason: str, dataset_source: str, timestamp: str = None):
    """Log a skipped record to derivation logs."""
    if timestamp is None:
        import datetime
        timestamp = datetime.datetime.now().isoformat()
    record = {
        "timestamp": timestamp,
        "reason": reason,
        "dataset_source": dataset_source
    }
    log_path = Path("data/derivation_logs/skipped_records.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_skipped_record_jsonl(record, str(log_path))

def handle_synthetic_fallback_failure(dataset_source: str):
    """Handle failure of synthetic fallback generation."""
    error_msg = "Primary research question cannot be answered: missing instruction_type and synthetic generation failed"
    logger.error(error_msg)
    log_skipped_record("synthetic_gen_failed", dataset_source)
    raise SystemExit(1)

def load_public_dataset(input_path: str) -> Optional[pd.DataFrame]:
    """Load and validate public dataset."""
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        return None

    try:
        if path.suffix == '.csv':
            df = pd.read_csv(path)
        elif path.suffix == '.json':
            df = pd.read_json(path)
        else:
            logger.error(f"Unsupported file format: {path.suffix}")
            return None
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return None

    required_cols = ['pre_test_score', 'post_test_score', 'instruction_type']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        return df # Return anyway for fallback logic to handle

    return df

def generate_synthetic_fallback(n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float) -> Optional[pd.DataFrame]:
    """Generate synthetic data as fallback."""
    try:
        generator = SyntheticDataGenerator()
        df = generator.generate(n, seed, mean_diff_embodied, mean_diff_static)
        return df
    except Exception as e:
        logger.error(f"Synthetic generation failed: {e}")
        return None

def calculate_gain_scores(df: pd.DataFrame) -> pd.Series:
    """Calculate gain scores, logging skipped records."""
    if 'pre_test_score' not in df.columns or 'post_test_score' not in df.columns:
        logger.error("Missing pre/post test scores for gain calculation")
        return pd.Series(dtype=float)

    gain = df['post_test_score'] - df['pre_test_score']
    # Log missing values
    missing = gain.isna().sum()
    if missing > 0:
        log_skipped_record("missing_gain_data", "current_dataset")
    return gain

def write_processed_data(df: pd.DataFrame, output_path: str):
    """Write processed data to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Processed data written to {output_path}")

def load_public_dataset_with_fallback(input_path: str, n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float) -> Optional[pd.DataFrame]:
    """
    Load public dataset. If instruction_type is missing, generate synthetic fallback.
    """
    df = load_public_dataset(input_path)

    if df is None:
        # If file doesn't exist, try synthetic
        synthetic_df = generate_synthetic_fallback(n, seed, mean_diff_embodied, mean_diff_static)
        if synthetic_df is None:
            handle_synthetic_fallback_failure(input_path)
        return synthetic_df

    # Check for instruction_type
    if 'instruction_type' not in df.columns:
        logger.warning("instruction_type missing in public data. Generating synthetic fallback.")
        synthetic_df = generate_synthetic_fallback(n, seed, mean_diff_embodied, mean_diff_static)
        if synthetic_df is None:
            handle_synthetic_fallback_failure(input_path)
        
        # Save fallback
        fallback_path = "data/processed/validated_fallback.csv"
        write_processed_data(synthetic_df, fallback_path)
        return synthetic_df

    return df

def main():
    pass
