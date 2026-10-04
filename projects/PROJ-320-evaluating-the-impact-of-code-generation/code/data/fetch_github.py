"""
T013: Implement fetch_github.py to fetch up to 200 PRs from prioritized list,
handling pagination, API backoff, and saving raw JSON payloads to data/raw/ with SHA-256 checksums.
"""
import os
import time
import json
import hashlib
import signal
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from utils.config import get_repo_list, get_api_settings, get_path
from utils.logging import get_logger, setup_logging
from utils.errors import GitHubAPIError, RateLimitExceeded, AuthError, ResourceNotFoundError, WatchdogTimeoutError, handle_github_error
from utils.checksum import calculate_checksum

# Watchdog global state
_watchdog_start_time = None
_watchdog_timeout_seconds = 300  # 5 minutes max execution
_watchdog_signal_active = False

def watchdog_handler(signum, frame):
    """Handle watchdog timeout signal."""
    raise WatchdogTimeoutError(f"Execution exceeded time limit of {_watchdog_timeout_seconds} seconds.")

def setup_watchdog(timeout_seconds: int = 300):
    """Setup the execution watchdog timer."""
    global _watchdog_timeout_seconds, _watchdog_start_time, _watchdog_signal_active
    _watchdog_timeout_seconds = timeout_seconds
    _watchdog_start_time = time.time()
    _watchdog_signal_active = True
    
    # Only set signal handlers on Unix-like systems
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, watchdog_handler)
        signal.alarm(timeout_seconds)
    else:
        # Fallback for Windows: check manually in the loop
        pass

def check_watchdog():
    """Check if watchdog timeout has been reached."""
    global _watchdog_start_time, _watchdog_signal_active
    if not _watchdog_signal_active:
        return
    
    if hasattr(signal, 'SIGALRM'):
        return  # Signal handler will raise if timeout reached
    
    # Manual check for Windows
    if time.time() - _watchdog_start_time > _watchdog_timeout_seconds:
        raise WatchdogTimeoutError(f"Execution exceeded time limit of {_watchdog_timeout_seconds} seconds.")

def get_session(retries: int = 5, backoff_factor: float = 0.5) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.adapters.Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def calculate_checksum(data: bytes) -> str:
    """Calculate SHA-256 checksum of data."""
    return hashlib.sha256(data).hexdigest()

