"""
GitHub PR Fetching Module with centralized session management and error handling.
"""
import os
import time
import json
import hashlib
import signal
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from requests.exceptions import RequestException

from utils.config import get_repo_list, get_api_settings, get_path
from utils.logging import get_logger, setup_logging
from utils.checksum import calculate_checksum
from utils.errors import handle_github_error, RateLimitExceeded, WatchdogTimeoutError

# Global session for connection pooling
_SESSION: Optional[requests.Session] = None
_WATCHDOG_START_TIME: Optional[float] = None
_MAX_RUNTIME_SECONDS: int = 3600  # 1 hour default limit


def get_session() -> requests.Session:
    """Get or create the shared HTTP session."""
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update({'Accept': 'application/vnd.github.v3+json'})
    return _SESSION


def watchdog_handler(signum, frame):
    """Signal handler for watchdog timeout."""
    raise WatchdogTimeoutError(f"Pipeline exceeded { _MAX_RUNTIME_SECONDS } seconds")


def setup_watchdog(timeout_seconds: int = 3600):
    """Set up the global watchdog timer."""
    global _MAX_RUNTIME_SECONDS
    _MAX_RUNTIME_SECONDS = timeout_seconds
    _WATCHDOG_START_TIME = time.time()
    signal.signal(signal.SIGALRM, watchdog_handler)
    signal.alarm(_MAX_RUNTIME_SECONDS)


def check_watchdog():
    """Check if the watchdog has timed out."""
    if _WATCHDOG_START_TIME is None:
        return
    elapsed = time.time() - _WATCHDOG_START_TIME
    if elapsed > _MAX_RUNTIME_SECONDS:
        signal.alarm(0)  # Disable alarm
        raise WatchdogTimeoutError(f"Pipeline exceeded {_MAX_RUNTIME_SECONDS} seconds")


def calculate_checksum(data: Dict[str, Any]) -> str:
    """Calculate SHA-256 checksum for a data payload."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def fetch_prs_from_repo(repo: str, max_prs: int = 200) -> List[Dict[str, Any]]:
    """
    Fetch PRs from a specific GitHub repository using the shared session.
    
    Args:
        repo: Repository in format 'owner/repo'
        max_prs: Maximum number of PRs to fetch
    
    Returns:
        List of PR dictionaries
    """
    session = get_session()
    api_settings = get_api_settings()
    base_url = api_settings.get('base_url', 'https://api.github.com')
    token = api_settings.get('token')
    
    if token:
        session.headers.update({'Authorization': f'token {token}'})
    
    url = f"{base_url}/repos/{repo}/pulls"
    params = {'state': 'all', 'per_page': 100}
    
    all_prs = []
    page = 1
    max_retries = 3
    
    while len(all_prs) < max_prs:
        params['page'] = page
        attempt = 0
        
        while attempt < max_retries:
            try:
                check_watchdog()
                response = session.get(url, params=params)
                response.raise_for_status()
                prs = response.json()
                
                if not prs:
                    break
                
                all_prs.extend(prs)
                if len(prs) < 100:
                    break
                
                page += 1
                break
                
            except (RequestException, RateLimitExceeded) as e:
                attempt += 1
                wait_time = handle_github_error(e, attempt, max_retries)
                if wait_time > 0:
                    logging.getLogger(__name__).warning(f"Retry {attempt}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                logging.getLogger(__name__).error(f"Unexpected error fetching PRs: {e}")
                raise
    
    return all_prs[:max_prs]


def save_prs_to_raw(prs: List[Dict[str, Any]], repo: str):
    """
    Save fetched PRs to raw data directory with checksums.
    
    Args:
        prs: List of PR dictionaries
        repo: Repository name
    """
    output_dir = get_path('data/raw')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{repo.replace('/', '_')}_prs.json"
    filepath = os.path.join(output_dir, filename)
    
    checksum = calculate_checksum({'prs': prs})
    payload = {
        'repo': repo,
        'count': len(prs),
        'checksum': checksum,
        'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'prs': prs
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    
    logging.getLogger(__name__).info(f"Saved {len(prs)} PRs to {filepath} (checksum: {checksum[:16]}...)")


def run_batch_fetch(max_prs_per_repo: int = 200):
    """
    Run the fetch pipeline across all configured repositories.
    
    Args:
        max_prs_per_repo: Maximum PRs to fetch per repository
    """
    logger = setup_logging('fetch_github')
    logger.info("Starting GitHub PR fetch pipeline")
    
    setup_watchdog()
    repos = get_repo_list()
    logger.info(f"Fetching from repos: {repos}")
    
    total_prs = 0
    
    for repo in repos:
        try:
            logger.info(f"Fetching from {repo}...")
            prs = fetch_prs_from_repo(repo, max_prs_per_repo)
            
            if not prs:
                logger.warning(f"No PRs found for {repo}")
                continue
            
            save_prs_to_raw(prs, repo)
            total_prs += len(prs)
            
            # Check watchdog between repos
            check_watchdog()
            
        except WatchdogTimeoutError:
            logger.critical("Watchdog timeout reached. Stopping pipeline.")
            break
        except Exception as e:
            logger.error(f"Failed to fetch from {repo}: {e}")
            # Continue to next repo on failure
            continue
    
    logger.info(f"Pipeline complete. Total PRs fetched: {total_prs}")


def main():
    """Entry point for the script."""
    run_batch_fetch()


if __name__ == "__main__":
    main()