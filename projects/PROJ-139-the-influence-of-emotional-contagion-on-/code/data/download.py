"""
Reddit Data Download Module for PROJ-139.

Implements a strict "fail-loud" policy for data fetching.
Removes any fallback to synthetic/mock data. If all real sources fail,
a RuntimeError is raised immediately.
"""

import os
import sys
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests

# Ensure project root is in path for imports if running as script
if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PUSHSHIFT_BASE_URL = "https://api.pushshift.io/reddit/search/subreddit"
REDDIT_API_BASE = "https://oauth.reddit.com"
ARCHIVE_BASE = "https://archive.org/advancedsearch.php"

def ensure_directories() -> None:
    """Create necessary output directories."""
    config = get_config()
    Path(config.paths.raw_data).mkdir(parents=True, exist_ok=True)
    Path(config.paths.processed_data).mkdir(parents=True, exist_ok=True)
    Path(config.paths.state).mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def log_download_attempt(endpoint: str, status_code: int, success: bool, message: str = "") -> None:
    """Log a download attempt to the processed log file."""
    config = get_config()
    log_path = Path(config.paths.processed_data) / "download_attempts.log"
    
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "endpoint": endpoint,
        "status_code": status_code,
        "success": success,
        "message": message
    }
    
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_from_pushshift(subreddit: str, limit: int = 500) -> Tuple[Optional[List[Dict]], bool]:
    """
    Fetch data from Pushshift API.
    Returns (data, success_status).
    Raises RuntimeError if the API is unreachable or returns 404/500 without data.
    """
    url = f"{PUSHSHIFT_BASE_URL}/{subreddit}"
    params = {
        "limit": limit,
        "sort": "created_utc",
        "sort_type": "desc",
        "fields": "id,subreddit,created_utc,author,title,selftext,link_id,parent_id"
    }

    logger.info(f"Attempting Pushshift API: {url}")
    try:
        response = requests.get(url, params=params, timeout=30)
        status_code = response.status_code
        
        if status_code != 200:
            log_download_attempt(url, status_code, False, f"HTTP Error: {status_code}")
            logger.warning(f"Pushshift failed with status {status_code}.")
            return None, False

        data = response.json()
        if "data" not in data or not data["data"]:
            log_download_attempt(url, status_code, False, "No data returned in response.")
            logger.warning("Pushshift returned empty data.")
            return None, False

        # Normalize data if wrapped in 'hits' or similar
        records = data.get("data", [])
        log_download_attempt(url, status_code, True, f"Retrieved {len(records)} records.")
        logger.info(f"Pushshift success: {len(records)} records.")
        return records, True

    except requests.exceptions.RequestException as e:
        log_download_attempt(url, 0, False, f"Network error: {str(e)}")
        logger.warning(f"Pushshift network error: {e}")
        return None, False
    except json.JSONDecodeError as e:
        log_download_attempt(url, 0, False, f"JSON decode error: {str(e)}")
        logger.warning(f"Pushshift JSON error: {e}")
        return None, False

def fetch_from_reddit_api(subreddit: str, limit: int = 500) -> Tuple[Optional[List[Dict]], bool]:
    """
    Fetch data from Reddit Official API (OAuth).
    Returns (data, success_status).
    Requires valid credentials in environment variables.
    """
    config = get_config()
    client_id = config.api_keys.reddit_client_id
    client_secret = config.api_keys.reddit_client_secret
    user_agent = config.api_keys.reddit_user_agent

    if not all([client_id, client_secret, user_agent]):
        logger.warning("Reddit API credentials not found in config. Skipping Reddit API.")
        return None, False

    # OAuth flow for script (simplified for read-only)
    auth_url = "https://www.reddit.com/api/v1/access_token"
    auth = (client_id, client_secret)
    headers = {"User-Agent": user_agent}
    data = {"grant_type": "client_credentials"}

    try:
        logger.info("Attempting Reddit Official API (OAuth)...")
        auth_resp = requests.post(auth_url, auth=auth, data=data, headers=headers, timeout=10)
        
        if auth_resp.status_code != 200:
            log_download_attempt("Reddit OAuth", auth_resp.status_code, False, "OAuth failed.")
            logger.warning("Reddit OAuth failed.")
            return None, False

        token = auth_resp.json().get("access_token")
        if not token:
            log_download_attempt("Reddit OAuth", 0, False, "No token in response.")
            return None, False

        # Fetch subreddit data
        url = f"{REDDIT_API_BASE}/r/{subreddit}/new.json"
        params = {"limit": limit, "raw_json": 1}
        headers["Authorization"] = f"bearer {token}"

        resp = requests.get(url, params=params, headers=headers, timeout=30)
        status_code = resp.status_code

        if status_code != 200:
            log_download_attempt(url, status_code, False, f"HTTP Error: {status_code}")
            logger.warning(f"Reddit API failed with status {status_code}.")
            return None, False

        json_data = resp.json()
        children = json_data.get("data", {}).get("children", [])
        
        if not children:
            log_download_attempt(url, status_code, False, "No posts found.")
            return None, False

        # Normalize Reddit API structure to our schema
        records = []
        for child in children:
            d = child.get("data", {})
            records.append({
                "id": d.get("id"),
                "subreddit": d.get("subreddit"),
                "created_utc": d.get("created_utc"),
                "author": d.get("author"),
                "title": d.get("title"),
                "selftext": d.get("selftext", ""),
                "link_id": d.get("link_id"),
                "parent_id": d.get("parent_id"),
                "origin_type": "reddit_api"
            })

        log_download_attempt(url, status_code, True, f"Retrieved {len(records)} records.")
        logger.info(f"Reddit API success: {len(records)} records.")
        return records, True

    except requests.exceptions.RequestException as e:
        log_download_attempt("Reddit API", 0, False, f"Network error: {str(e)}")
        logger.warning(f"Reddit API network error: {e}")
        return None, False
    except json.JSONDecodeError as e:
        log_download_attempt("Reddit API", 0, False, f"JSON decode error: {str(e)}")
        logger.warning(f"Reddit API JSON error: {e}")
        return None, False

