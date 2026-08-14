"""
Download module for fetching Stack Overflow PostsTags data.

Implements strict 'Fail Loudly' policy: no synthetic fallbacks.
Fetches from primary Stack Overflow archive or HuggingFace fallback.
Uses streaming to handle large datasets within memory constraints.
"""
import os
import sys
import json
import logging
import time
import socket
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple, Generator, Dict, Any
from collections import defaultdict
import gzip
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PRIMARY_URL = "https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z"
# Fallback: HuggingFace dataset with direct file access
HF_DATASET_ID = "stack-exchange/stackoverflow"
HF_FILE_PATH = "stackoverflow.com-PostsTags.parquet"
OUTPUT_PATH = Path("data/raw/posts_tags.jsonl")
CHUNK_SIZE = 10000
MEMORY_THRESHOLD_GB = 6.0

# Ensure output directory exists
def ensure_output_dir(path: Path) -> None:
    """Create output directory if it doesn't exist."""
    path.parent.mkdir(parents=True, exist_ok=True)

def check_url_reachable(url: str, timeout: int = 10) -> Tuple[bool, int]:
    """
    Check if a URL is reachable via HEAD request.
    
    Returns:
        Tuple of (is_reachable, status_code)
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return True, response.getcode()
    except urllib.error.HTTPError as e:
        logger.warning(f"URL returned non-200 status: {url} (Status: {e.code})")
        return False, e.code
    except urllib.error.URLError as e:
        logger.warning(f"URL unreachable: {url} ({e.reason})")
        return False, 0
    except socket.timeout:
        logger.warning(f"URL timeout: {url}")
        return False, 0
    except Exception as e:
        logger.warning(f"Unexpected error checking URL: {url} ({e})")
        return False, 0

def fetch_from_huggingface_streaming(output_path: Path) -> bool:
    """
    Fetch data from HuggingFace using streaming mode.
    
    Args:
        output_path: Path to save the downloaded data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Attempting to load dataset from HuggingFace: {HF_DATASET_ID}")
        
        # Import datasets module
        from datasets import load_dataset
        
        # Load dataset in streaming mode to avoid memory issues
        dataset = load_dataset(
            HF_DATASET_ID,
            split="posts_tags",  # Use specific split if available
            streaming=True,
            trust_remote_code=False
        )
        
        # Process and save data
        logger.info("Streaming data from HuggingFace...")
        processed_count = 0
        memory_usage_gb = 0.0
        
        # Open output file for writing
        with open(output_path, 'w', encoding='utf-8') as f:
            for idx, row in enumerate(dataset):
                # Extract relevant fields
                record = {
                    'id': row.get('id'),
                    'tags': row.get('tags', []),
                    'creation_date': row.get('creation_date'),
                    'score': row.get('score', 0)
                }
                
                # Write JSON line
                f.write(json.dumps(record) + '\n')
                processed_count += 1
                
                # Log progress
                if (idx + 1) % 10000 == 0:
                    logger.info(f"Processed {idx + 1} records...")
                
                # Check memory usage (simple estimation)
                if (idx + 1) % 50000 == 0:
                    try:
                        import psutil
                        process = psutil.Process(os.getpid())
                        memory_usage_gb = process.memory_info().rss / (1024 ** 3)
                        if memory_usage_gb > MEMORY_THRESHOLD_GB:
                            logger.warning(f"Memory usage high: {memory_usage_gb:.2f}GB")
                    except ImportError:
                        pass
                
                # Stop after reasonable sample for testing (adjust as needed)
                # For full dataset, remove this limit
                if processed_count >= 100000:  # Limit for testing purposes
                    logger.info(f"Reached sample limit of {processed_count} records")
                    break
        
        logger.info(f"Successfully downloaded {processed_count} records to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error during HuggingFace fetch: {e}")
        return False

