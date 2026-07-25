import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Configure logging for this module specifically
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
PUSHSHIFT_ENDPOINT = "https://api.pushshift.io/reddit/search/submission/"
REDDIT_API_ENDPOINT = "https://oauth.reddit.com/api/v1/search"
HUGGINGFACE_DATASET_ID = "reddit-research/threads-2024"
HUGGINGFACE_FILE_PATH = "train.jsonl"
HUGGINGFACE_URL = f"hf://datasets/{HUGGINGFACE_DATASET_ID}/{HUGGINGFACE_FILE_PATH}"

def log_download_attempt(
    endpoint: str,
    status_code: int,
    success: bool,
    log_path: Path,
    error_msg: Optional[str] = None
) -> None:
    """
    Logs the exact timestamp and HTTP status code for every API attempt
    to the specified log file.
    
    Args:
        endpoint: The API endpoint that was attempted.
        status_code: The HTTP status code received (or -1 if connection failed).
        success: Boolean indicating if the request was successful.
        log_path: Path to the log file.
        error_msg: Optional error message if the request failed.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_entry = {
        "timestamp": timestamp,
        "endpoint": endpoint,
        "status_code": status_code,
        "success": success,
        "error": error_msg
    }
    
    log_dir = log_path.parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    if success:
        logger.info(f"Download attempt successful: {endpoint} (Status: {status_code})")
    else:
        logger.warning(f"Download attempt failed: {endpoint} (Status: {status_code}) - {error_msg}")

def fetch_from_pushshift(
    subreddits: List[str],
    limit: int = 100,
    log_path: Optional[Path] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Fetches data from the Pushshift API.
    
    Args:
        subreddits: List of subreddit names to fetch.
        limit: Maximum number of submissions per subreddit.
        log_path: Path to log download attempts.
        
    Returns:
        Tuple of (data list, success boolean).
    """
    all_data = []
    success = False
    
    if log_path is None:
        log_path = Path("data/processed/download_attempts.log")
        
    for subreddit in subreddits:
        url = f"{PUSHSHIFT_ENDPOINT}?subreddit={subreddit}&limit={limit}"
        try:
            logger.info(f"Attempting Pushshift fetch for {subreddit}...")
            response = requests.get(url, timeout=30)
            status_code = response.status_code
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    all_data.extend(data['data'])
                    success = True
                    log_download_attempt(url, status_code, True, log_path)
                else:
                    log_download_attempt(url, status_code, False, log_path, "No 'data' field in response")
            else:
                log_download_attempt(url, status_code, False, log_path, f"HTTP Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            log_download_attempt(url, -1, False, log_path, str(e))
            
    return all_data, success

def fetch_from_reddit_api(
    subreddits: List[str],
    limit: int = 100,
    log_path: Optional[Path] = None,
    api_keys: Optional[Dict[str, str]] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Fetches data from the Reddit Official API (OAuth).
    
    Args:
        subreddits: List of subreddit names to fetch.
        limit: Maximum number of submissions per subreddit.
        log_path: Path to log download attempts.
        api_keys: Dictionary containing client_id, client_secret, user_agent.
        
    Returns:
        Tuple of (data list, success boolean).
    """
    all_data = []
    success = False
    
    if log_path is None:
        log_path = Path("data/processed/download_attempts.log")
        
    if not api_keys:
        logger.warning("Reddit API keys not provided. Skipping Reddit API fetch.")
        return [], False
        
    client_id = api_keys.get('client_id')
    client_secret = api_keys.get('client_secret')
    user_agent = api_keys.get('user_agent', 'test_script')
    
    if not client_id or not client_secret:
        logger.warning("Missing Reddit API credentials.")
        return [], False
        
    try:
        # Authenticate
        auth_url = "https://www.reddit.com/api/v1/access_token"
        auth_response = requests.post(
            auth_url,
            auth=(client_id, client_secret),
            data={'grant_type': 'client_credentials'},
            headers={'User-Agent': user_agent},
            timeout=30
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}', 'User-Agent': user_agent}
            
            for subreddit in subreddits:
                url = f"{REDDIT_API_ENDPOINT}?q=site:reddit.com/r/{subreddit}&type=link&limit={limit}"
                try:
                    logger.info(f"Attempting Reddit API fetch for {subreddit}...")
                    response = requests.get(url, headers=headers, timeout=30)
                    status_code = response.status_code
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'children' in data['data']:
                            all_data.extend([child['data'] for child in data['data']['children']])
                            success = True
                            log_download_attempt(url, status_code, True, log_path)
                        else:
                            log_download_attempt(url, status_code, False, log_path, "No data in response")
                    else:
                        log_download_attempt(url, status_code, False, log_path, f"HTTP Error: {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    log_download_attempt(url, -1, False, log_path, str(e))
        else:
            log_download_attempt(auth_url, auth_response.status_code, False, log_path, "Auth failed")
            
    except Exception as e:
        logger.error(f"Reddit API fetch failed: {e}")
        
    return all_data, success

def fetch_from_huggingface(
    log_path: Optional[Path] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Fetches data from the HuggingFace dataset archive.
    
    Args:
        log_path: Path to log download attempts.
        
    Returns:
        Tuple of (data list, success boolean).
    """
    all_data = []
    success = False
    
    if log_path is None:
        log_path = Path("data/processed/download_attempts.log")
        
    url = HUGGINGFACE_URL
    try:
        logger.info(f"Attempting HuggingFace fetch from {HUGGINGFACE_DATASET_ID}...")
        
        # Try to import datasets library
        try:
            from datasets import load_dataset
            dataset = load_dataset("json", data_files={"train": url}, streaming=True)
            
            # Iterate through the dataset
            count = 0
            for item in dataset['train']:
                all_data.append(item)
                count += 1
                if count % 1000 == 0:
                    logger.info(f"Downloaded {count} items from HuggingFace...")
                    
            if count > 0:
                success = True
                log_download_attempt(url, 200, True, log_path)
            else:
                log_download_attempt(url, 200, False, log_path, "Dataset empty")
                
        except ImportError:
            log_download_attempt(url, -1, False, log_path, "datasets library not installed")
        except Exception as e:
            log_download_attempt(url, -1, False, log_path, str(e))
            
    except Exception as e:
        logger.error(f"HuggingFace fetch failed: {e}")
        log_download_attempt(url, -1, False, log_path, str(e))
        
    return all_data, success

def fetch_from_internet_archive(
  subreddits: List[str],
  log_path: Optional[Path] = None
) -> Tuple[List[Dict[str, Any]], bool]:
  """
  Fetches data from the Internet Archive (archive.org).
  
  Args:
      subreddits: List of subreddit names to fetch.
      log_path: Path to log download attempts.
      
  Returns:
      Tuple of (data list, success boolean).
  """
  # Placeholder for Internet Archive implementation
  # This would typically involve searching archive.org for Reddit snapshots
  return [], False

def download_data(
    output_path: str,
    subreddits: Optional[List[str]] = None,
    stackexchange_sites: Optional[List[str]] = None,
    limit: int = 100,
    api_keys: Optional[Dict[str, str]] = None
) -> bool:
    """
    Main function to download data from multiple sources with fallback logic.
    
    Args:
        output_path: Path to save the downloaded data.
        subreddits: List of subreddit names to fetch (default: ['AskScience', 'AskReddit']).
        stackexchange_sites: List of Stack Exchange sites to fetch (default: ['stackoverflow']).
        limit: Maximum number of submissions per subreddit.
        api_keys: Dictionary containing API keys for Reddit API.
        
    Returns:
        Boolean indicating if download was successful.
    """
    if subreddits is None:
        subreddits = ['AskScience', 'AskReddit']
    if stackexchange_sites is None:
        stackexchange_sites = ['stackoverflow']
        
    output_file = Path(output_path)
    log_path = Path("data/processed/download_attempts.log")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    all_data = []
    origin_type = None
    
    # Try Pushshift API (Primary)
    logger.info("Attempting Pushshift API (Primary)...")
    data, success = fetch_from_pushshift(subreddits, limit, log_path)
    if success:
        all_data.extend(data)
        origin_type = "API"
        logger.info(f"Successfully fetched {len(data)} items from Pushshift.")
        
    # If Pushshift failed, try Reddit API (Fallback 1)
    if not success:
        logger.info("Pushshift failed. Attempting Reddit Official API (Fallback 1)...")
        data, success = fetch_from_reddit_api(subreddits, limit, log_path, api_keys)
        if success:
            all_data.extend(data)
            origin_type = "API"
            logger.info(f"Successfully fetched {len(data)} items from Reddit API.")
            
    # If both APIs failed, try HuggingFace (Fallback 2)
    if not success:
        logger.info("Reddit API failed. Attempting HuggingFace archives (Fallback 2)...")
        data, success = fetch_from_huggingface(log_path)
        if success:
            all_data.extend(data)
            origin_type = "archive"
            logger.info(f"Successfully fetched {len(data)} items from HuggingFace.")
            
    # If all sources failed, raise error
    if not success:
        error_msg = "All data sources (Pushshift, Reddit API, HuggingFace) failed."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    # Add origin_type to each record and write to file
    enriched_data = []
    for item in all_data:
        item['origin_type'] = origin_type
        enriched_data.append(item)
        
    # Write to JSONL file
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in enriched_data:
            f.write(json.dumps(item) + '\n')
            
    logger.info(f"Downloaded {len(enriched_data)} items to {output_file}")
    return True

def main():
    """Main entry point for the download script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Reddit data for analysis.")
    parser.add_argument("--output", default="data/raw/reddit_threads.jsonl", help="Output file path.")
    parser.add_argument("--subreddits", nargs="+", default=["AskScience", "AskReddit"], help="Subreddits to fetch.")
    parser.add_argument("--limit", type=int, default=100, help="Limit per subreddit.")
    parser.add_argument("--reddit-client-id", type=str, help="Reddit API client ID.")
    parser.add_argument("--reddit-client-secret", type=str, help="Reddit API client secret.")
    parser.add_argument("--reddit-user-agent", type=str, default="llmXive_script", help="Reddit API user agent.")
    
    args = parser.parse_args()
    
    api_keys = None
    if args.reddit_client_id and args.reddit_client_secret:
        api_keys = {
            'client_id': args.reddit_client_id,
            'client_secret': args.reddit_client_secret,
            'user_agent': args.reddit_user_agent
        }
        
    try:
        success = download_data(
            output_path=args.output,
            subreddits=args.subreddits,
            limit=args.limit,
            api_keys=api_keys
        )
        if success:
            print(f"Data download completed successfully to {args.output}")
        else:
            print("Data download failed.")
            exit(1)
    except RuntimeError as e:
        print(f"Data download failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()