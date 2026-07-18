import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Import project configuration
from code.config.settings import get_config, DatasetPaths
from code.utils.logging_config import get_logger

# Constants
MIN_SEED_POSTS = 3
REASON_CODE_INSUFFICIENT = "SEED_INSUFFICIENT"
EXCLUSIONS_LOG_NAME = "exclusions.log"

# Initialize logger
logger = get_logger(__name__)

def load_downloaded_data(data_dir: Path) -> pd.DataFrame:
    """
    Load the raw downloaded data from JSONL or CSV files in the data directory.
    Expects a merged dataset with columns: thread_id, comment_id, parent_id, author, timestamp, text.
    """
    raw_dir = data_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    # Look for JSONL files (common output from download.py)
    jsonl_files = list(raw_dir.glob("*.jsonl"))
    if not jsonl_files:
        # Fallback to CSV
        csv_files = list(raw_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No data files found in {raw_dir}")
        df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
    else:
        dfs = []
        for f in jsonl_files:
            dfs.append(pd.read_json(f, lines=True))
        df = pd.concat(dfs, ignore_index=True)

    # Ensure required columns exist
    required_cols = ['thread_id', 'comment_id', 'parent_id', 'author', 'timestamp', 'text']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")

    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    logger.info(f"Loaded {len(df)} comments from {len(jsonl_files) + len(csv_files)} files.")
    return df

def extract_seed_posts(df: pd.DataFrame, n_seed_posts: int = MIN_SEED_POSTS) -> pd.DataFrame:
    """
    Extract the first N top-level posts (comments with parent_id == thread_id or specific marker)
    for each thread. Returns a dataframe with only the seed posts.
    """
    # Identify top-level posts. In Reddit data, often parent_id == thread_id or parent_id is null/None
    # We assume top-level posts are those where parent_id equals thread_id or is a specific root marker.
    # If the schema uses 'parent_id' == 'thread_id' for top-level, we filter that.
    # If the schema uses None/NaN for top-level, we handle that.
    
    # Strategy: Group by thread_id. For each group, sort by timestamp. Take the first N.
    # We assume the first N comments in a thread (chronologically) are the seed posts.
    
    if df.empty:
        return df.head(0)

    # Sort by thread_id and timestamp to ensure order
    df_sorted = df.sort_values(by=['thread_id', 'timestamp'])
    
    # Group by thread and take first N
    seed_posts = df_sorted.groupby('thread_id').head(n_seed_posts).reset_index(drop=True)
    
    logger.info(f"Extracted {len(seed_posts)} seed posts from {seed_posts['thread_id'].nunique()} threads.")
    return seed_posts

def flag_insufficient_seeds(df: pd.DataFrame, n_seed_posts: int = MIN_SEED_POSTS) -> pd.DataFrame:
    """
    Identify threads that have fewer than N top-level posts.
    Returns a DataFrame of threads that FAILED the seed post requirement.
    """
    if df.empty:
        return pd.DataFrame(columns=['thread_id', 'reason_code', 'comment_count', 'timestamp'])

    # Count comments per thread
    thread_counts = df.groupby('thread_id').size().reset_index(name='comment_count')
    
    # Filter threads with fewer than required seed posts
    insufficient = thread_counts[thread_counts['comment_count'] < n_seed_posts]
    
    if not insufficient.empty:
        insufficient['reason_code'] = REASON_CODE_INSUFFICIENT
        # Get a representative timestamp for the thread (e.g., the first comment)
        first_comments = df.sort_values('timestamp').groupby('thread_id').first().reset_index()
        insufficient = insufficient.merge(first_comments[['thread_id', 'timestamp']], on='thread_id')
        # Select and order columns
        insufficient = insufficient[['thread_id', 'reason_code', 'comment_count', 'timestamp']]
    
    logger.info(f"Flagged {len(insufficient)} threads as insufficient seeds.")
    return insufficient

def log_exclusions(insufficient_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Log the excluded threads to a file named exclusions.log in the processed directory.
    Format: JSON lines (one thread per line) or a structured text log.
    """
    if insufficient_df.empty:
        logger.info("No threads to exclude.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / EXCLUSIONS_LOG_NAME
    
    # Use append mode or overwrite? For a single run, overwrite is safer for idempotency,
    # but append is better for incremental runs. We'll append with a run header.
    timestamp = datetime.now().isoformat()
    
    with open(log_path, 'a') as f:
        f.write(f"\n--- Exclusion Run: {timestamp} ---\n")
        for _, row in insufficient_df.iterrows():
            log_entry = {
                "thread_id": row['thread_id'],
                "reason_code": row['reason_code'],
                "comment_count": int(row['comment_count']),
                "timestamp": str(row['timestamp'])
            }
            f.write(json.dumps(log_entry) + "\n")
    
    logger.info(f"Logged {len(insufficient_df)} exclusions to {log_path}")

def validate_metadata_completeness(df: pd.DataFrame) -> float:
    """
    Validate that metadata (timestamp, author, comment ID) is complete for >= 95% of rows.
    Returns the completeness percentage.
    """
    if df.empty:
        return 100.0

    required_cols = ['thread_id', 'comment_id', 'author', 'timestamp']
    # Check for non-null values
    completeness = df[required_cols].notna().all(axis=1).mean()
    percentage = completeness * 100

    logger.info(f"Metadata completeness: {percentage:.2f}%")
    if percentage < 95.0:
        logger.warning(f"Metadata completeness ({percentage:.2f}%) is below 95% threshold.")
    
    return percentage

def run_extraction(input_dir: Path, output_dir: Path, n_seed_posts: int = MIN_SEED_POSTS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main pipeline for data extraction:
    1. Load raw data.
    2. Flag threads with insufficient seed posts.
    3. Log exclusions.
    4. Extract seed posts for valid threads.
    5. Validate metadata completeness.
    
    Returns: (seed_posts_df, exclusions_df)
    """
    logger.info(f"Starting extraction pipeline. Input: {input_dir}, Output: {output_dir}")
    
    # 1. Load Data
    df = load_downloaded_data(input_dir)
    
    # 2. Flag Insufficient
    exclusions_df = flag_insufficient_seeds(df, n_seed_posts)
    
    # 3. Log Exclusions
    log_exclusions(exclusions_df, output_dir)
    
    # 4. Extract Seed Posts (only for threads that passed, i.e., not in exclusions)
    valid_threads = df[~df['thread_id'].isin(exclusions_df['thread_id'])]
    seed_posts_df = extract_seed_posts(valid_threads, n_seed_posts)
    
    # 5. Validate Metadata
    completeness = validate_metadata_completeness(seed_posts_df)
    
    logger.info(f"Extraction complete. Seed posts: {len(seed_posts_df)}, Exclusions: {len(exclusions_df)}")
    return seed_posts_df, exclusions_df

def main():
    """
    Entry point for the extraction script.
    Reads configuration from environment or default paths.
    """
    config = get_config()
    input_dir = config.data_paths.raw
    output_dir = config.data_paths.processed
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        seed_posts, exclusions = run_extraction(input_dir, output_dir)
        
        # Save extracted seed posts to processed data
        output_file = output_dir / "seed_posts.csv"
        seed_posts.to_csv(output_file, index=False)
        logger.info(f"Saved extracted seed posts to {output_file}")
        
        # If exclusions exist, they are already logged to exclusions.log
        if not exclusions.empty:
            logger.warning(f"Excluded {len(exclusions)} threads due to insufficient seeds.")
        
    except Exception as e:
        logger.error(f"Extraction pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()