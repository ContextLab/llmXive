import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import hashlib

from code.config.settings import get_config, DatasetPaths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_downloaded_data(file_path: str) -> pd.DataFrame:
    """
    Load the downloaded raw data from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file containing raw thread data.
        
    Returns:
        DataFrame containing the raw data.
    """
    logger.info(f"Loading data from {file_path}")
    df = pd.read_json(file_path, lines=True)
    logger.info(f"Loaded {len(df)} records")
    return df

def flag_insufficient_seeds(df: pd.DataFrame, min_seeds: int = 3) -> pd.DataFrame:
    """
    Flag threads with fewer than min_seeds top-level posts.
    
    Args:
        df: DataFrame containing thread data.
        min_seeds: Minimum number of top-level posts required.
        
    Returns:
        DataFrame with an additional column 'seed_status' indicating
        'SUFFICIENT' or 'INSUFFICIENT'.
    """
    logger.info(f"Flagging threads with fewer than {min_seeds} seeds")
    
    # Assuming 'top_level_count' or similar column exists, or calculate from data
    # If the data structure is nested, we might need to explode or aggregate first.
    # For this implementation, we assume a column 'top_level_count' exists or 
    # we count occurrences of parent_id == None or similar.
    
    if 'top_level_count' not in df.columns:
        # Fallback: if we have a list of replies, count them? 
        # Or if we have a 'parent_id' column, count nulls.
        # Given the context of T010, we assume the data has been pre-processed 
        # to have a count or we count based on structure.
        # Let's assume a generic approach: if 'replies' is a list, len(replies)
        # But usually, for threads, we count top-level comments.
        # Let's assume the input df has a column 'num_top_level_posts' or we derive it.
        # Since T010 is about flagging, we assume the data has the necessary structure.
        # If not, we might need to aggregate.
        # For now, let's assume 'top_level_count' is available or we count null parent_ids.
        if 'parent_id' in df.columns:
            # Count top-level (parent_id is None or 't3_...')
            # This might be per-row, so we need groupby.
            # But T010 says "Flag threads", implying we are at thread level.
            # Let's assume the input is already aggregated at thread level with 'top_level_count'.
            # If not, we raise an error or try to infer.
            logger.warning("Column 'top_level_count' not found. Assuming 'num_top_level_posts' or similar.")
            if 'num_top_level_posts' in df.columns:
                df = df.rename(columns={'num_top_level_posts': 'top_level_count'})
            else:
                # If we have a list of top-level posts, we can count.
                # Assuming a column 'top_level_posts' which is a list.
                if 'top_level_posts' in df.columns:
                    df['top_level_count'] = df['top_level_posts'].apply(len)
                else:
                    logger.error("Could not determine top-level post count. Expected 'top_level_count', 'num_top_level_posts', or 'top_level_posts'.")
                    raise ValueError("Missing required column for top-level post count.")
    
    df['seed_status'] = df['top_level_count'].apply(
        lambda x: 'SUFFICIENT' if x >= min_seeds else 'INSUFFICIENT'
    )
    
    logger.info(f"Flagged {len(df[df['seed_status'] == 'INSUFFICIENT'])} threads as insufficient")
    return df

