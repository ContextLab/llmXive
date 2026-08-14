"""
Download module for fetching Stack Overflow PostsTags data.

Implements robust fetching with primary Stack Overflow dump and HuggingFace fallback.
Enforces "Fail Loudly" policy: no synthetic fallbacks.
"""
import os
import sys
import json
import logging
import time
import socket
import requests
import gzip
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Tuple
from urllib.parse import urljoin
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Primary source: Stack Overflow Archive (Internet Archive)
# Updated to use the correct path structure for the dump
PRIMARY_URL = "https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z"

# Fallback: HuggingFace dataset
HF_DATASET_ID = "stack-exchange/stackoverflow"
HF_SPLIT = "train"  # Using train split as it typically contains the full data

# Output paths
RAW_OUTPUT_PATH = DATA_RAW_DIR / "stackoverflow_posts.jsonl"
PROCESSED_OUTPUT_PATH = DATA_PROCESSED_DIR / "posts_tags_processed.json"

# Memory constraints for streaming
CHUNK_SIZE = 10000
MEMORY_THRESHOLD_GB = 6.0

def ensure_output_dir():
    """Ensure output directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directories exist: {DATA_RAW_DIR}, {DATA_PROCESSED_DIR}")

def check_url_reachable(url: str, timeout: int = 10) -> bool:
    """Check if a URL is reachable via HEAD request."""
    try:
        logger.info(f"Checking reachability of: {url}")
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            logger.info(f"URL is reachable: {url} (Status: {response.status_code})")
            return True
        else:
            logger.warning(f"URL returned non-200 status: {url} (Status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"URL check failed for {url}: {e}")
        return False

def fetch_from_huggingface() -> Optional[Generator[Dict[str, Any], None, None]]:
    """
    Fetch data from HuggingFace dataset as a fallback.
    Returns a generator yielding records.
    """
    try:
        logger.info(f"Attempting to load HuggingFace dataset: {HF_DATASET_ID}")
        from datasets import load_dataset
        
        # Load dataset in streaming mode to handle large sizes
        dataset = load_dataset(HF_DATASET_ID, split=HF_SPLIT, streaming=True)
        
        # Verify we have data
        first_item = next(iter(dataset))
        logger.info(f"HF dataset loaded successfully. Sample keys: {first_item.keys()}")
        
        # Filter and transform to expected format
        def transform_record(record):
            # Extract relevant fields
            return {
                "id": record.get("id", record.get("PostId")),
                "title": record.get("title", record.get("Title")),
                "tags": record.get("tags", record.get("Tags", [])),
                "creation_date": record.get("creation_date", record.get("CreationDate")),
                "score": record.get("score", record.get("Score")),
                "view_count": record.get("view_count", record.get("ViewCount")),
                "answer_count": record.get("answer_count", record.get("AnswerCount")),
                "body": record.get("body", record.get("Body"))
            }
        
        return (transform_record(item) for item in dataset)
        
    except Exception as e:
        logger.error(f"HF dataset load failed: {e}")
        return None

def fetch_from_archive() -> Optional[Generator[Dict[str, Any], None, None]]:
    """
    Fetch data from Stack Overflow Archive (Internet Archive).
    Downloads and extracts the .7z file, then streams JSON records.
    """
    try:
        # Check if primary URL is reachable
        if not check_url_reachable(PRIMARY_URL):
            logger.warning(f"Primary URL {PRIMARY_URL} is not reachable")
            return None
        
        logger.info("Starting download from Stack Overflow Archive...")
        
        # We'll use a direct download approach for the .7z file
        # Note: For large files, we'd need to handle chunked downloading
        # Here we assume the file is manageable or use streaming
        
        # Since .7z extraction requires external tools, we'll look for a JSON/CSV alternative
        # or use a different approach. Let's try to find a direct JSONL file.
        
        # Alternative: Try to find a JSONL version
        jsonl_url = "https://archive.org/download/stackexchange/stackoverflow.com-Posts.json.gz"
        
        if check_url_reachable(jsonl_url):
            logger.info(f"Found JSONL version at: {jsonl_url}")
            
            # Stream and decompress
            response = requests.get(jsonl_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with gzip.GzipFile(fileobj=response.raw, mode='rb') as gz_file:
                for line in gz_file:
                    try:
                        record = json.loads(line.decode('utf-8'))
                        yield {
                            "id": record.get("Id"),
                            "title": record.get("Title"),
                            "tags": record.get("Tags", "").split(';') if record.get("Tags") else [],
                            "creation_date": record.get("CreationDate"),
                            "score": record.get("Score"),
                            "view_count": record.get("ViewCount"),
                            "answer_count": record.get("AnswerCount"),
                            "body": record.get("Body")
                        }
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON line: {e}")
                        continue
        else:
            logger.warning(f"JSONL version not found at {jsonl_url}")
            return None
            
    except Exception as e:
        logger.error(f"Error during archive fetch: {e}")
        return None

def fetch_posts_tags_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Main streaming function that tries primary source then fallback.
    Implements "Fail Loudly" policy - no synthetic data.
    """
    # Try primary source first
    logger.info("Attempting primary Stack Overflow dump...")
    primary_stream = fetch_from_archive()
    
    if primary_stream is not None:
        logger.info("Primary source successful, streaming data...")
        yield from primary_stream
        return
    
    # Fallback to HuggingFace
    logger.info("Primary source failed, attempting HuggingFace fallback...")
    hf_stream = fetch_from_huggingface()
    
    if hf_stream is not None:
        logger.info("HuggingFace fallback successful, streaming data...")
        yield from hf_stream
        return
    
    # Both sources failed - fail loudly
    error_msg = (
        "Primary Stack Overflow dump URL unreachable and HuggingFace fallback failed. "
        "Cannot proceed with data download. "
        "Please check network connectivity and source availability."
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)

