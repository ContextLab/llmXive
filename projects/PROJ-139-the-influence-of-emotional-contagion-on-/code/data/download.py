"""
Data download module for emotional contagion research.
Implements fallback chain: Pushshift -> Reddit API -> HuggingFace/Internet Archive.
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
import pandas as pd

from code.utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
PUSHSHIFT_BASE_URL = "https://api.pushshift.io/reddit/search/submission"
REDDIT_API_BASE = "https://oauth.reddit.com"
DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "reddit_threads.csv"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_from_pushshift(subreddits: List[str], limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Fetch data from Pushshift API.
    Returns DataFrame if successful, None otherwise.
    """
    logger.info(f"Attempting to fetch from Pushshift for subreddits: {subreddits}")
    
    all_posts = []
    
    for subreddit in subreddits:
        try:
            params = {
                "subreddit": subreddit,
                "size": min(limit, 100),  # Pushshift max batch size
                "sort": "created_utc",
                "sort_type": "desc",
                "fields": "id,title,author,selftext,created_utc,num_comments,subreddit,url"
            }
            
            response = requests.get(PUSHSHIFT_BASE_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    posts = data["data"]
                    all_posts.extend(posts)
                    logger.info(f"Retrieved {len(posts)} posts from r/{subreddit} via Pushshift")
                else:
                    logger.warning(f"No data returned from Pushshift for r/{subreddit}")
            else:
                logger.warning(f"Pushshift returned status {response.status_code} for r/{subreddit}")
                continue
            
            # Respect rate limits
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Pushshift request failed for r/{subreddit}: {e}")
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Pushshift JSON decode error for r/{subreddit}: {e}")
            continue
    
    if not all_posts:
        logger.warning("No posts retrieved from Pushshift")
        return None
    
    df = pd.DataFrame(all_posts)
    df["origin_type"] = "pushshift"
    logger.info(f"Successfully fetched {len(df)} posts from Pushshift")
    return df


def fetch_from_reddit_api(subreddits: List[str], limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Fetch data from Reddit Official API.
    Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "emotional_contagion_research:1.0")
    
    if not client_id or not client_secret:
        logger.warning("Reddit API credentials not found in environment variables")
        return None
    
    logger.info("Attempting to fetch from Reddit Official API")
    
    try:
        # Get access token
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        data = {"grant_type": "client_credentials"}
        token_response = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data=data,
            headers={"User-Agent": user_agent},
            timeout=30
        )
        
        if token_response.status_code != 200:
            logger.error(f"Reddit auth failed: {token_response.text}")
            return None
        
        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"bearer {access_token}", "User-Agent": user_agent}
        
        all_posts = []
        
        for subreddit in subreddits:
            try:
                # Fetch top posts
                url = f"{REDDIT_API_BASE}/r/{subreddit}/top"
                params = {"limit": min(limit, 100), "t": "month"}
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and "children" in data["data"]:
                        posts = [child["data"] for child in data["data"]["children"]]
                        all_posts.extend(posts)
                        logger.info(f"Retrieved {len(posts)} posts from r/{subreddit} via Reddit API")
                else:
                    logger.warning(f"Reddit API returned status {response.status_code} for r/{subreddit}")
                
                time.sleep(1)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Reddit API request failed for r/{subreddit}: {e}")
                continue
        
        if not all_posts:
            logger.warning("No posts retrieved from Reddit API")
            return None
        
        df = pd.DataFrame(all_posts)
        df["origin_type"] = "reddit_api"
        logger.info(f"Successfully fetched {len(df)} posts from Reddit API")
        return df
        
    except Exception as e:
        logger.error(f"Reddit API fetch failed: {e}")
        return None


