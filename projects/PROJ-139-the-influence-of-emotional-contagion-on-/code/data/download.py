import os
import sys
import json
import time
import logging
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

# Import config to ensure paths are initialized
from config.settings import get_config, Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories(config: Config):
    """Ensure all required directories exist."""
    config.raw_dir.mkdir(parents=True, exist_ok=True)
    config.processed_dir.mkdir(parents=True, exist_ok=True)
    config.state_dir.mkdir(parents=True, exist_ok=True)

def log_download_attempt(config: Config, thread_id: str, origin_type: str, success: bool, message: str = ""):
    """Log download attempt to data/processed/download_attempts.log."""
    log_path = config.processed_dir / "download_attempts.log"
    entry = {
        "thread_id": thread_id,
        "origin_type": origin_type,
        "success": success,
        "timestamp": time.time(),
        "message": message
    }
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_memory_usage():
    """Check if memory usage is within limits (placeholder for T081)."""
    # T081 handles detailed memory monitoring with psutil.
    # This is a placeholder to satisfy the interface if called early.
    pass

def fetch_from_pushshift(subreddit: str, limit: int = 1000) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch data from Pushshift API.
    Note: Pushshift API has been deprecated/unreliable. We attempt it but expect failure.
    """
    url = "https://api.pushshift.io/reddit/search/subreddit/"
    params = {
        "subreddit": subreddit,
        "size": min(limit, 1000),
        "sort": "desc",
        "sort_type": "desc"
    }
    
    logger.info(f"Attempting Pushshift API: {url}")
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                logger.info(f"Pushshift returned {len(data['data'])} items.")
                return data["data"]
            else:
                logger.warning("Pushshift response missing 'data' key.")
                return None
        else:
            logger.warning(f"Pushshift failed with status {response.status_code}.")
            return None
    except Exception as e:
        logger.warning(f"Pushshift request failed: {e}")
        return None

def fetch_from_reddit_api(subreddit: str, limit: int = 1000) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch data from Reddit Official API (OAuth).
    Requires credentials in config.
    """
    config = get_config()
    if not config.api_keys.reddit_client_id or not config.api_keys.reddit_client_secret:
        logger.warning("Reddit API credentials not found in config. Skipping Reddit API.")
        return None

    # Simplified OAuth flow for demonstration (real implementation requires token refresh)
    # In a real scenario, we would implement the full OAuth2 flow.
    # For this task, we simulate the fetch or return None if not fully configured.
    logger.info("Reddit API credentials present, but full OAuth flow not implemented in this snippet.")
    logger.warning("Reddit API access requires full OAuth implementation. Skipping for now.")
    return None

def fetch_from_internet_archive(subreddit: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch data from Internet Archive / Common Crawl.
    Placeholder for T008 Fallback 2.
    """
    logger.warning("Internet Archive fallback is not fully implemented for Reddit data.")
    return None

def download_data(subreddit: str, output_file: Path, log_file: Path):
    """
    Main function to download data for a subreddit.
    Tries sources in order: Pushshift -> Reddit API -> Internet Archive.
    Fails loudly if all fail.
    """
    config = get_config()
    ensure_directories(config)
    
    logger.info(f"Processing subreddit: {subreddit}")
    data_sources = [
        ("Pushshift", lambda: fetch_from_pushshift(subreddit)),
        ("Reddit API", lambda: fetch_from_reddit_api(subreddit)),
        ("Internet Archive", lambda: fetch_from_internet_archive(subreddit))
    ]
    
    all_threads = []
    success = False
    used_source = None

    for source_name, fetch_func in data_sources:
        logger.info(f"Attempting source: {source_name}")
        data = fetch_func()
        
        if data:
            all_threads.extend(data)
            success = True
            used_source = source_name
            logger.info(f"Successfully fetched data from {source_name}.")
            break
        else:
            logger.warning(f"Failed to fetch data from {source_name}.")

    if not success:
        error_msg = f"CRITICAL FAILURE: Could not retrieve any data for subreddit '{subreddit}' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Write raw data
    logger.info(f"Writing {len(all_threads)} threads to {output_file}")
    with open(output_file, 'w') as f:
        for thread in all_threads:
            # Ensure origin_type is recorded
            thread['origin_type'] = used_source
            f.write(json.dumps(thread) + '\n')

    # Compute checksum
    checksum = compute_sha256(output_file)
    logger.info(f"Checksum for {output_file}: {checksum}")

    # Log attempts (simplified: log the overall success for the subreddit)
    # In a real scenario, we would log per-thread attempts if we had them.
    # Here we log the successful fetch for the batch.
    log_download_attempt(config, f"subreddit_{subreddit}", used_source, True, f"Fetched {len(all_threads)} threads")

    return len(all_threads)

def validate_origin_types(config: Config):
    """Validate that origin_type is present in the downloaded data."""
    raw_file = config.raw_dir / "reddit_threads.jsonl"
    if not raw_file.exists():
        logger.error("Raw data file not found. Cannot validate origin types.")
        return False

    count = 0
    valid_count = 0
    with open(raw_file, 'r') as f:
        for line in f:
            count += 1
            try:
                data = json.loads(line)
                if 'origin_type' in data:
                    valid_count += 1
                else:
                    logger.warning(f"Thread {count} missing origin_type")
            except json.JSONDecodeError:
                logger.warning(f"Thread {count} is not valid JSON")

    if count == 0:
        logger.warning("No threads found in raw file.")
        return False

    ratio = valid_count / count
    if ratio < 1.0:
        logger.warning(f"Origin type validation failed: {ratio:.2%} of threads have origin_type")
        return False
    
    logger.info(f"Origin type validation passed: 100% of threads have origin_type")
    return True

def main():
    parser = argparse.ArgumentParser(description="Download Reddit data for analysis.")
    parser.add_argument("--source", type=str, default="askScience", help="Subreddit name to download.")
    parser.add_argument("--limit", type=int, default=1000, help="Max number of threads to fetch.")
    args = parser.parse_args()

    config = get_config()
    ensure_directories(config)
    
    output_file = config.raw_dir / "reddit_threads.jsonl"
    log_file = config.processed_dir / "download_attempts.log"

    try:
        count = download_data(args.source, output_file, log_file)
        logger.info(f"Download complete. Fetched {count} threads.")
        
        # Validate
        if validate_origin_types(config):
            logger.info("Validation successful.")
        else:
            logger.warning("Validation incomplete.")
            
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
