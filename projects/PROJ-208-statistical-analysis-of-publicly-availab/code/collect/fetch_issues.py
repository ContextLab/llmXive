import json
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
import requests
import yaml

from utils.config import get_config, get_path, set_seed
from utils.validators import ensure_contracts_dir

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_REPOSITORIES = 100
RATE_LIMIT_PAUSE_SECONDS = 65  # Slightly more than 60s to be safe
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0

def load_repository_list(config: Dict[str, Any]) -> List[str]:
    """
    Load the list of repositories to fetch from the configuration.
    Ensures at least MIN_REPOSITORIES are available.
    """
    repos = config.get('repositories', [])
    if not repos:
        # Fallback: Load from a known file if config is empty
        repo_file = get_path('data', 'raw', 'repository_list.yaml')
        if repo_file.exists():
            with open(repo_file, 'r') as f:
                data = yaml.safe_load(f)
                repos = data.get('repositories', [])
        else:
            raise ValueError(
                f"No repositories found in config or at {repo_file}. "
                f"Please provide at least {MIN_REPOSITORIES} repositories."
            )
    
    if len(repos) < MIN_REPOSITORIES:
        raise ValueError(
            f"Only {len(repos)} repositories provided. "
            f"Requirement FR-001 enforces a minimum of {MIN_REPOSITORIES} repositories."
        )
    
    logger.info(f"Loaded {len(repos)} repositories. Minimum requirement ({MIN_REPOSITORIES}) met.")
    return repos

def fetch_issues_for_repo(
    repo: str, 
    api_client: requests.Session, 
    config: Dict[str, Any],
    output_dir: Path
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch all closed issues for a specific repository using GitHub API.
    Handles rate limiting and pagination.
    
    Args:
        repo: Repository string in format 'owner/repo'
        api_client: Configured requests session
        config: Configuration dictionary
        output_dir: Directory to write raw JSONL files
    
    Yields:
        Dictionary containing issue data
    """
    token = config.get('github', {}).get('token')
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Research-Agent'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    
    base_url = f'https://api.github.com/repos/{repo}/issues'
    params = {
        'state': 'closed',
        'per_page': 100,
        'sort': 'updated',
        'direction': 'desc'
    }
    
    page = 1
    total_fetched = 0
    
    while True:
        params['page'] = page
        try:
            response = api_client.get(base_url, headers=headers, params=params)
            
            # Handle Rate Limiting
            if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
                logger.warning(f"Rate limit hit for {repo}. Waiting {RATE_LIMIT_PAUSE_SECONDS}s...")
                time.sleep(RATE_LIMIT_PAUSE_SECONDS)
                response = api_client.get(base_url, headers=headers, params=params)
            
            response.raise_for_status()
            
            issues = response.json()
            
            if not issues:
                break
            
            for issue in issues:
                # Filter out pull requests (GitHub API returns PRs as issues sometimes)
                if 'pull_request' in issue:
                    continue
                
                yield issue
                total_fetched += 1
            
            page += 1
            
            # Check for remaining rate limit to decide if we should pause proactively
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 10:
                logger.info(f"Low rate limit remaining for {repo}. Waiting before next page...")
                time.sleep(RATE_LIMIT_PAUSE_SECONDS)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issues for {repo} (page {page}): {e}")
            # Exponential backoff for transient errors
            backoff = min(INITIAL_BACKOFF * (2 ** page), MAX_BACKOFF)
            logger.info(f"Retrying in {backoff}s...")
            time.sleep(backoff)
            if page > MAX_RETRIES:
                logger.error(f"Max retries exceeded for {repo}. Skipping.")
                break
            page += 1
    
    logger.info(f"Fetched {total_fetched} closed issues for {repo}.")

def main():
    """
    Main entry point for the issue fetching pipeline.
    1. Loads config.
    2. Validates repository count (>= 100).
    3. Iterates through repos and fetches issues.
    4. Writes raw issues to data/processed/issues_raw.jsonl
    """
    set_seed(42)
    config = get_config()
    ensure_contracts_dir()
    
    output_dir = get_path('data', 'raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'issues_raw.jsonl'
    
    logger.info(f"Starting issue fetch. Output: {output_file}")
    
    repos = load_repository_list(config)
    
    api_session = requests.Session()
    
    # Use a generator to stream issues to file to avoid memory blowup
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for repo in repos:
            logger.info(f"Processing repository: {repo}")
            try:
                for issue in fetch_issues_for_repo(repo, api_session, config, output_dir):
                    # Ensure timestamps are parsed or stored as strings for validity
                    # The schema expects specific fields, but we store raw first
                    issue['_fetched_at'] = datetime.now(timezone.utc).isoformat()
                    issue['_source_repo'] = repo
                    f_out.write(json.dumps(issue, default=str) + '\n')
            except Exception as e:
                logger.error(f"Failed to process {repo}: {e}")
                continue
    
    logger.info(f"Fetch complete. Total issues written to {output_file}")

if __name__ == '__main__':
    main()