def fetch_from_huggingface(subreddits: List[str], limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Fetch data from verified HuggingFace archives.
    Uses the 'reddit' dataset from HuggingFace Datasets.
    """
    logger.info("Attempting to fetch from HuggingFace archives")
    
    try:
        # Dynamically import datasets to avoid dependency if not installed
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("datasets library not installed. Install with: pip install datasets")
            return None
        
        all_posts = []
        
        for subreddit in subreddits:
            try:
                # Load dataset - this may take time for large datasets
                logger.info(f"Loading r/{subreddit} data from HuggingFace...")
                
                # Try to load a subset of Reddit data
                # Using a specific configuration if available, otherwise general
                dataset = load_dataset(
                    "csef/reddit", 
                    name="top",  # Use top posts configuration
                    split="train",
                    streaming=True,  # Stream to avoid loading entire dataset
                    trust_remote_code=True
                )
                
                subreddit_posts = []
                count = 0
                for item in dataset:
                    if item.get("subreddit") == subreddit:
                        subreddit_posts.append(item)
                        count += 1
                        if count >= limit:
                            break
                
                if subreddit_posts:
                    all_posts.extend(subreddit_posts)
                    logger.info(f"Retrieved {len(subreddit_posts)} posts from r/{subreddit} via HuggingFace")
                
            except Exception as e:
                logger.warning(f"HuggingFace fetch failed for r/{subreddit}: {e}")
                continue
        
        if not all_posts:
            logger.warning("No posts retrieved from HuggingFace")
            return None
        
        df = pd.DataFrame(all_posts)
        # Normalize column names if necessary
        required_cols = ["id", "title", "author", "selftext", "created_utc", "num_comments", "subreddit"]
        available_cols = [col for col in required_cols if col in df.columns]
        if available_cols:
            df = df[available_cols]
        
        df["origin_type"] = "huggingface"
        logger.info(f"Successfully fetched {len(df)} posts from HuggingFace")
        return df
        
    except Exception as e:
        logger.error(f"HuggingFace fetch failed: {e}")
        return None


def fetch_from_internet_archive(subreddits: List[str], limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Fetch data from Internet Archive dumps.
    Note: This is a fallback and may require manual intervention for large datasets.
    """
    logger.info("Attempting to fetch from Internet Archive")
    
    try:
        # Try to load from a known archive dataset
        # This is a simplified approach - real implementation would need specific archive paths
        from datasets import load_dataset
        
        all_posts = []
        
        for subreddit in subreddits:
            try:
                # Attempt to load from a generic Reddit archive
                dataset = load_dataset(
                    "csef/reddit",
                    split="train",
                    streaming=True
                )
                
                subreddit_posts = []
                count = 0
                for item in dataset:
                    if item.get("subreddit") == subreddit:
                        subreddit_posts.append(item)
                        count += 1
                        if count >= limit:
                            break
                
                if subreddit_posts:
                    all_posts.extend(subreddit_posts)
                    logger.info(f"Retrieved {len(subreddit_posts)} posts from r/{subreddit} via Internet Archive")
                
            except Exception as e:
                logger.warning(f"Internet Archive fetch failed for r/{subreddit}: {e}")
                continue
        
        if not all_posts:
            logger.warning("No posts retrieved from Internet Archive")
            return None
        
        df = pd.DataFrame(all_posts)
        required_cols = ["id", "title", "author", "selftext", "created_utc", "num_comments", "subreddit"]
        available_cols = [col for col in required_cols if col in df.columns]
        if available_cols:
            df = df[available_cols]
        
        df["origin_type"] = "internet_archive"
        logger.info(f"Successfully fetched {len(df)} posts from Internet Archive")
        return df
        
    except Exception as e:
        logger.error(f"Internet Archive fetch failed: {e}")
        return None


def download_data(
    subreddits: List[str] = None,
    limit: int = 500,
    output_path: Path = None
) -> pd.DataFrame:
    """
    Main download function implementing the fallback chain.
    
    Fallback order:
    1. Pushshift API (primary)
    2. Reddit Official API (fallback 1)
    3. HuggingFace archives (fallback 2)
    4. Internet Archive dumps (fallback 3)
    
    Args:
        subreddits: List of subreddit names to fetch. Defaults to ['AskScience'].
        limit: Maximum number of posts per subreddit.
        output_path: Path to save the CSV file. Defaults to data/raw/reddit_threads.csv.
        
    Returns:
        DataFrame containing the fetched posts.
        
    Raises:
        RuntimeError: If all data sources fail.
    """
    if subreddits is None:
        subreddits = ["AskScience"]
        
    if output_path is None:
        output_path = OUTPUT_FILE
        
    logger.info(f"Starting data download for subreddits: {subreddits}")
    logger.info(f"Data sources: Pushshift -> Reddit API -> HuggingFace -> Internet Archive")
    
    # Try Pushshift first
    df = fetch_from_pushshift(subreddits, limit)
    if df is not None:
        logger.info(f"Data successfully fetched from Pushshift. Saving to {output_path}")
        df.to_csv(output_path, index=False)
        return df
    
    # Fallback 1: Reddit API
    logger.info("Pushshift failed, attempting Reddit Official API...")
    df = fetch_from_reddit_api(subreddits, limit)
    if df is not None:
        logger.info(f"Data successfully fetched from Reddit API. Saving to {output_path}")
        df.to_csv(output_path, index=False)
        return df
    
    # Fallback 2: HuggingFace
    logger.info("Reddit API failed, attempting HuggingFace archives...")
    df = fetch_from_huggingface(subreddits, limit)
    if df is not None:
        logger.info(f"Data successfully fetched from HuggingFace. Saving to {output_path}")
        df.to_csv(output_path, index=False)
        return df
    
    # Fallback 3: Internet Archive
    logger.info("HuggingFace failed, attempting Internet Archive...")
    df = fetch_from_internet_archive(subreddits, limit)
    if df is not None:
        logger.info(f"Data successfully fetched from Internet Archive. Saving to {output_path}")
        df.to_csv(output_path, index=False)
        return df
    
    # All sources failed
    error_msg = "All data sources (Pushshift, Reddit API, HuggingFace, Internet Archive) failed."
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def main():
    """
    Entry point for the download script.
    """
    logger.info("Running data download script")
    
    # Default subreddits for the study
    subreddits = ["AskScience", "science"]
    limit = 250  # 250 per subreddit = 500 total minimum
    
    try:
        df = download_data(subreddits=subreddits, limit=limit)
        logger.info(f"Download complete. Total posts: {len(df)}")
        logger.info(f"Origin types: {df['origin_type'].value_counts().to_dict()}")
        logger.info(f"Data saved to: {OUTPUT_FILE}")
        
        # Basic validation
        if len(df) < 100:
            logger.warning(f"Low data volume: {len(df)} posts retrieved")
        
        if len(df["subreddit"].unique()) < 2:
            logger.warning(f"Single subreddit detected: {df['subreddit'].unique()}")
            
    except RuntimeError as e:
        logger.error(f"Data download failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during download: {e}")
        raise


if __name__ == "__main__":
    main()
