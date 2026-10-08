"""
GitHub PR Fetcher with Fallback Logic (T018)

Fetches PRs from prioritized repositories, handles rate limits, and implements
fallback logic to switch repos if LLM count is insufficient.
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

# Import from project utils
from utils.logging import setup_logging, get_logger
from utils.config import get_repo_list, get_path
from utils.errors import GitHubAPIError, RateLimitExceeded, AuthError, ResourceNotFoundError
from utils.checksum import calculate_checksum
from utils.seeds import set_global_seed

# Constants
MAX_RETRIES = 3
BASE_DELAY = 1.0
TARGET_LLM_COUNT = 10
BATCH_SIZE = 200
GITHUB_API_BASE = "https://api.github.com"

def watchdog_handler(signum, frame):
    """Handle watchdog timeout signal."""
    raise TimeoutError("Fetch operation exceeded time limit")

def setup_watchdog(seconds: int = 300):
    """Setup a watchdog timer for the fetch operation."""
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, watchdog_handler)
        signal.alarm(seconds)
    else:
        logging.warning("SIGALRM not available on this platform; watchdog disabled")

def check_watchdog():
    """Check if watchdog timer has expired."""
    pass  # Handled by signal

def get_session() -> requests.Session:
    """Create a persistent session for GitHub API requests."""
    session = requests.Session()
    token = os.getenv("GITHUB_TOKEN")
    if token:
        session.headers.update({"Authorization": f"token {token}"})
    session.headers.update({"Accept": "application/vnd.github.v3+json"})
    return session

def calculate_checksum(data: bytes) -> str:
    """Calculate SHA-256 checksum for data."""
    return hashlib.sha256(data).hexdigest()

def save_prs_to_raw(prs: List[Dict], repo: str, output_dir: str):
    """Save fetched PRs to raw JSON with checksum."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    filename = f"prs_raw_{repo.replace('/', '_')}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(prs, f, indent=2)
    
    checksum = calculate_checksum(open(filepath, 'rb').read())
    checksum_file = f"{filepath}.sha256"
    with open(checksum_file, 'w') as f:
        f.write(checksum)
    
    logging.info(f"Saved {len(prs)} PRs to {filepath} (checksum: {checksum[:8]}...)")

def get_next_repo(current_repo: str, repo_list: List[str]) -> Optional[str]:
    """Get the next repository in the list after the current one."""
    try:
        idx = repo_list.index(current_repo)
        if idx + 1 < len(repo_list):
            return repo_list[idx + 1]
    except ValueError:
        pass
    return None