def log_exclusions(df: pd.DataFrame, exclusion_log_path: str, reason_code: str = "SEED_INSUFFICIENT"):
    """
    Log excluded threads to a file.
    
    Args:
        df: DataFrame containing thread data with 'seed_status'.
        exclusion_log_path: Path to the exclusion log file.
        reason_code: The reason code for exclusion.
    """
    logger.info(f"Logging exclusions to {exclusion_log_path}")
    
    excluded = df[df['seed_status'] == 'INSUFFICIENT']
    
    # Ensure the directory exists
    Path(exclusion_log_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(exclusion_log_path, 'w') as f:
        # Header
        f.write("thread_id,reason_code,origin_type\n")
        
        for _, row in excluded.iterrows():
            thread_id = row.get('thread_id', 'UNKNOWN')
            origin_type = row.get('origin_type', 'UNKNOWN')
            f.write(f"{thread_id},{reason_code},{origin_type}\n")
    
    logger.info(f"Logged {len(excluded)} exclusions")

def extract_seed_posts(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """
    Extract the first N top-level posts as seed posts for each thread.
    
    Args:
        df: DataFrame containing thread data.
        n: Number of seed posts to extract.
        
    Returns:
        DataFrame containing only the seed posts, with thread_id and seed_index.
    """
    logger.info(f"Extracting first {n} seed posts per thread")
    
    # Assuming the data is structured such that we can group by thread_id and take the first n
    # This might require the data to be sorted by timestamp or similar.
    # For this implementation, we assume the data is already sorted or we sort by timestamp.
    
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')
    
    # Group by thread_id and take the first n rows
    seed_posts = df.groupby('thread_id').head(n)
    
    # Add a column to indicate which seed post this is (0, 1, 2, ...)
    seed_posts['seed_index'] = seed_posts.groupby('thread_id').cumcount()
    
    logger.info(f"Extracted {len(seed_posts)} seed posts")
    return seed_posts

def validate_metadata_completeness(df: pd.DataFrame, required_fields: List[str] = None) -> Dict[str, Any]:
    """
    Validate that metadata (timestamp, author, comment ID) is complete for ≥95% of extracted threads.
    
    Args:
        df: DataFrame containing thread data.
        required_fields: List of required metadata fields. Defaults to ['timestamp', 'author', 'comment_id'].
        
    Returns:
        Dictionary with validation results including completeness percentage and status.
    """
    if required_fields is None:
        required_fields = ['timestamp', 'author', 'comment_id']
    
    logger.info(f"Validating metadata completeness for fields: {required_fields}")
    
    # Check if all required fields are present in the DataFrame
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        logger.error(f"Missing required fields in DataFrame: {missing_fields}")
        return {
            'status': 'FAIL',
            'message': f"Missing required fields: {missing_fields}",
            'completeness_percentage': 0.0,
            'threshold': 0.95
        }
    
    # Count rows with all required fields present (non-null)
    total_rows = len(df)
    if total_rows == 0:
        logger.warning("DataFrame is empty. Cannot compute completeness.")
        return {
            'status': 'FAIL',
            'message': "DataFrame is empty.",
            'completeness_percentage': 0.0,
            'threshold': 0.95
        }
    
    complete_rows = df[required_fields].dropna().shape[0]
    completeness_percentage = (complete_rows / total_rows) * 100
    
    status = 'PASS' if completeness_percentage >= 95.0 else 'FAIL'
    
    result = {
        'status': status,
        'message': f"Metadata completeness: {completeness_percentage:.2f}% (Threshold: 95.0%)",
        'completeness_percentage': completeness_percentage,
        'threshold': 95.0,
        'total_rows': total_rows,
        'complete_rows': complete_rows,
        'missing_rows': total_rows - complete_rows
    }
    
    logger.info(f"Metadata validation result: {status} - {completeness_percentage:.2f}%")
    return result

def run_extraction(
    input_path: str,
    output_seeds_path: str,
    exclusion_log_path: str,
    min_seeds: int = 3,
    n_seed_posts: int = 3
) -> Dict[str, Any]:
    """
    Run the full extraction pipeline: load, flag, log exclusions, extract seeds.
    
    Args:
        input_path: Path to the raw data JSONL file.
        output_seeds_path: Path to save the extracted seed posts CSV.
        exclusion_log_path: Path to save the exclusion log.
        min_seeds: Minimum number of seeds required.
        n_seed_posts: Number of seed posts to extract per thread.
        
    Returns:
        Dictionary with extraction results and metadata.
    """
    logger.info("Starting extraction pipeline")
    
    # Load data
    df = load_downloaded_data(input_path)
    
    # Flag insufficient seeds
    df = flag_insufficient_seeds(df, min_seeds)
    
    # Log exclusions
    log_exclusions(df, exclusion_log_path)
    
    # Extract seed posts (only from sufficient threads? Or all? 
    # The task says "extract the first N=3 top-level posts as seed posts from the *filtered* dataset"
    # But T009 says "from the *filtered* dataset (valid threads only)". 
    # T011 is about metadata completeness of *extracted* threads.
    # Let's assume we extract from threads that passed the seed check (SUFFICIENT).
    sufficient_df = df[df['seed_status'] == 'SUFFICIENT']
    
    seed_posts_df = extract_seed_posts(sufficient_df, n_seed_posts)
    
    # Save seed posts
    Path(output_seeds_path).parent.mkdir(parents=True, exist_ok=True)
    seed_posts_df.to_csv(output_seeds_path, index=False)
    logger.info(f"Saved {len(seed_posts_df)} seed posts to {output_seeds_path}")
    
    # Validate metadata completeness on the seed posts (or the filtered dataset?)
    # T011 says "ensure metadata ... is complete for ≥95% of extracted threads".
    # "Extracted threads" likely refers to the threads from which we extracted seeds.
    # So we validate on `sufficient_df` or `seed_posts_df`? 
    # Since seed_posts_df is a subset, we should validate on the threads that were considered for extraction.
    # Let's validate on `sufficient_df` (the threads that passed the seed check).
    # But `sufficient_df` might be at the thread level, while `seed_posts_df` is at the comment level.
    # The metadata (timestamp, author, comment_id) is per comment.
    # So we should validate on `seed_posts_df` (the actual extracted comments).
    
    validation_result = validate_metadata_completeness(seed_posts_df)
    
    # Save validation result to a JSON file? The task doesn't specify an output file for this validation,
    # but it's good practice. However, T011 only says "Implement validation logic".
    # Let's assume we log it and return it.
    
    return {
        'total_threads_loaded': len(df),
        'threads_sufficient': len(sufficient_df),
        'threads_insufficient': len(df) - len(sufficient_df),
        'seed_posts_extracted': len(seed_posts_df),
        'metadata_validation': validation_result,
        'output_seeds_path': output_seeds_path,
        'exclusion_log_path': exclusion_log_path
    }

def main():
    """
    Main entry point for the extraction script.
    """
    config = get_config()
    paths = config.paths
    
    # Define paths
    input_file = paths.raw_data_dir / "reddit_threads.jsonl"
    output_seeds_file = paths.processed_data_dir / "threads_with_seeds.csv"
    exclusion_log_file = paths.processed_data_dir / "exclusions_seed.log"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return
    
    results = run_extraction(
        input_path=str(input_file),
        output_seeds_path=str(output_seeds_file),
        exclusion_log_path=str(exclusion_log_file),
        min_seeds=3,
        n_seed_posts=3
    )
    
    logger.info("Extraction pipeline completed")
    logger.info(f"Results: {json.dumps(results, indent=2, default=str)}")

if __name__ == "__main__":
    main()
