"""
Data download module for fetching Reddit thread data.
Implements a strict "fail-loud" policy: no synthetic fallbacks.
"""

import os
import sys
import json
import time
import logging
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path (assumes code/data/ is the current directory structure)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

def ensure_directories():
    """Ensure all required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def log_download_attempt(thread_id: str, origin_type: str, success: bool, message: str = ""):
    """Log download attempt to data/processed/download_attempts.log."""
    log_path = DATA_PROCESSED_DIR / "download_attempts.log"
    entry = {
        "timestamp": time.time(),
        "thread_id": thread_id,
        "origin_type": origin_type,
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

def check_memory_usage():
    """Check memory usage and raise if too high (for streaming safety)."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        if mem_info.rss > 6 * 1024 * 1024 * 1024:  # 6GB
            raise RuntimeError(f"Memory usage exceeded 6GB: {mem_info.rss / (1024**3):.2f} GB")
    except ImportError:
        logger.warning("psutil not installed; skipping memory check.")

def fetch_from_pushshift(subreddit: str, size: int = 1000) -> Optional[List[Dict]]:
    """
    Fetch data from Pushshift API.
    Returns None if fetch fails.
    """
    url = f"https://api.pushshift.io/reddit/search/subreddit/{subreddit}"
    params = {
        "size": min(size, 1000),  # Pushshift max is 1000
        "sort": "desc"
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return data["data"]
            else:
                logger.warning(f"Pushshift returned no data for {subreddit}")
                return None
        else:
            logger.warning(f"Pushshift failed with status {response.status_code} for {subreddit}")
            return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Pushshift request failed for {subreddit}: {e}")
        return None

def fetch_from_reddit_api(subreddit: str, size: int = 1000) -> Optional[List[Dict]]:
    """
    Fetch data from Reddit Official API (OAuth).
    Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT env vars.
    Returns None if credentials missing or fetch fails.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "llmXive_research/1.0")

    if not client_id or not client_secret:
        logger.warning("Reddit API credentials not found in config. Skipping Reddit API.")
        return None

    try:
        # OAuth token
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        data = {"grant_type": "client_credentials"}
        token_response = requests.post("https://www.reddit.com/api/v1/access_token",
                                       auth=auth, data=data, timeout=30)
        token_response.raise_for_status()
        token = token_response.json()["access_token"]

        headers = {"Authorization": f"bearer {token}", "User-Agent": user_agent}
        url = f"https://oauth.reddit.com/r/{subreddit}/hot"
        params = {"limit": min(size, 1000)}

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "data" in data and "children" in data["data"]:
            return [child["data"] for child in data["data"]["children"]]
        else:
            logger.warning(f"Reddit API returned no data for {subreddit}")
            return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Reddit API request failed for {subreddit}: {e}")
        return None

def fetch_from_internet_archive(subreddit: str, size: int = 1000) -> Optional[List[Dict]]:
    """
    Fallback to Internet Archive/Common Crawl.
    Currently not fully implemented; returns None.
    """
    logger.warning("Internet Archive fallback is not fully implemented for Reddit data.")
    return None

def download_data(subreddit: str, output_file: Path):
    """
    Download data for a given subreddit using available sources.
    Implements strict fail-loud policy: raises RuntimeError if all sources fail.
    """
    ensure_directories()

    sources = [
        ("Pushshift API", fetch_from_pushshift),
        ("Reddit API", fetch_from_reddit_api),
        ("Internet Archive", fetch_from_internet_archive)
    ]

    all_threads = []
    data_retrieved = False

    for source_name, fetch_func in sources:
        logger.info(f"Attempting {source_name}: {fetch_func.__name__}")
        try:
            data = fetch_func(subreddit)
            if data:
                all_threads.extend(data)
                data_retrieved = True
                logger.info(f"Successfully retrieved {len(data)} threads from {source_name}")
                # Log successful fetches
                for thread in data:
                    log_download_attempt(
                        thread_id=thread.get("id", "unknown"),
                        origin_type=source_name,
                        success=True
                    )
                break  # Stop after first successful source
            else:
                log_download_attempt(
                    thread_id="batch",
                    origin_type=source_name,
                    success=False,
                    message="No data returned"
                )
        except Exception as e:
            logger.warning(f"{source_name} failed with exception: {e}")
            log_download_attempt(
                thread_id="batch",
                origin_type=source_name,
                success=False,
                message=str(e)
            )

    if not data_retrieved:
        error_msg = (
            f"CRITICAL FAILURE: Could not retrieve any data for subreddit '{subreddit}' "
            f"from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed "
            f"without real data. Please check network connectivity, API credentials, or source availability."
        )
        logger.error(error_msg)
        # Strict fail-loud: raise RuntimeError
        raise RuntimeError(error_msg)

    # Write data to output file
    with open(output_file, "w") as f:
        for thread in all_threads:
            f.write(json.dumps(thread) + "\n")

    logger.info(f"Wrote {len(all_threads)} threads to {output_file}")

    # Compute and log checksum
    checksum = compute_sha256(output_file)
    logger.info(f"Checksum for {output_file}: {checksum}")

    # Record checksum in state
    state_file = STATE_DIR / f"{os.path.basename(PROJECT_ROOT)}.yaml"
    if not state_file.exists():
        state_file.write_text("artifact_hashes: {}\n")

    # Simple YAML update (in production, use a proper YAML library)
    content = state_file.read_text()
    if "artifact_hashes:" not in content:
        content += "artifact_hashes:\n"
    content += f"  {output_file.name}: {checksum}\n"
    state_file.write_text(content)

def validate_origin_types(raw_file: Path):
    """
    Verify that origin_type log is present and accurate.
    """
    log_file = DATA_PROCESSED_DIR / "download_attempts.log"
    if not log_file.exists():
        raise FileNotFoundError(f"Download log not found: {log_file}")

    raw_data = []
    with open(raw_file) as f:
        for line in f:
            raw_data.append(json.loads(line))

    log_entries = []
    with open(log_file) as f:
        for line in f:
            log_entries.append(json.loads(line))

    # Simple validation: check that every thread in raw_data has a corresponding log entry
    raw_ids = {thread["id"] for thread in raw_data}
    logged_ids = {entry["thread_id"] for entry in log_entries if entry["thread_id"] != "batch"}

    if not raw_ids.issubset(logged_ids):
        missing = raw_ids - logged_ids
        logger.warning(f"Some thread IDs missing from log: {missing}")
    else:
        logger.info("Origin type log validation passed.")

def main():
    """Main entry point for data download."""
    import argparse

    parser = argparse.ArgumentParser(description="Download Reddit thread data.")
    parser.add_argument("--source", action="append", required=True,
                        help="Subreddit(s) to fetch data from (e.g., --source AskScience)")
    args = parser.parse_args()

    for subreddit in args.source:
        logger.info(f"Processing subreddit: {subreddit}")
        output_file = DATA_RAW_DIR / f"reddit_{subreddit}.jsonl"
        download_data(subreddit, output_file)

        # Validate origin types if file exists
        if output_file.exists():
            validate_origin_types(output_file)

    logger.info("Data download completed.")

if __name__ == "__main__":
    main()