def fetch_prs_from_repo(
    session: requests.Session, 
    repo: str, 
    limit: int = BATCH_SIZE,
    max_retries: int = MAX_RETRIES
) -> List[Dict]:
    """
    Fetch PRs from a single GitHub repository.
    
    Args:
        session: Authenticated GitHub API session
        repo: Repository in format 'owner/name'
        limit: Maximum number of PRs to fetch
        max_retries: Maximum retry attempts for rate limits
        
    Returns:
        List of PR dictionaries
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/pulls"
    params = {"state": "all", "per_page": 100}
    prs = []
    retries = 0
    
    logger = logging.getLogger(__name__)
    
    while len(prs) < limit:
        try:
            response = session.get(url, params=params)
            
            if response.status_code == 200:
                batch = response.json()
                if not batch:
                    break  # No more PRs
                prs.extend(batch)
                logger.info(f"Fetched {len(batch)} PRs from {repo} (total: {len(prs)})")
                
                # Check for next page
                if len(batch) < 100:
                    break
                # Get next page URL from Link header if present
                link_header = response.headers.get('Link', '')
                if 'rel="next"' in link_header:
                    next_url = link_header.split('<')[1].split('>')[0]
                    url = next_url
                else:
                    break
            elif response.status_code == 403:
                if 'rate limit' in response.text.lower():
                    retries += 1
                    if retries > max_retries:
                        raise RateLimitExceeded(f"Rate limit exceeded for {repo} after {max_retries} retries")
                    delay = BASE_DELAY * (2 ** retries)
                    logger.warning(f"Rate limit hit. Waiting {delay}s before retry {retries}/{max_retries}")
                    time.sleep(delay)
                    continue
                else:
                    raise AuthError(f"Authentication error for {repo}: {response.status_code}")
            elif response.status_code == 404:
                raise ResourceNotFoundError(f"Repository not found: {repo}")
            else:
                raise GitHubAPIError(f"GitHub API error for {repo}: {response.status_code}")
                
        except requests.RequestException as e:
            retries += 1
            if retries > max_retries:
                raise GitHubAPIError(f"Network error after {max_retries} retries: {str(e)}")
            delay = BASE_DELAY * (2 ** retries)
            logger.warning(f"Network error. Waiting {delay}s before retry {retries}/{max_retries}")
            time.sleep(delay)
    
    return prs[:limit]

def classify_pr_source_type(pr: Dict) -> str:
    """
    Classify if a PR is likely from an LLM based on simple heuristics.
    This is a placeholder implementation; actual logic should be in classify_prs.py.
    For now, we use bot names as a simple heuristic.
    """
    user = pr.get('user', {}).get('login', '').lower()
    llm_indicators = ['copilot', 'github-actions', 'dependabot']
    human_indicators = ['dependabot']  # Dependabot is considered human for this context
    
    # Dependabot is human
    if any(ind in user for ind in human_indicators):
        return 'human'
    
    # LLM indicators
    if any(ind in user for ind in llm_indicators):
        return 'llm'
        
    # Default to human for non-bot users
    if 'bot' not in user:
        return 'human'
        
    # For other bots, default to human unless we have specific LLM indicators
    return 'human'

def run_batch_fetch(
    output_dir: str = None,
    target_llm_count: int = TARGET_LLM_COUNT,
    max_repos: int = None
) -> Dict[str, Any]:
    """
    Main fetch loop with fallback logic (T018).
    
    Fetches PRs from repos in order until target LLM count is met or list exhausted.
    
    Args:
        output_dir: Directory to save raw PR data
        target_llm_count: Minimum number of LLM-classified PRs needed
        max_repos: Maximum number of repos to try
        
    Returns:
        Dictionary with fetch statistics
    """
    logger = logging.getLogger(__name__)
    repo_list = get_repo_list()
    all_prs = []
    current_repo_idx = 0
    llm_count = 0
    stats = {
        'repos_tried': 0,
        'repos_success': 0,
        'repos_failed': 0,
        'total_prs_fetched': 0,
        'llm_prs': 0,
        'human_prs': 0,
        'final_repo': None,
        'switched_repos': False
    }
    
    if output_dir is None:
        output_dir = get_path('raw')
        
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting batch fetch. Target LLM count: {target_llm_count}")
    logger.info(f"Repo list: {repo_list}")
    
    while llm_count < target_llm_count and current_repo_idx < len(repo_list):
        repo = repo_list[current_repo_idx]
        stats['repos_tried'] += 1
        logger.info(f"Fetching from repo {current_repo_idx + 1}/{len(repo_list)}: {repo}")
        
        try:
            session = get_session()
            prs = fetch_prs_from_repo(session, repo, limit=BATCH_SIZE)
            
            if not prs:
                logger.warning(f"No PRs found in {repo}, moving to next repo")
                current_repo_idx += 1
                continue
                
            # Classify PRs
            repo_llm_count = 0
            repo_human_count = 0
            for pr in prs:
                source_type = classify_pr_source_type(pr)
                pr['source_type'] = source_type
                if source_type == 'llm':
                    repo_llm_count += 1
                else:
                    repo_human_count += 1
                    
            all_prs.extend(prs)
            llm_count += repo_llm_count
            stats['llm_prs'] += repo_llm_count
            stats['human_prs'] += repo_human_count
            stats['repos_success'] += 1
            stats['total_prs_fetched'] += len(prs)
            stats['final_repo'] = repo
            
            logger.info(f"Repo {repo}: {len(prs)} PRs (LLM: {repo_llm_count}, Human: {repo_human_count})")
            
            # Check if we need to switch repos
            if repo_llm_count < 10:
                logger.warning(f"LLM count ({repo_llm_count}) below threshold (10) in {repo}")
                if llm_count < target_llm_count:
                    next_repo = get_next_repo(repo, repo_list)
                    if next_repo:
                        logger.info(f"Switching to next repo: {next_repo}")
                        stats['switched_repos'] = True
                        current_repo_idx += 1
                        continue
                    else:
                        logger.warning("No more repos available to try")
                        break
            else:
                logger.info(f"LLM count ({repo_llm_count}) meets threshold in {repo}")
                break  # Target met
                
        except Exception as e:
            stats['repos_failed'] += 1
            logger.error(f"Failed to fetch from {repo}: {str(e)}")
            next_repo = get_next_repo(repo, repo_list)
            if next_repo:
                logger.info(f"Switching to next repo due to error: {next_repo}")
                stats['switched_repos'] = True
                current_repo_idx += 1
            else:
                logger.error("No more repos available after failure")
                break
    
    # Save all fetched PRs
    if all_prs:
        save_prs_to_raw(all_prs, "combined", output_dir)
        
    stats['target_met'] = llm_count >= target_llm_count
    stats['final_llm_count'] = llm_count
    
    logger.info(f"Fetch complete. Stats: {stats}")
    return stats

def main():
    """CLI entry point for fetch_github.py."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch GitHub PRs with fallback logic")
    parser.add_argument("--output", type=str, default=None, help="Output directory for raw data")
    parser.add_argument("--target-llm", type=int, default=TARGET_LLM_COUNT, help="Target LLM PR count")
    parser.add_argument("--max-repos", type=int, default=None, help="Maximum repos to try")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Setup logging
    log_config = setup_logging(script_name="fetch_github")
    
    # Setup watchdog
    setup_watchdog(seconds=300)
    
    # Set seed
    set_global_seed(args.seed)
    
    try:
        stats = run_batch_fetch(
            output_dir=args.output,
            target_llm_count=args.target_llm,
            max_repos=args.max_repos
        )
        
        # Save stats
        stats_path = os.path.join(args.output or get_path('raw'), "fetch_stats.json")
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
            
        print(f"Fetch complete. Stats saved to {stats_path}")
        return 0
        
    except Exception as e:
        logging.error(f"Fetch failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())