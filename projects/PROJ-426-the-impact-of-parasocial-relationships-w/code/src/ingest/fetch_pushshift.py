"""
Fetch AI interaction logs from Pushshift for matched users.

This script retrieves Reddit comments/posts from specific subreddits
(r/Replika, r/characterAI, r/AICompanions) for users identified in the
matched dataset, strictly within the survey window defined in the
survey_window_final.json file.

It implements exponential backoff and rate limit handling as specified
in the project's retry and rate limit utilities.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Project imports
from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context
from src.utils.retry_policy import retry_with_backoff, RetryConfig
from src.utils.rate_limit_handler import RateLimitError, handle_429_response, is_rate_limited

# Constants
PUSHSHIFT_API_URL = "https://api.pushshift.io/reddit/search/comment/"
# Subreddits of interest for AI companion interactions
TARGET_SUBREDDITS = ["Replika", "characterAI", "AICompanions"]

# Retry configuration matching project standards
RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    backoff_factor=2.0
)

logger = get_logger(__name__)


def load_survey_window(window_path: Path) -> Dict[str, datetime]:
    """
    Load the survey window boundaries from the JSON file.
    
    Args:
        window_path: Path to survey_window_final.json
        
    Returns:
        Dictionary with 'start_date' and 'end_date' as datetime objects.
        
    Raises:
        FileNotFoundError: If the window file does not exist.
        ValueError: If the file format is invalid or dates are missing.
    """
    if not window_path.exists():
        raise FileNotFoundError(f"Survey window file not found: {window_path}")
        
    with open(window_path, 'r') as f:
        data = json.load(f)
        
    if 'start_date' not in data or 'end_date' not in data:
        raise ValueError("Survey window file must contain 'start_date' and 'end_date' keys")
        
    # Parse ISO format dates
    try:
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid date format in survey window file: {e}")
        
    return {
        'start_date': start_date,
        'end_date': end_date
    }


def load_matched_users(matched_path: Path) -> pd.DataFrame:
    """
    Load the matched users dataset.
    
    Args:
        matched_path: Path to matched_users.parquet
        
    Returns:
        DataFrame with user data including hashed usernames.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not matched_path.exists():
        raise FileNotFoundError(f"Matched users file not found: {matched_path}")
        
    df = pd.read_parquet(matched_path)
    
    # Validate required columns
    required_cols = ['user_id', 'username_hash']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Matched users file missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} matched users")
    return df


def fetch_pushshift_logs_for_user(
    user_id: str,
    username_hash: str,
    start_date: datetime,
    end_date: datetime,
    subreddits: List[str]
) -> List[Dict[str, Any]]:
    """
    Fetch Reddit comments for a specific user from Pushshift API.
    
    Args:
        user_id: The user identifier
        username_hash: The hashed username to search for
        start_date: Start of the search window
        end_date: End of the search window
        subreddits: List of subreddits to search in
        
    Returns:
        List of comment dictionaries matching the criteria.
    """
    all_logs = []
    
    for subreddit in subreddits:
        # Construct search parameters
        params = {
            'author': username_hash,
            'subreddit': subreddit,
            'after': int(start_date.timestamp()),
            'before': int(end_date.timestamp()),
            'limit': 1000,  # Pushshift max per request
            'sort': 'created_utc'
        }
        
        logger.debug(f"Fetching logs for user {user_id} in r/{subreddit}")
        
        # Use retry logic with backoff for API calls
        @retry_with_backoff(retry_config=RETRY_CONFIG)
        def make_request():
            response = requests.get(PUSHSHIFT_API_URL, params=params, timeout=60)
            
            if is_rate_limited(response):
                raise RateLimitError(f"Rate limited for user {user_id} in r/{subreddit}")
            
            response.raise_for_status()
            return response.json()
        
        try:
            result = make_request()
            
            if 'data' in result and result['data']:
                for comment in result['data']:
                    # Add metadata
                    comment['user_id'] = user_id
                    comment['source_subreddit'] = subreddit
                    comment['fetched_at'] = datetime.now().isoformat()
                    all_logs.append(comment)
                    
                logger.debug(f"Found {len(result['data'])} comments for user {user_id} in r/{subreddit}")
            else:
                logger.debug(f"No comments found for user {user_id} in r/{subreddit}")
                
        except RateLimitError as e:
            logger.warning(f"Rate limit hit for user {user_id} in r/{subreddit}: {e}")
            # Continue to next subreddit rather than failing entirely
            continue
        except Exception as e:
            logger.error(f"Error fetching logs for user {user_id} in r/{subreddit}: {e}")
            continue
        
        # Rate limiting between requests to be respectful
        time.sleep(0.5)
        
    return all_logs


