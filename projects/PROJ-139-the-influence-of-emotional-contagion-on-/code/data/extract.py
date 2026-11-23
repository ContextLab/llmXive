import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config.settings import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist based on config."""
    config = get_config()
    # Fallback to standard paths if config attributes are missing (tolerant design)
    base_dir = getattr(config, 'base_dir', Path('.'))
    processed_dir = base_dir / 'data' / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured at {processed_dir}")

def load_downloaded_data(raw_file_path: str) -> List[Dict[str, Any]]:
    """
    Load raw JSONL data from a file.
    Args:
        raw_file_path: Path to the raw JSONL file.
    Returns:
        List of dictionaries, each representing a thread.
    """
    data = []
    path = Path(raw_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file_path}")
    
    logger.info(f"Loading data from {raw_file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
    logger.info(f"Loaded {len(data)} threads from {raw_file_path}")
    return data

def load_exclusion_log(exclusion_log_path: str) -> set:
    """
    Load existing exclusion log to avoid re-processing excluded threads.
    Args:
        exclusion_log_path: Path to the exclusion log file.
    Returns:
        Set of excluded thread IDs.
    """
    excluded_ids = set()
    path = Path(exclusion_log_path)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if parts:
                    excluded_ids.add(parts[0])
        logger.info(f"Loaded {len(excluded_ids)} existing exclusions from {exclusion_log_path}")
    return excluded_ids

def count_top_level_posts(thread: Dict[str, Any]) -> int:
    """
    Count the number of top-level posts in a thread.
    Assumes 'comments' key contains a list of top-level comments.
    Args:
        thread: A dictionary representing a thread.
    Returns:
        Integer count of top-level posts.
    """
    comments = thread.get('comments', [])
    if isinstance(comments, list):
        return len(comments)
    return 0

def extract_seed_posts(thread: Dict[str, Any], n: int = 3) -> List[Dict[str, Any]]:
    """
    Extract the first N top-level posts as seed posts.
    Args:
        thread: A dictionary representing a thread.
        n: Number of seed posts to extract.
    Returns:
        List of seed post dictionaries.
    """
    comments = thread.get('comments', [])
    if isinstance(comments, list):
        return comments[:n]
    return []

def validate_metadata_completeness(thread: Dict[str, Any]) -> bool:
    """
    Validate that essential metadata is present.
    Args:
        thread: A dictionary representing a thread.
    Returns:
        True if metadata is complete, False otherwise.
    """
    required_fields = ['thread_id', 'subreddit', 'timestamp', 'author_id']
    for field in required_fields:
        if field not in thread or thread[field] is None:
            return False
    return True

def save_exclusions_log(exclusions: List[Dict[str, Any]], output_path: str):
    """
    Save the exclusion log to a file.
    Args:
        exclusions: List of dictionaries containing exclusion details.
        output_path: Path to the output log file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for item in exclusions:
            line = f"{item['thread_id']}|{item['reason']}\n"
            f.write(line)
    logger.info(f"Saved {len(exclusions)} exclusions to {output_path}")

def save_validation_report(report: Dict[str, Any], output_path: str):
    """
    Save a validation report to a JSON file.
    Args:
        report: Dictionary containing validation results.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved validation report to {output_path}")

def save_output(df: pd.DataFrame, output_path: str):
    """
    Save a DataFrame to a CSV file.
    Args:
        df: The DataFrame to save.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved DataFrame to {output_path} with {len(df)} rows")

def run_extraction(input_file: str, exclusion_log_path: str, output_file: str, exclusion_output_path: str):
    """
    Main extraction logic:
    1. Load raw data.
    2. Identify threads with <3 top-level posts.
    3. Write excluded threads to exclusion log.
    4. Filter excluded threads and process remaining ones.
    5. Extract seed posts and save results.
    Args:
        input_file: Path to raw input JSONL.
        exclusion_log_path: Path to save exclusion log.
        output_file: Path to save final extracted CSV.
        exclusion_output_path: Path to save exclusion log (alias).
    """
    ensure_directories()
    
    # Load existing exclusions if any
    existing_excluded = load_exclusion_log(exclusion_log_path)
    
    # Load raw data
    threads = load_downloaded_data(input_file)
    
    new_exclusions = []
    processed_threads = []
    
    for thread in threads:
        thread_id = thread.get('thread_id')
        
        # Skip if already excluded
        if thread_id in existing_excluded:
            continue

        # Count top-level posts
        top_level_count = count_top_level_posts(thread)
        
        if top_level_count < 3:
            new_exclusions.append({
                'thread_id': thread_id,
                'reason': 'SEED_INSUFFICIENT',
                'top_level_count': top_level_count
            })
        else:
            # Extract seed posts
            seed_posts = extract_seed_posts(thread, n=3)
            processed_threads.append({
                'thread_id': thread_id,
                'subreddit': thread.get('subreddit'),
                'timestamp': thread.get('timestamp'),
                'author_id': thread.get('author_id'),
                'top_level_count': top_level_count,
                'seed_posts': json.dumps(seed_posts),
                'metadata_complete': validate_metadata_completeness(thread)
            })
    
    # Save new exclusions
    if new_exclusions:
        save_exclusions_log(new_exclusions, exclusion_output_path)
        logger.info(f"Identified {len(new_exclusions)} threads with insufficient seeds.")
    else:
        # Ensure file exists even if empty
        Path(exclusion_output_path).touch()
    
    # Save processed threads
    if processed_threads:
        df = pd.DataFrame(processed_threads)
        save_output(df, output_file)
    else:
        # Create empty CSV with headers
        pd.DataFrame(columns=['thread_id', 'subreddit', 'timestamp', 'author_id', 'top_level_count', 'seed_posts', 'metadata_complete']).to_csv(output_file, index=False)
        logger.warning("No threads passed the seed count filter.")

def main():
    """
    Entry point for the extraction script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract seed posts and generate exclusion log.')
    parser.add_argument('--input', type=str, required=True, help='Path to raw input JSONL file.')
    parser.add_argument('--output', type=str, required=True, help='Path to save processed CSV.')
    parser.add_argument('--exclusions', type=str, required=True, help='Path to save exclusion log.')
    
    args = parser.parse_args()
    
    try:
        run_extraction(
            input_file=args.input,
            exclusion_log_path=args.exclusions,
            output_file=args.output,
            exclusion_output_path=args.exclusions
        )
        logger.info("Extraction completed successfully.")
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()