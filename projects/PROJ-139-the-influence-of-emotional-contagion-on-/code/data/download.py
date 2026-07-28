import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOWNLOAD_LOG_PATH = PROCESSED_DIR / "download_attempts.log"

def ensure_directories():
    """Ensure the processed directory exists."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def log_download_attempt(endpoint: str, status_code: Optional[int], success: bool, error_msg: Optional[str] = None):
    """
    Logs the exact timestamp and HTTP status code for every API attempt.
    Appends a JSON line to data/processed/download_attempts.log.
    """
    ensure_directories()
    attempt = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": endpoint,
        "status_code": status_code,
        "success": success,
        "error": error_msg
    }
    
    with open(DOWNLOAD_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(attempt) + '\n')
    
    if success:
        logger.info(f"Download attempt successful: {endpoint} (Status: {status_code})")
    else:
        logger.warning(f"Download attempt failed: {endpoint} (Status: {status_code}, Error: {error_msg})")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_from_pushshift(subreddits: List[str], limit: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch data from Pushshift API.
    """
    results = []
    # Pushshift API endpoint for submissions
    url = "https://api.pushshift.io/reddit/search/submission/"
    
    for subreddit in subreddits:
        params = {
            "subreddit": subreddit,
            "size": min(limit, 100), # Pushshift max size per request
            "sort": "created_utc",
            "sort_type": "desc"
        }
        
        try:
            logger.info(f"Attempting Pushshift fetch for r/{subreddit}...")
            response = requests.get(url, params=params, timeout=30)
            status_code = response.status_code
            
            if status_code == 200:
                data = response.json()
                if 'data' in data:
                    results.extend(data['data'])
                    log_download_attempt(f"Pushshift/r/{subreddit}", status_code, True)
                else:
                    log_download_attempt(f"Pushshift/r/{subreddit}", status_code, False, "No 'data' key in response")
            else:
                log_download_attempt(f"Pushshift/r/{subreddit}", status_code, False, f"HTTP {status_code}")
        except requests.exceptions.RequestException as e:
            log_download_attempt(f"Pushshift/r/{subreddit}", None, False, str(e))
    
    return results

