"""
Repository Metadata Enrichment Script (T045)

Fetches language, star_count, and contributor_count for repositories
identified in the cleaned dataset via GitHub API.

Output: data/processed/repo_metadata.json
Schema: {repo_id, language, star_count, contributor_count}

Dependencies:
- utils.config: get_config
- utils.api_client: GitHubAPIClient (from T005)
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

# Project imports
from utils.config import get_config
from utils.api_client import GitHubAPIClient
from utils.validators import validate_dataset_schema

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/enrich_metadata.log')
    ]
)
logger = logging.getLogger(__name__)

def load_repository_list(cleaned_data_path: str) -> Set[str]:
    """
    Load unique repository identifiers from the cleaned dataset.
    Expects CSV format with a 'repository' or 'repo' column.
    """
    import pandas as pd
    path = Path(cleaned_data_path)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {cleaned_data_path}")

    logger.info(f"Loading repository list from {cleaned_data_path}")
    df = pd.read_csv(path)

    # Identify the repository column
    repo_col = None
    candidates = ['repository', 'repo', 'repo_name', 'full_name']
    for col in candidates:
        if col in df.columns:
            repo_col = col
            break

    if repo_col is None:
        raise ValueError(f"Could not find repository column in {df.columns}. Expected one of {candidates}.")

    # Extract unique repositories
    repos = set(df[repo_col].dropna().unique())
    logger.info(f"Found {len(repos)} unique repositories to enrich.")

    if len(repos) == 0:
        raise ValueError("No repositories found in the cleaned dataset.")

    return repos

def fetch_repo_metadata(api_client: GitHubAPIClient, repo: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a single repository via GitHub API.
    Returns dict with: repo_id, language, star_count, contributor_count.
    """
    try:
        # Fetch repo details (language, stargazers_count)
        repo_data = api_client.get_repo(repo)
        if not repo_data:
            logger.warning(f"Failed to fetch details for {repo}")
            return None

        language = repo_data.get('language') or 'Unknown'
        star_count = repo_data.get('stargazers_count', 0)

        # Fetch contributor count
        # Note: API returns paginated list; we just need the count.
        # Using per_page=1 to minimize data transfer, but we need to check 'Link' header or total count.
        # GitHub API /repos/{owner}/{repo}/contributors returns a list.
        # To get total count without fetching all, we can look at the 'Link' header or just fetch the first page and check if we have more.
        # However, for efficiency, we can try to get the count from the 'total_count' if available in a search, but standard contributors endpoint doesn't give total count in body.
        # We will fetch the first page with per_page=1 to get the link header or just count if it's small.
        # Better approach for "count": Use the search API? No, search is for issues.
        # Standard way: Fetch contributors with per_page=1, check 'Link' header for 'last' page.
        # Simpler, robust way for this task: Fetch contributors with per_page=1. If the 'Link' header exists, parse the 'last' page number. If not, count is 1.
        # Actually, the simplest robust way without parsing headers is to just fetch the first page and if we get 1 item, we assume there might be more.
        # Let's use the API to get the count directly if possible.
        # GitHub API /repos/{owner}/{repo}/contributors?per_page=1
        # The response headers contain 'Link' with 'last' page.
        
        contributors_url = f"https://api.github.com/repos/{repo}/contributors"
        headers = {"Accept": "application/vnd.github.v3+json"}
        headers.update(api_client.headers)
        
        response = api_client.session.get(contributors_url, headers=headers, params={'per_page': 1})
        api_client._handle_rate_limit(response)
        
        if response.status_code == 200:
            # Check Link header for total count
            link_header = response.headers.get('Link', '')
            if 'last' in link_header:
                # Parse last page number
                import re
                match = re.search(r'page=(\d+)>', link_header)
                if match:
                    contributor_count = int(match.group(1))
                else:
                    # Fallback: if we got 1 item and no link header, count is 1
                    contributor_count = 1
            else:
                # No link header means only one page
                contributor_count = len(response.json())
        else:
            logger.warning(f"Failed to fetch contributors for {repo}: {response.status_code}")
            contributor_count = 0

        return {
            "repo_id": repo,
            "language": language,
            "star_count": star_count,
            "contributor_count": contributor_count
        }

    except Exception as e:
        logger.error(f"Error fetching metadata for {repo}: {e}", exc_info=True)
        return None

def enrich_metadata(repos: Set[str], api_client: GitHubAPIClient, output_path: str) -> Dict[str, Any]:
    """
    Enrich metadata for all repositories.
    Implements rate limit handling and retry logic via api_client.
    """
    logger.info(f"Starting enrichment for {len(repos)} repositories...")
    
    results = []
    failed_repos = []
    
    for i, repo in enumerate(repos):
        logger.info(f"Processing [{i+1}/{len(repos)}]: {repo}")
        
        metadata = fetch_repo_metadata(api_client, repo)
        
        if metadata:
            results.append(metadata)
        else:
            failed_repos.append(repo)
        
        # Small delay to be polite, though api_client handles rate limits
        if i < len(repos) - 1:
            time.sleep(0.1)

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": results,
            "failed_repos": failed_repos,
            "total_processed": len(repos),
            "successful": len(results),
            "failed": len(failed_repos)
        }, f, indent=2)
    
    logger.info(f"Enrichment complete. Results saved to {output_path}")
    if failed_repos:
        logger.warning(f"Failed to enrich {len(failed_repos)} repositories.")
    
    return {
        "total_processed": len(repos),
        "successful": len(results),
        "failed": len(failed_repos)
    }

def main():
    """Main entry point for T045."""
    config = get_config()
    
    # Paths
    cleaned_data_path = config.get_path('processed_cleaned_issues')
    output_path = config.get_path('repo_metadata')
    
    logger.info(f"Configuration loaded. Cleaned data: {cleaned_data_path}")
    logger.info(f"Output path: {output_path}")
    
    # Load repository list
    try:
        repos = load_repository_list(cleaned_data_path)
    except Exception as e:
        logger.error(f"Failed to load repository list: {e}")
        sys.exit(1)
    
    # Initialize API client
    try:
        api_client = GitHubAPIClient()
    except Exception as e:
        logger.error(f"Failed to initialize GitHub API client: {e}")
        sys.exit(1)
    
    # Enrich metadata
    try:
        stats = enrich_metadata(repos, api_client, output_path)
        logger.info(f"Enrichment statistics: {stats}")
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Task T045 completed successfully.")

if __name__ == "__main__":
    main()
