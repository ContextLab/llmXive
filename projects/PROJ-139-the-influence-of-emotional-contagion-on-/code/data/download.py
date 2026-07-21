import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PUSHSHIFT_API_URL = "https://api.pushshift.io/reddit/search/submission/"
REDDIT_OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
HF_DATASET_ID = "reddit_comments"  # Placeholder for verified HF archive
MAX_RETRIES = 3
TIMEOUT = 30

def fetch_from_pushshift(subreddits: List[str], limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch data from Pushshift API.
    
    Args:
        subreddits: List of subreddit names to fetch.
        limit: Maximum number of submissions per subreddit.
        
    Returns:
        List of submission dictionaries.
        
    Raises:
        RuntimeError: If the API call fails after retries.
    """
    all_data = []
    
    for subreddit in subreddits:
        params = {
            'subreddit': subreddit,
            'size': min(limit, 100),  # Pushshift max batch size
            'sort': 'created_utc',
            'sort_type': 'desc'
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Fetching from Pushshift: r/{subreddit} (Attempt {attempt + 1})")
                response = requests.get(PUSHSHIFT_API_URL, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                
                data = response.json()
                if 'data' in data:
                    all_data.extend(data['data'])
                    logger.info(f"Retrieved {len(data['data'])} submissions from r/{subreddit}")
                else:
                    logger.warning(f"No data field in Pushshift response for r/{subreddit}")
                
                # Respect rate limits
                time.sleep(2)
                break
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Pushshift request failed for r/{subreddit}: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise RuntimeError(f"Pushshift API failed for r/{subreddit} after {MAX_RETRIES} attempts: {e}")
                time.sleep(5 * (attempt + 1))  # Exponential backoff
                
    return all_data

def fetch_from_reddit_api(subreddits: List[str], limit: int = 100, config: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Fetch data from Reddit Official API (requires OAuth).
    
    Args:
        subreddits: List of subreddit names to fetch.
        limit: Maximum number of submissions per subreddit.
        config: Configuration containing API keys.
        
    Returns:
        List of submission dictionaries.
        
    Raises:
        RuntimeError: If OAuth or API calls fail.
    """
    if not config:
        raise RuntimeError("Reddit API configuration not provided.")
        
    client_id = config.get('reddit_client_id')
    client_secret = config.get('reddit_client_secret')
    user_agent = config.get('reddit_user_agent', 'llmXive-research-agent/1.0')
    
    if not all([client_id, client_secret]):
        raise RuntimeError("Missing Reddit API credentials in configuration.")
        
    # Authenticate
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    data = {'grant_type': 'client_credentials'}
    
    try:
        logger.info("Authenticating with Reddit API...")
        response = requests.post(REDDIT_OAUTH_URL, auth=auth, data=data, timeout=TIMEOUT)
        response.raise_for_status()
        token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Reddit API authentication failed: {e}")
        
    headers = {'Authorization': f'Bearer {token}', 'User-Agent': user_agent}
    all_data = []
    
    for subreddit in subreddits:
        url = f"https://oauth.reddit.com/r/{subreddit}/new"
        params = {'limit': limit}
        
        try:
            logger.info(f"Fetching from Reddit API: r/{subreddit}")
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            
            children = response.json()['data']['children']
            for child in children:
                all_data.append(child['data'])
                
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Reddit API fetch failed for r/{subreddit}: {e}")
            
    return all_data

def fetch_from_huggingface(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch data from a verified HuggingFace archive.
    
    Args:
        limit: Maximum number of rows to fetch.
        
    Returns:
        List of submission dictionaries.
        
    Raises:
        RuntimeError: If the dataset cannot be loaded.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset from HuggingFace: {HF_DATASET_ID}")
        dataset = load_dataset(HF_DATASET_ID, split='train', streaming=True)
        
        all_data = []
        count = 0
        for item in dataset:
            if count >= limit:
                break
            # Normalize keys to match expected schema
            normalized = {
                'id': item.get('id', item.get('post_id', '')),
                'subreddit': item.get('subreddit', item.get('subreddit_name', '')),
                'title': item.get('title', item.get('post_title', '')),
                'selftext': item.get('selftext', item.get('text', '')),
                'created_utc': item.get('created_utc', 0),
                'score': item.get('score', 0),
                'num_comments': item.get('num_comments', 0)
            }
            all_data.append(normalized)
            count += 1
            
        logger.info(f"Retrieved {len(all_data)} submissions from HuggingFace")
        return all_data
        
    except Exception as e:
        raise RuntimeError(f"HuggingFace dataset fetch failed: {e}")

def fetch_from_internet_archive(subreddits: List[str], limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch data from Internet Archive (Wayback Machine) as a last resort.
    Note: This is a simplified placeholder; real implementation would parse HTML/JSON.
    
    Args:
        subreddits: List of subreddit names.
        limit: Max items.
        
    Returns:
        List of submissions.
        
    Raises:
        RuntimeError: If fetch fails.
    """
    # Placeholder for actual archive logic
    # In a real scenario, this would query the Wayback Machine API
    raise RuntimeError("Internet Archive fetch not implemented for this task.")

def download_data(output_path: str, subreddits: List[str], config: Optional[Dict] = None) -> None:
    """
    Main entry point for data download. Implements strict fail-loud policy.
    
    Strategy:
    1. Try Pushshift API.
    2. If Pushshift fails, try Reddit Official API.
    3. If Reddit API fails, try HuggingFace archives.
    4. If all fail, raise RuntimeError.
    
    Args:
        output_path: Path to save the JSONL file.
        subreddits: List of subreddits to download.
        config: Configuration dictionary for API keys.
        
    Raises:
        RuntimeError: If all data sources fail.
    """
    logger.info(f"Starting data download for subreddits: {subreddits}")
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_data = []
    source_used = None
    last_error = None
    
    # Attempt 1: Pushshift
    try:
        logger.info("Attempting Pushshift API...")
        all_data = fetch_from_pushshift(subreddits)
        if all_data:
            source_used = "pushshift"
            logger.info("Data successfully fetched from Pushshift.")
        else:
            logger.warning("Pushshift returned no data.")
    except Exception as e:
        logger.error(f"Pushshift failed: {e}")
        last_error = e
    
    # Attempt 2: Reddit API (if Pushshift failed or empty)
    if not all_data:
        try:
            logger.info("Attempting Reddit Official API...")
            all_data = fetch_from_reddit_api(subreddits, config=config)
            if all_data:
                source_used = "reddit_api"
                logger.info("Data successfully fetched from Reddit API.")
            else:
                logger.warning("Reddit API returned no data.")
        except Exception as e:
            logger.error(f"Reddit API failed: {e}")
            last_error = e
    
    # Attempt 3: HuggingFace (if previous failed)
    if not all_data:
        try:
            logger.info("Attempting HuggingFace archives...")
            all_data = fetch_from_huggingface(limit=len(subreddits) * 100)
            if all_data:
                source_used = "huggingface"
                logger.info("Data successfully fetched from HuggingFace.")
            else:
                logger.warning("HuggingFace returned no data.")
        except Exception as e:
            logger.error(f"HuggingFace failed: {e}")
            last_error = e
    
    # Final Check: Fail Loudly if no data
    if not all_data:
        error_msg = (
            f"All data sources (Pushshift, Reddit API, HuggingFace) failed. "
            f"Last error: {last_error}. "
            f"No synthetic data generated. Please verify network access or data source availability."
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    # Write output
    logger.info(f"Writing {len(all_data)} records to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_data:
            # Add origin_type for tracking
            item['origin_type'] = source_used
            f.write(json.dumps(item) + '\n')
    
    logger.info(f"Download complete. Source: {source_used}, Count: {len(all_data)}")

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Reddit data for analysis.")
    parser.add_argument('--subreddits', type=str, nargs='+', default=['AskScience', 'science'],
                        help='List of subreddits to download.')
    parser.add_argument('--output', type=str, default='data/raw/reddit_threads.jsonl',
                        help='Output file path.')
    parser.add_argument('--config', type=str, default=None,
                        help='Path to config file (JSON) for API keys.')
    
    args = parser.parse_args()
    
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    try:
        download_data(args.output, args.subreddits, config)
    except RuntimeError as e:
        logger.critical(f"Pipeline halted: {e}")
        raise

if __name__ == "__main__":
    main()