def fetch_from_reddit_api(subreddits: List[str], limit: int = 500, client_id: Optional[str] = None, client_secret: Optional[str] = None, user_agent: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch data from Reddit Official API (OAuth).
    Note: Requires valid credentials.
    """
    if not all([client_id, client_secret, user_agent]):
        logger.warning("Reddit API credentials missing. Skipping Reddit API fetch.")
        return []

    results = []
    auth_url = "https://www.reddit.com/api/v1/access_token"
    headers = {"User-Agent": user_agent}
    auth = (client_id, client_secret)
    
    try:
        logger.info("Requesting Reddit OAuth token...")
        auth_resp = requests.post(auth_url, headers=headers, auth=auth, data={"grant_type": "client_credentials"}, timeout=30)
        token = auth_resp.json().get("access_token")
        
        if not token:
            log_download_attempt("Reddit OAuth", auth_resp.status_code, False, "Token acquisition failed")
            return []
        
        log_download_attempt("Reddit OAuth", auth_resp.status_code, True)
        
        for subreddit in subreddits:
            url = f"https://oauth.reddit.com/r/{subreddit}/hot"
            params = {"limit": min(limit, 100)}
            headers["Authorization"] = f"Bearer {token}"
            
            try:
                logger.info(f"Fetching from Reddit r/{subreddit}...")
                resp = requests.get(url, params=params, headers=headers, timeout=30)
                status_code = resp.status_code
                
                if status_code == 200:
                    data = resp.json()
                    if 'data' in data and 'children' in data['data']:
                        # Transform Reddit API response to match expected structure
                        for child in data['data']['children']:
                            post = child['data']
                            results.append({
                                "id": post['id'],
                                "subreddit": post['subreddit'],
                                "title": post['title'],
                                "selftext": post['selftext'],
                                "created_utc": post['created_utc'],
                                "author": post['author'],
                                "upvote_ratio": post.get('upvote_ratio'),
                                "ups": post.get('ups'),
                                "downs": post.get('downs'),
                                "num_comments": post.get('num_comments')
                            })
                        log_download_attempt(f"Reddit/r/{subreddit}", status_code, True)
                    else:
                        log_download_attempt(f"Reddit/r/{subreddit}", status_code, False, "No data children")
                else:
                    log_download_attempt(f"Reddit/r/{subreddit}", status_code, False, f"HTTP {status_code}")
            except requests.exceptions.RequestException as e:
                log_download_attempt(f"Reddit/r/{subreddit}", None, False, str(e))
                
    except requests.exceptions.RequestException as e:
        log_download_attempt("Reddit OAuth", None, False, str(e))
    
    return results

def fetch_from_huggingface(dataset_name: str = "cardiffnlp/reddit-tweet-sentiment", split: str = "train", limit: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch data from HuggingFace datasets.
    """
    results = []
    try:
        logger.info(f"Attempting HuggingFace fetch: {dataset_name}...")
        from datasets import load_dataset
        
        ds = load_dataset(dataset_name, split=split, streaming=True)
        count = 0
        for item in ds:
            if count >= limit:
                break
            # Map HuggingFace fields to expected structure
            # Assuming typical structure: text, label, etc.
            results.append({
                "id": f"hf_{count}",
                "text": item.get("text", ""),
                "label": item.get("label", 0),
                "source": "huggingface",
                "created_utc": time.time() # Placeholder
            })
            count += 1
        
        log_download_attempt(f"HuggingFace/{dataset_name}", 200, True)
    except Exception as e:
        log_download_attempt(f"HuggingFace/{dataset_name}", None, False, str(e))
    
    return results

def fetch_from_internet_archive(subreddits: List[str], limit: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch data from Internet Archive (Wayback Machine) - fallback.
    Note: This is a complex fallback, often requires specific snapshots.
    For this implementation, we log the attempt and return empty if not feasible.
    """
    results = []
    for subreddit in subreddits:
        # Example archive URL structure (simplified)
        url = f"https://web.archive.org/cdx/search/cdx?url=reddit.com/r/{subreddit}/*&output=json&limit=1"
        try:
            logger.info(f"Attempting Internet Archive check for r/{subreddit}...")
            resp = requests.get(url, timeout=30)
            status_code = resp.status_code
            if status_code == 200:
                # If we get here, archives exist, but parsing them into structured posts is non-trivial
                # without a specific snapshot ID.
                log_download_attempt(f"Internet Archive/r/{subreddit}", status_code, False, "Snapshot parsing not implemented for generic search")
            else:
                log_download_attempt(f"Internet Archive/r/{subreddit}", status_code, False, f"HTTP {status_code}")
        except Exception as e:
            log_download_attempt(f"Internet Archive/r/{subreddit}", None, False, str(e))
    
    return results

def download_data(
    output_path: Optional[str] = None,
    subreddits: Optional[List[str]] = None,
    limit: int = 500,
    reddit_client_id: Optional[str] = None,
    reddit_client_secret: Optional[str] = None,
    reddit_user_agent: Optional[str] = None
):
    """
    Main entry point for data download with fallback chain.
    Logs every attempt to data/processed/download_attempts.log.
    """
    if subreddits is None:
        subreddits = ["AskScience", "FDR"] # Default fallbacks if not provided
    
    output_file = Path(output_path) if output_path else PROJECT_ROOT / "data" / "raw" / "reddit_threads.jsonl"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    all_posts = []
    
    # 1. Try Pushshift
    logger.info("Starting download pipeline: Pushshift...")
    posts = fetch_from_pushshift(subreddits, limit)
    if posts:
        all_posts.extend(posts)
        logger.info(f"Pushshift succeeded. Collected {len(posts)} posts.")
    
    # 2. Try Reddit API if Pushshift failed or returned insufficient data
    if len(all_posts) < limit:
        logger.info("Pushshift insufficient. Trying Reddit API...")
        posts = fetch_from_reddit_api(
            subreddits, 
            limit - len(all_posts),
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent
        )
        if posts:
            all_posts.extend(posts)
            logger.info(f"Reddit API succeeded. Collected {len(posts)} posts.")

    # 3. Try HuggingFace if still insufficient
    if len(all_posts) < limit:
        logger.info("Reddit API insufficient. Trying HuggingFace...")
        posts = fetch_from_huggingface(limit=limit - len(all_posts))
        if posts:
            all_posts.extend(posts)
            logger.info(f"HuggingFace succeeded. Collected {len(posts)} posts.")

    # 4. Try Internet Archive (Last resort)
    if len(all_posts) < limit:
        logger.info("HuggingFace insufficient. Trying Internet Archive...")
        posts = fetch_from_internet_archive(subreddits, limit=limit - len(all_posts))
        if posts:
            all_posts.extend(posts)
            logger.info(f"Internet Archive succeeded. Collected {len(posts)} posts.")

    if not all_posts:
        error_msg = "All data sources failed. No synthetic data generated."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Write to file
    logger.info(f"Writing {len(all_posts)} posts to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for post in all_posts:
            f.write(json.dumps(post) + '\n')
    
    checksum = compute_sha256(output_file)
    logger.info(f"Download complete. Checksum: {checksum}")
    return output_file, checksum

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download Reddit data with logging.")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--subreddits", nargs="+", type=str, help="List of subreddits to fetch")
    parser.add_argument("--limit", type=int, default=500, help="Max posts to fetch")
    parser.add_argument("--reddit-client-id", type=str, help="Reddit API Client ID")
    parser.add_argument("--reddit-client-secret", type=str, help="Reddit API Client Secret")
    parser.add_argument("--reddit-user-agent", type=str, help="Reddit API User Agent")
    
    args = parser.parse_args()
    
    try:
        download_data(
            output_path=args.output,
            subreddits=args.subreddits,
            limit=args.limit,
            reddit_client_id=args.reddit_client_id,
            reddit_client_secret=args.reddit_client_secret,
            reddit_user_agent=args.reddit_user_agent
        )
    except RuntimeError as e:
        logger.critical(str(e))
        exit(1)

if __name__ == "__main__":
    main()