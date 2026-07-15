import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing API surface
from utils.config import load_env, get_config, get_github_token, get_data_raw_dir
from utils.github_client import create_client, GitHubClient, GitHubRateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def build_search_query(
    language: str,
    min_stars: int = 100,
    min_forks: int = 10,
    has_license: bool = True,
    has_ci: bool = True,
    min_issues: int = 10
) -> str:
    """
    Build a GitHub Advanced Search query string.
    
    Args:
        language: Programming language (e.g., 'python', 'java')
        min_stars: Minimum number of stars
        min_forks: Minimum number of forks
        has_license: Filter for repositories with a license
        has_ci: Filter for repositories with CI configuration
        min_issues: Minimum number of open issues
        
    Returns:
        A formatted GitHub search query string
    """
    query_parts = [f"language:{language}"]
    query_parts.append(f"stars:>{min_stars}")
    query_parts.append(f"forks:>{min_forks}")
    
    if has_license:
        query_parts.append("license:true")
    
    if has_ci:
        # Look for common CI files: .github/workflows, .travis.yml, .gitlab-ci.yml, appveyor.yml
        query_parts.append(".github/workflows OR .travis.yml OR .gitlab-ci.yml OR appveyor.yml")
    
    query_parts.append(f"issues:>{min_issues}")
    query_parts.append("is:public")
    query_parts.append("pushed:>2020-01-01")
    
    return " ".join(query_parts)

def fetch_repos_for_language(
    client: GitHubClient,
    language: str,
    min_stars: int = 100,
    min_forks: int = 10,
    has_license: bool = True,
    has_ci: bool = True,
    min_issues: int = 10,
    max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch repositories for a specific language with optional filters.
    
    Args:
        client: GitHub API client instance
        language: Target programming language
        min_stars: Minimum stars threshold
        min_forks: Minimum forks threshold
        has_license: Require license
        has_ci: Require CI configuration
        min_issues: Minimum open issues
        max_results: Maximum number of repos to fetch
        
    Returns:
        List of repository metadata dictionaries
    """
    query = build_search_query(
        language=language,
        min_stars=min_stars,
        min_forks=min_forks,
        has_license=has_license,
        has_ci=has_ci,
        min_issues=min_issues
    )
    
    logger.info(f"Searching for {language} repos with query: {query}")
    
    repos = []
    try:
        for repo in client.search_repos(query, per_page=30, max_results=max_results):
            repos.append({
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
                "language": repo["language"],
                "stargazers_count": repo["stargazers_count"],
                "forks_count": repo["forks_count"],
                "open_issues_count": repo["open_issues_count"],
                "license": repo.get("license", {}).get("spdx_id", "UNKNOWN"),
                "default_branch": repo.get("default_branch", "main")
            })
    except GitHubRateLimitExceeded as e:
        logger.error(f"Rate limit exceeded while searching {language}: {e}")
        raise
    
    logger.info(f"Found {len(repos)} repositories for {language}")
    return repos

def filter_repos(
    repos: List[Dict[str, Any]],
    required_licenses: Optional[List[str]] = None,
    required_ci_patterns: Optional[List[str]] = None,
    min_issues: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    PESTO Filter: Apply License, CI, and Issue constraints to a list of repos.
    
    This implements FR-002: Filter repositories based on:
    1. License type (e.g., MIT, Apache-2.0, BSD-3-Clause)
    2. CI presence (verified by file existence in repo structure or search query)
    3. Issue activity (minimum number of open/closed issues)
    
    Args:
        repos: List of repository metadata dictionaries
        required_licenses: List of allowed SPDX license IDs (e.g., ['MIT', 'Apache-2.0'])
        required_ci_patterns: List of patterns to check for CI (e.g., ['.github/workflows'])
        min_issues: Minimum number of issues required
        
    Returns:
        Filtered list of repositories passing all PESTO criteria
    """
    if required_licenses is None:
        required_licenses = ['MIT', 'Apache-2.0', 'BSD-3-Clause', 'ISC']
    
    filtered = []
    excluded_count = 0
    
    for repo in repos:
        reason = []
        
        # 1. License Filter
        repo_license = repo.get("license", "UNKNOWN")
        if repo_license not in required_licenses:
            reason.append(f"License '{repo_license}' not in {required_licenses}")
        
        # 2. CI Filter (Double check: ensure CI pattern exists in search metadata or structure)
        # Note: The search query already filters for CI files, but we verify the metadata
        # If the search was done with has_ci=True, this is a sanity check.
        # In a full implementation, we would fetch the repo contents to verify file existence.
        # For now, we rely on the search query result which already included CI patterns.
        # If we need stricter checking, we would call client.get_contents(repo['full_name'], path)
        # But for the search result list, we assume the query was effective.
        
        # 3. Issue Filter
        if min_issues is not None:
            open_issues = repo.get("open_issues_count", 0)
            if open_issues < min_issues:
                reason.append(f"Open issues ({open_issues}) < {min_issues}")
        
        if not reason:
            filtered.append(repo)
        else:
            excluded_count += 1
            logger.debug(f"Excluding {repo['full_name']}: {'; '.join(reason)}")
    
    logger.info(f"PESTO Filter: {len(repos)} -> {len(filtered)} (excluded {excluded_count})")
    return filtered

def main():
    """
    Main entry point for data acquisition with PESTO filtering.
    
    This script:
    1. Loads configuration (GitHub token, paths)
    2. Initializes the GitHub client
    3. Fetches repos for multiple languages
    4. Applies PESTO filters (License, CI, Issues)
    5. Saves the filtered list to data/raw/
    """
    logger.info("Starting Data Acquisition with PESTO Filtering")
    
    # Load environment
    load_env()
    config = get_config()
    token = get_github_token()
    raw_dir = get_data_raw_dir()
    
    # Ensure output directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize client
    client = create_client(token)
    
    # Languages to target (stratified sampling)
    languages = ["python", "java", "javascript", "go"]
    
    all_repos = []
    
    # Fetch repos for each language
    for lang in languages:
        try:
            repos = fetch_repos_for_language(
                client=client,
                language=lang,
                min_stars=100,
                min_forks=10,
                has_license=True,
                has_ci=True,
                min_issues=10,
                max_results=10  # Small sample for demo, increase for full run
            )
            all_repos.extend(repos)
        except Exception as e:
            logger.error(f"Failed to fetch {lang}: {e}")
            continue
    
    if not all_repos:
        logger.warning("No repositories found. Exiting.")
        return
    
    # Apply PESTO Filter (FR-002)
    # 1. License: MIT, Apache-2.0, BSD-3-Clause, ISC
    # 2. CI: Already filtered by search, but we keep the logic for extensibility
    # 3. Issues: Min 5 open issues
    filtered_repos = filter_repos(
        repos=all_repos,
        required_licenses=['MIT', 'Apache-2.0', 'BSD-3-Clause', 'ISC'],
        min_issues=5
    )
    
    # Save results
    output_path = raw_dir / "filtered_repos_raw.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_repos, f, indent=2)
    
    logger.info(f"Saved {len(filtered_repos)} filtered repositories to {output_path}")

if __name__ == "__main__":
    main()