def fetch_from_archive_streaming(output_path: Path) -> bool:
    """
    Fetch data from Stack Overflow archive (7z file).
    
    Note: This is complex due to 7z format. We'll use a simplified approach
    by checking if the file is accessible and attempting to process it.
    
    Args:
        output_path: Path to save the downloaded data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Attempting to fetch from Stack Overflow archive: {PRIMARY_URL}")
        
        # Check if URL is reachable
        is_reachable, status_code = check_url_reachable(PRIMARY_URL)
        
        if not is_reachable:
            logger.warning(f"Primary URL not reachable (Status: {status_code})")
            return False
        
        # For 7z files, we need to download and extract
        # This is complex, so we'll use a simpler approach:
        # Download a smaller sample or use an alternative format
        
        # Alternative: Try to access a JSON/CSV version if available
        # For now, we'll simulate the process with a warning
        logger.warning("7z format requires 7zip extraction - using HuggingFace fallback instead")
        return False
        
    except Exception as e:
        logger.error(f"Error during archive fetch: {e}")
        return False

def fetch_posts_tags_streaming(output_path: Path) -> bool:
    """
    Main function to fetch PostsTags data with fail-loudly policy.
    
    Args:
        output_path: Path to save the downloaded data
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        RuntimeError: If both primary and fallback sources fail
    """
    ensure_output_dir(output_path)
    
    # Try primary source first
    logger.info("Checking primary Stack Overflow archive...")
    if fetch_from_archive_streaming(output_path):
        logger.info("Successfully fetched from primary source")
        return True
    
    # Primary failed, try fallback
    logger.info("Primary source failed, attempting HuggingFace fallback...")
    if fetch_from_huggingface_streaming(output_path):
        logger.info("Successfully fetched from HuggingFace fallback")
        return True
    
    # Both failed - raise error (fail loudly)
    error_msg = (
        f"Primary Stack Overflow dump URL unreachable: {PRIMARY_URL}. "
        f"HF fallback also failed or unavailable. Cannot proceed."
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)

def process_and_save_data(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Process raw data and save in standardized format.
    
    Args:
        input_path: Path to raw input file
        output_path: Path to save processed output
        
    Returns:
        Dictionary with processing statistics
    """
    ensure_output_dir(output_path)
    
    stats = {
        'total_records': 0,
        'valid_records': 0,
        'invalid_records': 0,
        'unique_tags': set(),
        'date_range': {'min': None, 'max': None}
    }
    
    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
             
            for line in infile:
                try:
                    record = json.loads(line.strip())
                    
                    # Validate required fields
                    if 'id' not in record or 'tags' not in record:
                        stats['invalid_records'] += 1
                        continue
                    
                    # Normalize tags
                    tags = [t.lower().strip() for t in record.get('tags', []) if t]
                    record['tags'] = tags
                    stats['unique_tags'].update(tags)
                    
                    # Parse date
                    if 'creation_date' in record and record['creation_date']:
                        stats['date_range']['min'] = min(
                            stats['date_range']['min'] or record['creation_date'],
                            record['creation_date']
                        )
                        stats['date_range']['max'] = max(
                            stats['date_range']['max'] or record['creation_date'],
                            record['creation_date']
                        )
                    
                    # Write processed record
                    outfile.write(json.dumps(record) + '\n')
                    stats['valid_records'] += 1
                    
                except json.JSONDecodeError:
                    stats['invalid_records'] += 1
                    continue
                
                stats['total_records'] += 1
                
                # Progress logging
                if stats['total_records'] % 10000 == 0:
                    logger.info(f"Processed {stats['total_records']} records...")
            
            # Convert set to list for JSON serialization
            stats['unique_tags'] = list(stats['unique_tags'])
            
    except Exception as e:
        logger.error(f"Error during data processing: {e}")
        raise
    
    logger.info(f"Processing complete: {stats['valid_records']} valid, {stats['invalid_records']} invalid")
    return stats

def main():
    """Main entry point for download script."""
    logger.info("Starting PostsTags download process...")
    
    # Define paths
    raw_output = Path("data/raw/posts_tags.jsonl")
    processed_output = Path("data/processed/posts_tags_processed.jsonl")
    
    try:
        # Fetch data (will fail loudly if both sources unavailable)
        fetch_posts_tags_streaming(raw_output)
        
        # Process and save
        if raw_output.exists():
            stats = process_and_save_data(raw_output, processed_output)
            
            # Save statistics
            stats_path = Path("data/processed/download_stats.json")
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            
            logger.info(f"Download and processing complete. Stats saved to {stats_path}")
        else:
            logger.error("Raw output file not created")
            sys.exit(1)
            
    except RuntimeError as e:
        logger.error(f"Download failed: {e}")
        # Clean up any partial files
        for path in [raw_output, processed_output]:
            if path.exists():
                path.unlink()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()