def fetch_prs_from_repo(
    repo: str,
    session: requests.Session,
    max_prs: int = 200,
    api_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch PRs from a specific GitHub repository.
    Handles pagination and rate limiting.
    """
    base_url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmXive-research-bot"
    }
    
    if api_token:
        headers["Authorization"] = f"token {api_token}"
    
    all_prs = []
    page = 1
    per_page = 100
    
    logger = get_logger(__name__)
    logger.info(f"Fetching PRs from {repo}, page {page}")
    
    while len(all_prs) < max_prs:
        check_watchdog()
        
        params = {
            "state": "all",
            "per_page": min(per_page, max_prs - len(all_prs)),
            "page": page
        }
        
        try:
            response = session.get(base_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Repository not found: {repo}")
            elif response.status_code == 403:
                if "rate limit" in response.text.lower():
                    raise RateLimitExceeded(f"Rate limit exceeded for {repo}")
                elif "bad credentials" in response.text.lower():
                    raise AuthError(f"Authentication failed for {repo}")
                else:
                    raise GitHubAPIError(f"GitHub API error (403): {response.text}")
            elif response.status_code >= 500:
                raise GitHubAPIError(f"GitHub API server error: {response.status_code}")
            elif response.status_code != 200:
                raise GitHubAPIError(f"Unexpected status code: {response.status_code}")
            
            prs = response.json()
            if not prs:
                break  # No more PRs
            
            all_prs.extend(prs)
            
            if len(prs) < params["per_page"]:
                break  # Last page
            
            page += 1
            
            # Respect rate limits
            rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            if rate_limit_remaining < 10:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                wait_time = max(0, reset_time - int(time.time()) + 5)
                logger.info(f"Rate limit low, waiting {wait_time}s")
                time.sleep(wait_time)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {repo}: {e}")
            raise GitHubAPIError(f"Network error: {str(e)}")
    
    logger.info(f"Fetched {len(all_prs)} PRs from {repo}")
    return all_prs[:max_prs]

def get_next_repo(current_repo: str, repo_list: List[str]) -> Optional[str]:
    """Get the next repo in the list after the current one."""
    try:
        idx = repo_list.index(current_repo)
        if idx + 1 < len(repo_list):
            return repo_list[idx + 1]
    except ValueError:
        pass
    return None

def save_prs_to_raw(
    prs: List[Dict[str, Any]],
    output_path: Path,
    source_repo: str
) -> str:
    """
    Save PRs to a raw JSON file and return the checksum.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data with metadata
    data = {
        "source_repo": source_repo,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pr_count": len(prs),
        "prs": prs
    }
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    with open(output_path, 'wb') as f:
        f.write(json_bytes)
    
    checksum = calculate_checksum(json_bytes)
    
    # Save checksum manifest
    manifest_path = output_path.with_suffix('.sha256')
    manifest_data = {
        "file": str(output_path),
        "checksum": checksum,
        "algorithm": "sha256",
        "source_repo": source_repo,
        "pr_count": len(prs)
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    return checksum

def run_batch_fetch(
    output_path: Path,
    max_total_prs: int = 200,
    timeout_seconds: int = 300
):
    """
    Run the batch fetch process across prioritized repos.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting batch fetch for up to {max_total_prs} PRs")
    
    # Setup watchdog
    setup_watchdog(timeout_seconds)
    
    # Get configuration
    repo_list = get_repo_list()
    api_settings = get_api_settings()
    api_token = api_settings.get("token")
    
    if not repo_list:
        raise RuntimeError("No repositories configured in get_repo_list()")
    
    session = get_session()
    all_prs = []
    current_repo = None
    
    try:
        for repo in repo_list:
            if len(all_prs) >= max_total_prs:
                break
            
            current_repo = repo
            remaining = max_total_prs - len(all_prs)
            
            logger.info(f"Fetching from {repo} (need {remaining} more)")
            
            try:
                repo_prs = fetch_prs_from_repo(
                    repo, 
                    session, 
                    max_prs=remaining,
                    api_token=api_token
                )
                all_prs.extend(repo_prs)
                
                if len(repo_prs) > 0:
                    # Save intermediate results if we have data
                    intermediate_path = output_path.parent / f"prs_raw_{repo.replace('/', '_')}.json"
                    save_prs_to_raw(repo_prs, intermediate_path, repo)
                    logger.info(f"Saved {len(repo_prs)} PRs from {repo}")
                
            except (ResourceNotFoundError, RateLimitExceeded, AuthError) as e:
                logger.warning(f"Skipping {repo} due to error: {e}")
                next_repo = get_next_repo(repo, repo_list)
                if next_repo:
                    logger.info(f"Switching to next repo: {next_repo}")
                else:
                    logger.warning("No more repos to try")
                    break
            
            # Small delay between repos to be nice to API
            time.sleep(1)
            
    except WatchdogTimeoutError:
        logger.error("Watchdog timeout reached")
        if not all_prs:
            raise
    except Exception as e:
        logger.error(f"Unexpected error during fetch: {e}")
        if not all_prs:
            raise
    
    if not all_prs:
        raise RuntimeError("No PRs were successfully fetched from any repository")
    
    # Save final combined dataset
    logger.info(f"Saving {len(all_prs)} total PRs to {output_path}")
    checksum = save_prs_to_raw(all_prs, output_path, "combined")
    
    logger.info(f"Fetch complete. Checksum: {checksum}")
    return checksum

def main():
    """Main entry point for the fetch script."""
    # Setup logging
    log_config = setup_logging(script_name="fetch_github")
    logger = get_logger(__name__)
    
    try:
        # Parse arguments
        import argparse
        parser = argparse.ArgumentParser(description="Fetch PRs from GitHub")
        parser.add_argument(
            "--output",
            type=str,
            default="data/raw/prs_raw.json",
            help="Output path for raw PR data"
        )
        parser.add_argument(
            "--max-prs",
            type=int,
            default=200,
            help="Maximum number of PRs to fetch"
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=300,
            help="Watchdog timeout in seconds"
        )
        args = parser.parse_args()
        
        output_path = Path(args.output)
        
        # Run fetch
        checksum = run_batch_fetch(
            output_path=output_path,
            max_total_prs=args.max_prs,
            timeout_seconds=args.timeout
        )
        
        print(f"Successfully fetched and saved PRs to {output_path}")
        print(f"Checksum: {checksum}")
        
    except KeyboardInterrupt:
        logger.warning("Fetch interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        # Re-raise for proper exit code
        raise

if __name__ == "__main__":
    main()