def fetch_from_internet_archive(subreddit: str, limit: int = 500) -> Tuple[Optional[List[Dict]], bool]:
    """
    Fetch data from Internet Archive (Common Crawl).
    This is a fallback for when APIs fail.
    Note: This implementation is a placeholder for the generic reference.
    Currently, it does not implement full Common Crawl parsing logic for Reddit.
    """
    logger.warning("Internet Archive fallback is not fully implemented for Reddit data.")
    # We do NOT simulate data here. We return failure to trigger the RuntimeError.
    return None, False

def download_data(subreddits: List[str], output_file: str) -> None:
    """
    Main download function implementing the strict fail-loud policy.
    
    1. Iterates through provided subreddits.
    2. Attempts Pushshift -> Reddit API -> Internet Archive.
    3. If ALL sources fail for a specific subreddit, raises RuntimeError.
    4. Does NOT generate synthetic data.
    """
    ensure_directories()
    config = get_config()
    output_path = Path(output_file)
    
    all_threads = []
    
    for subreddit in subreddits:
        logger.info(f"Processing subreddit: {subreddit}")
        source_found = False
        
        # Try Pushshift
        data, success = fetch_from_pushshift(subreddit)
        if success and data:
            all_threads.extend(data)
            source_found = True
        
        if not source_found:
            # Try Reddit API
            data, success = fetch_from_reddit_api(subreddit)
            if success and data:
                all_threads.extend(data)
                source_found = True
        
        if not source_found:
            # Try Internet Archive
            data, success = fetch_from_internet_archive(subreddit)
            if success and data:
                all_threads.extend(data)
                source_found = True
        
        if not source_found:
            error_msg = f"CRITICAL FAILURE: Could not retrieve any data for subreddit '{subreddit}' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    # Write to file
    logger.info(f"Writing {len(all_threads)} threads to {output_path}")
    with open(output_path, 'w') as f:
        for thread in all_threads:
            f.write(json.dumps(thread) + "\n")
    
    # Log checksum
    checksum = compute_sha256(output_path)
    logger.info(f"Checksum for {output_path}: {checksum}")
    
    # Update state
    state_file = Path(config.paths.state) / "artifact_hashes.yaml"
    # Simple append logic for state file (in a real scenario, use a proper YAML library)
    with open(state_file, "a") as sf:
        sf.write(f"- file: {output_path}\n  hash: {checksum}\n  timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def validate_origin_types(input_file: str, output_log: str) -> None:
    """
    Validates that origin_type is present in the downloaded data.
    Reads the raw file and logs the origin types found.
    """
    input_path = Path(input_file)
    log_path = Path(output_log)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    origin_counts = {}
    total_count = 0
    
    with open(input_path, 'r') as f:
        for line in f:
            try:
                thread = json.loads(line)
                origin = thread.get("origin_type", "unknown")
                origin_counts[origin] = origin_counts.get(origin, 0) + 1
                total_count += 1
            except json.JSONDecodeError:
                continue
    
    with open(log_path, 'w') as f:
        f.write(json.dumps({
            "total_records": total_count,
            "origin_counts": origin_counts
        }, indent=2))
    
    logger.info(f"Validation complete. Total: {total_count}, Origins: {origin_counts}")

def main():
    """Entry point for the download script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Reddit data for analysis.")
    parser.add_argument("--source", nargs="+", required=True, help="List of subreddits to fetch (e.g., --source askScience fdr)")
    args = parser.parse_args()
    
    config = get_config()
    output_file = str(Path(config.paths.raw_data) / "reddit_threads.jsonl")
    
    try:
        download_data(args.source, output_file)
        logger.info("Data download completed successfully.")
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