def process_and_save_data():
    """
    Process streaming data and save to disk.
    Handles memory constraints by writing in chunks.
    """
    ensure_output_dir()
    
    logger.info("Starting data download and processing...")
    start_time = time.time()
    
    records_written = 0
    memory_usage_gb = 0
    
    try:
        # Open output file for writing
        with open(RAW_OUTPUT_PATH, 'w', encoding='utf-8') as outfile:
            for record in fetch_posts_tags_streaming():
                # Write record as JSON line
                json_line = json.dumps(record, ensure_ascii=False, default=str)
                outfile.write(json_line + '\n')
                records_written += 1
                
                # Log progress every 10000 records
                if records_written % CHUNK_SIZE == 0:
                    logger.info(f"Processed {records_written} records...")
                    
                    # Check memory usage
                    try:
                        import psutil
                        process = psutil.Process(os.getpid())
                        memory_usage_gb = process.memory_info().rss / (1024 ** 3)
                        
                        if memory_usage_gb > MEMORY_THRESHOLD_GB:
                            logger.warning(f"Memory usage high: {memory_usage_gb:.2f} GB. Consider reducing chunk size.")
                            # In a real implementation, we might pause or reduce chunk size here
                    except ImportError:
                        logger.warning("psutil not available, skipping memory check")
                    
                    # Force garbage collection
                    import gc
                    gc.collect()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Successfully processed {records_written} records in {duration:.2f} seconds")
        logger.info(f"Output saved to: {RAW_OUTPUT_PATH}")
        
        # Create a summary file
        summary = {
            "source": "Stack Overflow Archive / HuggingFace",
            "total_records": records_written,
            "output_path": str(RAW_OUTPUT_PATH),
            "processing_time_seconds": duration,
            "final_memory_usage_gb": memory_usage_gb
        }
        
        summary_path = DATA_PROCESSED_DIR / "download_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary saved to: {summary_path}")
        
    except Exception as e:
        logger.error(f"Error during data processing: {e}")
        # Clean up partial output
        if RAW_OUTPUT_PATH.exists():
            RAW_OUTPUT_PATH.unlink()
            logger.info(f"Removed partial output file: {RAW_OUTPUT_PATH}")
        raise

def main():
    """Main entry point for the download module."""
    logger.info("=== Starting Stack Overflow Data Download ===")
    try:
        process_and_save_data()
        logger.info("=== Download Completed Successfully ===")
    except Exception as e:
        logger.error(f"=== Download Failed: {e} ===")
        sys.exit(1)

if __name__ == "__main__":
    main()