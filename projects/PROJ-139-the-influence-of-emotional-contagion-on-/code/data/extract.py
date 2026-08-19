import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config.settings import get_config

logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    config = get_config()
    # Ensure state_dir exists for logging if needed, though we use data/processed here
    if hasattr(config, 'state_dir') and config.state_dir:
        config.state_dir.mkdir(parents=True, exist_ok=True)
    
    data_processed = Path('data/processed')
    data_processed.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured at {data_processed}")

def load_downloaded_data() -> List[Dict[str, Any]]:
    """Load raw Reddit threads from the downloaded JSONL file."""
    config = get_config()
    raw_file = Path('data/raw/reddit_threads.jsonl')
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}. Run download.py first.")
    
    threads = []
    with open(raw_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    threads.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line: {e}")
    return threads

def load_exclusion_log() -> List[str]:
    """Load existing exclusion log if it exists."""
    exclusion_file = Path('data/processed/exclusions_seed.log')
    if not exclusion_file.exists():
        return []
    
    excluded_ids = []
    with open(exclusion_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if parts:
                excluded_ids.append(parts[0])
    return excluded_ids

def count_top_level_posts(thread: Dict[str, Any]) -> int:
    """
    Count the number of top-level posts (comments with depth 0 or parent_id == None)
    in a thread.
    """
    comments = thread.get('comments', [])
    if not comments:
        return 0
    
    # Assuming comments are a list of dicts with 'depth' or 'parent_id'
    # In Reddit JSON structure, top-level comments usually have depth=0
    # or parent_id matching the submission ID (which we might not have directly here)
    # We will count comments where depth is 0 or parent_id is None
    count = 0
    for comment in comments:
        if comment.get('depth') == 0 or comment.get('parent_id') is None:
            count += 1
    return count

def extract_seed_posts(thread: Dict[str, Any], n: int = 3) -> List[Dict[str, Any]]:
    """
    Extract the first N top-level posts from a thread.
    """
    comments = thread.get('comments', [])
    top_level = []
    for comment in comments:
        if comment.get('depth') == 0 or comment.get('parent_id') is None:
            top_level.append(comment)
            if len(top_level) >= n:
                break
    return top_level

def validate_metadata_completeness(thread: Dict[str, Any]) -> bool:
    """
    Validate that essential metadata (timestamp, author, comment ID) is present.
    """
    required_fields = ['id', 'author', 'created_utc']
    comments = thread.get('comments', [])
    if not comments:
        return False
    
    complete_count = 0
    for comment in comments:
        if all(field in comment for field in required_fields):
            complete_count += 1
    
    # Require at least 95% completeness across comments in the thread
    if len(comments) == 0:
        return False
    return (complete_count / len(comments)) >= 0.95

def save_exclusions_log(excluded_threads: List[Dict[str, str]], output_path: str):
    """
    Save the list of excluded threads to a log file.
    Format: thread_id\treason_code
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in excluded_threads:
            thread_id = item.get('thread_id', 'UNKNOWN')
            reason = item.get('reason', 'UNKNOWN')
            f.write(f"{thread_id}\t{reason}\n")
    logger.info(f"Exclusion log written to {output_path}")

def save_validation_report(report: Dict[str, Any], output_path: str):
    """Save validation report to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {output_path}")

def save_output(data: List[Dict[str, Any]], output_path: str):
    """Save extracted data to CSV."""
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Output written to {output_path}")

def run_extraction():
    """
    Main extraction logic for T010:
    Identify threads with <3 top-level posts and write them to exclusions_seed.log.
    """
    ensure_directories()
    
    logger.info("Loading downloaded data...")
    threads = load_downloaded_data()
    logger.info(f"Loaded {len(threads)} threads.")
    
    excluded_threads = []
    processed_threads = []
    
    for thread in threads:
        thread_id = thread.get('id', 'UNKNOWN')
        top_level_count = count_top_level_posts(thread)
        
        if top_level_count < 3:
            excluded_threads.append({
                'thread_id': thread_id,
                'reason': 'SEED_INSUFFICIENT',
                'top_level_count': top_level_count
            })
            logger.debug(f"Excluded thread {thread_id}: insufficient seeds ({top_level_count})")
        else:
            processed_threads.append(thread)
    
    # Write exclusions log
    exclusion_log_path = 'data/processed/exclusions_seed.log'
    save_exclusions_log(excluded_threads, exclusion_log_path)
    
    logger.info(f"Extraction complete. {len(excluded_threads)} threads excluded, {len(processed_threads)} processed.")
    return excluded_threads, processed_threads

def main():
    """Entry point for T010 execution."""
    logging.basicConfig(level=logging.INFO)
    run_extraction()

if __name__ == '__main__':
    main()