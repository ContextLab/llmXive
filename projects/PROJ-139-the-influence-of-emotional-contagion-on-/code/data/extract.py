"""
Extract module for processing Reddit threads.
Handles seed post extraction, metadata validation, and exclusion logging.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config.settings import get_config

# Configure logging
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required output directories exist."""
    config = get_config()
    dirs = [
        config.paths.processed_data,
        config.state_dir
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_downloaded_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Load raw Reddit thread data from JSONL file.
    
    Args:
        input_path: Path to the JSONL file containing thread data.
        
    Returns:
        List of dictionaries, each representing a thread.
    """
    threads = []
    logger.info(f"Loading data from {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                thread = json.loads(line)
                threads.append(thread)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
    
    logger.info(f"Loaded {len(threads)} threads from {input_path}")
    return threads

def load_exclusion_log(exclusion_log_path: str) -> set:
    """
    Load existing exclusion log to identify threads to skip.
    
    Args:
        exclusion_log_path: Path to the exclusion log file.
        
    Returns:
        Set of thread IDs that should be excluded.
    """
    excluded_ids = set()
    if not os.path.exists(exclusion_log_path):
        logger.info(f"No existing exclusion log found at {exclusion_log_path}")
        return excluded_ids
    
    with open(exclusion_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if 'thread_id' in entry:
                    excluded_ids.add(entry['thread_id'])
            except json.JSONDecodeError:
                # Fallback: assume line is just thread_id
                excluded_ids.add(line)
    
    logger.info(f"Loaded {len(excluded_ids)} excluded thread IDs from log")
    return excluded_ids

def extract_seed_posts(thread: Dict[str, Any], seed_count: int = 3) -> List[Dict[str, Any]]:
    """
    Extract the first N top-level posts (seed posts) from a thread.
    
    Args:
        thread: Dictionary containing thread data with 'comments' or 'top_level_posts'.
        seed_count: Number of seed posts to extract (default 3).
        
    Returns:
        List of seed post dictionaries.
    """
    # Try to get top-level posts from different possible keys
    top_level_posts = thread.get('top_level_posts', [])
    if not top_level_posts:
        top_level_posts = thread.get('comments', [])
    
    # Filter to only top-level posts (parent_id is None or thread_id)
    thread_id = thread.get('thread_id')
    seed_posts = []
    
    for post in top_level_posts:
        parent_id = post.get('parent_id')
        # Top-level posts have parent_id == thread_id or parent_id is None
        if parent_id == thread_id or parent_id is None:
            seed_posts.append(post)
            if len(seed_posts) >= seed_count:
                break
    
    return seed_posts

def count_top_level_posts(thread: Dict[str, Any]) -> int:
    """
    Count the number of top-level posts in a thread.
    
    Args:
        thread: Dictionary containing thread data.
        
    Returns:
        Number of top-level posts.
    """
    top_level_posts = thread.get('top_level_posts', [])
    if not top_level_posts:
        top_level_posts = thread.get('comments', [])
    
    thread_id = thread.get('thread_id')
    count = 0
    
    for post in top_level_posts:
        parent_id = post.get('parent_id')
        if parent_id == thread_id or parent_id is None:
            count += 1
    
    return count

def validate_metadata_completeness(threads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that required metadata fields are present for each thread.
    
    Args:
        threads: List of thread dictionaries.
        
    Returns:
        Dictionary with validation statistics.
    """
    required_fields = ['thread_id', 'timestamp', 'author', 'comment_id']
    stats = {
        'total_threads': len(threads),
        'complete_threads': 0,
        'incomplete_threads': 0,
        'missing_fields': {}
    }
    
    for thread in threads:
        missing = []
        for field in required_fields:
            if field not in thread or thread[field] is None:
                missing.append(field)
        
        if not missing:
            stats['complete_threads'] += 1
        else:
            stats['incomplete_threads'] += 1
            for field in missing:
                stats['missing_fields'][field] = stats['missing_fields'].get(field, 0) + 1
    
    completeness_ratio = stats['complete_threads'] / stats['total_threads'] if stats['total_threads'] > 0 else 0
    stats['completeness_ratio'] = completeness_ratio
    
    logger.info(f"Metadata completeness: {completeness_ratio:.2%} ({stats['complete_threads']}/{stats['total_threads']})")
    
    return stats

def save_validation_report(stats: Dict[str, Any], output_path: str):
    """
    Save validation report to JSON file.
    
    Args:
        stats: Validation statistics dictionary.
        output_path: Path to save the report.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved validation report to {output_path}")

def save_exclusions_log(exclusions: List[Dict[str, Any]], output_path: str):
    """
    Save exclusion log to JSONL file.
    
    Args:
        exclusions: List of exclusion entries.
        output_path: Path to save the log.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in exclusions:
            f.write(json.dumps(entry) + '\n')
    logger.info(f"Saved {len(exclusions)} exclusions to {output_path}")

def run_extraction(input_path: str, exclusion_log_path: str, output_path: str, min_seed_count: int = 3):
    """
    Main extraction pipeline: load data, apply exclusions, extract seed posts.
    
    Args:
        input_path: Path to raw data JSONL file.
        exclusion_log_path: Path to exclusion log file.
        output_path: Path to save extracted threads CSV.
        min_seed_count: Minimum number of seed posts required (default 3).
        
    Returns:
        Tuple of (extracted_threads, exclusions)
    """
    # Load data
    threads = load_downloaded_data(input_path)
    
    # Load existing exclusions
    existing_excluded = load_exclusion_log(exclusion_log_path)
    
    # Filter out already excluded threads
    threads = [t for t in threads if t.get('thread_id') not in existing_excluded]
    
    # Process threads and identify new exclusions
    extracted_threads = []
    new_exclusions = []
    
    for thread in threads:
        thread_id = thread.get('thread_id')
        top_level_count = count_top_level_posts(thread)
        
        if top_level_count < min_seed_count:
            # Thread doesn't have enough seed posts
            exclusion_entry = {
                'thread_id': thread_id,
                'reason_code': 'SEED_INSUFFICIENT',
                'top_level_count': top_level_count,
                'min_required': min_seed_count
            }
            new_exclusions.append(exclusion_entry)
        else:
            # Thread is valid, extract seed posts
            seed_posts = extract_seed_posts(thread, min_seed_count)
            
            # Create extracted thread record
            extracted_thread = {
                'thread_id': thread_id,
                'subreddit': thread.get('subreddit'),
                'title': thread.get('title'),
                'timestamp': thread.get('timestamp'),
                'author': thread.get('author'),
                'seed_posts': seed_posts,
                'seed_count': len(seed_posts),
                'reply_count': top_level_count - 1 if top_level_count > 0 else 0  # Exclude the OP
            }
            extracted_threads.append(extracted_thread)
    
    # Save exclusions
    if new_exclusions:
        save_exclusions_log(new_exclusions, exclusion_log_path)
        logger.info(f"Added {len(new_exclusions)} new exclusions to {exclusion_log_path}")
    
    # Save extracted threads
    if extracted_threads:
        df = pd.DataFrame(extracted_threads)
        # Flatten seed_posts for CSV storage
        df['seed_post_ids'] = df['seed_posts'].apply(lambda x: [p.get('id') for p in x])
        df['seed_post_authors'] = df['seed_posts'].apply(lambda x: [p.get('author') for p in x])
        df['seed_post_timestamps'] = df['seed_posts'].apply(lambda x: [p.get('timestamp') for p in x])
        df = df.drop(columns=['seed_posts'])
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(extracted_threads)} extracted threads to {output_path}")
    
    return extracted_threads, new_exclusions

def save_output(data: List[Dict[str, Any]], output_path: str):
    """
    Save extracted data to CSV file.
    
    Args:
        data: List of extracted thread dictionaries.
        output_path: Path to save the CSV file.
    """
    if not data:
        logger.warning("No data to save")
        return
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(data)} records to {output_path}")

def main():
    """Main entry point for the extraction script."""
    config = get_config()
    
    # Ensure directories exist
    ensure_directories()
    
    # Define paths
    input_path = config.paths.raw_data / 'reddit_threads_english.jsonl'
    exclusion_log_path = config.paths.processed_data / 'exclusions_seed.log'
    output_path = config.paths.processed_data / 'threads_with_seeds.csv'
    
    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Run extraction
    logger.info("Starting extraction pipeline...")
    extracted_threads, new_exclusions = run_extraction(
        input_path=str(input_path),
        exclusion_log_path=str(exclusion_log_path),
        output_path=str(output_path),
        min_seed_count=3
    )
    
    logger.info(f"Extraction complete: {len(extracted_threads)} threads extracted, {len(new_exclusions)} excluded")

if __name__ == '__main__':
    main()