def fetch_all_pushshift_logs(
    matched_users_path: Path,
    window_path: Path,
    output_path: Path
) -> None:
    """
    Main function to fetch Pushshift logs for all matched users.
    
    Args:
        matched_users_path: Path to matched_users.parquet
        window_path: Path to survey_window_final.json
        output_path: Path where the output parquet file will be saved
    """
    log_stage_start(logger, "Pushshift Log Fetching")
    
    # Load dependencies
    window = load_survey_window(window_path)
    matched_users = load_matched_users(matched_users_path)
    
    logger.info(f"Survey window: {window['start_date']} to {window['end_date']}")
    logger.info(f"Fetching logs for {len(matched_users)} users across {len(TARGET_SUBREDDITS)} subreddits")
    
    all_logs = []
    
    # Process each user
    for idx, row in matched_users.iterrows():
        user_id = row['user_id']
        username_hash = row['username_hash']
        
        logs = fetch_pushshift_logs_for_user(
            user_id=user_id,
            username_hash=username_hash,
            start_date=window['start_date'],
            end_date=window['end_date'],
            subreddits=TARGET_SUBREDDITS
        )
        
        all_logs.extend(logs)
        
        # Progress logging
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(matched_users)} users. Total logs: {len(all_logs)}")
    
    # Create output DataFrame
    if all_logs:
        logs_df = pd.DataFrame(all_logs)
        
        # Standardize column names and types
        # Ensure timestamp columns are datetime
        if 'created_utc' in logs_df.columns:
            logs_df['created_utc'] = pd.to_datetime(logs_df['created_utc'], unit='s')
        
        # Sort by user and timestamp
        logs_df = logs_df.sort_values(by=['user_id', 'created_utc'])
        
        # Save to parquet
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logs_df.to_parquet(output_path, index=False)
        
        logger.info(f"Saved {len(logs_df)} log entries to {output_path}")
    else:
        logger.warning("No logs found for any users. Creating empty DataFrame with expected schema.")
        # Create empty DataFrame with expected schema
        empty_df = pd.DataFrame(columns=[
            'user_id', 'username_hash', 'created_utc', 'subreddit', 'body',
            'score', 'source_subreddit', 'fetched_at'
        ])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        empty_df.to_parquet(output_path, index=False)
        logger.info(f"Created empty output file at {output_path}")
        
    log_stage_end(logger, "Pushshift Log Fetching", success=True)


def main():
    """Entry point for the script."""
    # Setup logging
    setup_logging_level = logging.INFO
    logging.basicConfig(level=setup_logging_level)
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    matched_users_path = project_root / "data" / "processed" / "matched_users.parquet"
    window_path = project_root / "data" / "processed" / "survey_window_final.json"
    output_path = project_root / "data" / "processed" / "pushshift_logs_refined.parquet"
    
    # Validate input files exist
    if not matched_users_path.exists():
        logger.error(f"Required input file not found: {matched_users_path}")
        logger.error("Please ensure T014 (user_match.py) has been completed successfully.")
        raise FileNotFoundError(f"Missing matched users file: {matched_users_path}")
        
    if not window_path.exists():
        logger.error(f"Required input file not found: {window_path}")
        logger.error("Please ensure T012.6 (calculate_matched_window.py) has been completed successfully.")
        raise FileNotFoundError(f"Missing survey window file: {window_path}")
    
    try:
        fetch_all_pushshift_logs(matched_users_path, window_path, output_path)
        logger.info("Pushshift log fetching completed successfully.")
    except Exception as e:
        log_error_context(logger, "Pushshift log fetching failed", error=e)
        raise


if __name__ == "__main__":
    main()
