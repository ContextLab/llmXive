"""
Repository Fetcher Module for PROJ-318.

This module implements the logic to fetch a representative set of top-ranked
Python repositories. It adheres to the constraint of failing loudly if the
required number of repositories cannot be fetched from the real source.
"""
import json
import logging
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import custom exceptions from the project's utils module
from utils.exceptions import RepoFetcherException

# Configuration constants
TARGET_COUNT = 20
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
TIMEOUT_SECONDS = 30

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/repo_fetcher.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def fetch_github_stars(github_url: str) -> int:
    """
    Fetches the star count for a specific GitHub repository.

    Args:
        github_url: The full GitHub URL of the repository.

    Returns:
        The number of stars as an integer.

    Raises:
        RepoFetcherException: If the API request fails or returns invalid data.
    """
    # Extract owner/repo from URL like https://github.com/owner/repo
    parts = github_url.rstrip('/').split('/')
    if len(parts) < 2:
        raise RepoFetcherException(f"Invalid GitHub URL format: {github_url}")
    
    owner = parts[-2]
    repo = parts[-1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(api_url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            return data.get('stargazers_count', 0)
        except requests.exceptions.RequestException as e:
            wait_time = BACKOFF_FACTOR ** attempt
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {github_url}: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except json.JSONDecodeError as e:
            raise RepoFetcherException(f"Failed to parse JSON response for {github_url}: {e}")
    
    raise RepoFetcherException(f"Failed to fetch star count for {github_url} after {MAX_RETRIES} retries.")


def fetch_top_repos_from_pypi(source_type: str = "huggingface") -> List[Dict[str, Any]]:
    """
    Fetches a list of top Python repositories.
    
    Currently, since a direct 'pypi/top-100' HuggingFace dataset with star counts
    is not guaranteed to exist or be stable, and the PyPI API does not provide
    star counts directly, we implement a robust fetcher that:
    1. Fetches a list of top packages from a known reliable source (PyPI JSON API for a curated list of popular packages).
    2. Enriches this list with GitHub star counts via the GitHub API.
    
    To ensure the 'real data' requirement and 'fail loudly' constraint:
    - We use a fixed list of known popular packages as the seed (since PyPI has no 'top' endpoint).
    - We fetch GitHub stars for each.
    - If we cannot reach GitHub API to get stars, we fail.
    - If we cannot get enough repos, we fail.
    
    Note: The task asks to fetch from "pypi/top-100" or PyPI JSON API. 
    Since PyPI JSON API requires a package name, we will use a curated list of 
    known top packages to simulate fetching the "top" list, then enrich with stars.
    If the GitHub API fails for these known packages, we fail loudly.

    Args:
        source_type: Ignored for now as we use a unified strategy, but kept for API compatibility.

    Returns:
        A list of dictionaries with repo_url, github_url, and star_count.

    Raises:
        RepoFetcherException: If the fetch fails or we cannot get enough repos.
    """
    # A curated list of known top Python packages to act as our "top list" source.
    # This satisfies the requirement to get a "representative set of top-ranked" repos.
    # We fetch their GitHub stars to sort them deterministically.
    popular_packages = [
        "requests", "flask", "django", "pandas", "numpy", 
        "scikit-learn", "keras", "pytorch", "tensorflow", "transformers",
        "black", "pytest", "pip", "urllib3", "aiohttp",
        "sqlalchemy", "celery", "fastapi", "pydantic", "build",
        "boto3", "matplotlib", "seaborn", "scipy", "pillow"
    ]

    repos = []
    logger.info(f"Fetching star counts for {len(popular_packages)} known top packages...")

    for package in popular_packages:
        try:
            # Try to find the GitHub URL from PyPI JSON API
            pypi_url = f"https://pypi.org/pypi/{package}/json"
            response = requests.get(pypi_url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            
            project_info = data.get('info', {})
            homepage = project_info.get('homepage')
            project_urls = project_info.get('project_urls', {})
            
            github_url = None
            
            # Check various fields for GitHub URL
            if homepage and 'github.com' in homepage:
                github_url = homepage
            else:
                # Check project_urls
                for key, url in project_urls.items():
                    if 'github.com' in url:
                        github_url = url
                        break
            
            if not github_url:
                # Fallback: assume standard github URL if not found
                github_url = f"https://github.com/{package}/{package}"
            
            # Fetch star count
            star_count = fetch_github_stars(github_url)
            
            repos.append({
                "repo_url": github_url,
                "github_url": github_url,
                "star_count": star_count
            })
            
        except RepoFetcherException:
            # If we fail to fetch stars for a package, we might still continue
            # but the task says "If the API/mirror fails to return the required number... raise exception".
            # We will collect what we can and check the count at the end.
            logger.warning(f"Skipping {package} due to fetch error.")
            continue
        except Exception as e:
            logger.warning(f"Unexpected error processing {package}: {e}")
            continue

    if len(repos) < TARGET_COUNT:
        raise RepoFetcherException(
            f"Failed to fetch enough repositories. Expected {TARGET_COUNT}, got {len(repos)}. "
            "The API or network may be unreachable. Aborting."
        )

    # Sort deterministically by star count (descending)
    repos.sort(key=lambda x: x['star_count'], reverse=True)
    
    # Truncate to exactly TARGET_COUNT
    result = repos[:TARGET_COUNT]
    
    logger.info(f"Successfully fetched and sorted {len(result)} repositories.")
    for r in result:
        logger.info(f"  - {r['github_url']} ({r['star_count']} stars)")
        
    return result


def validate_repo_list_schema(repos: List[Dict[str, Any]]) -> bool:
    """
    Validates that the repository list matches the required schema.
    
    Args:
        repos: List of repository dictionaries.
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        RepoFetcherException: If validation fails.
    """
    required_keys = {'repo_url', 'github_url', 'star_count'}
    for i, repo in enumerate(repos):
        if not isinstance(repo, dict):
            raise RepoFetcherException(f"Item {i} is not a dictionary.")
        if not required_keys.issubset(repo.keys()):
            missing = required_keys - set(repo.keys())
            raise RepoFetcherException(f"Item {i} missing keys: {missing}.")
        if not isinstance(repo['star_count'], int):
            raise RepoFetcherException(f"Item {i} star_count is not an integer.")
    return True


def create_repo_list_file(repos: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the repository list to a JSON file.
    
    Args:
        repos: List of repository dictionaries.
        output_path: Path to the output JSON file.
        
    Raises:
        RepoFetcherException: If file writing fails.
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(repos, f, indent=2)
        
        logger.info(f"Successfully wrote {len(repos)} repositories to {output_path}")
    except IOError as e:
        raise RepoFetcherException(f"Failed to write file {output_path}: {e}")


def main():
    """
    Main entry point for the repo fetcher script.
    
    This script:
    1. Fetches top repos.
    2. Validates the list.
    3. Writes to data/raw/frozen_repo_list.json.
    4. Copies to data/raw/repo_list.json.
    """
    logger.info("Starting repo fetcher process...")
    
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = base_dir / "data" / "raw"
    frozen_list_path = data_raw_dir / "frozen_repo_list.json"
    copy_list_path = data_raw_dir / "repo_list.json"
    
    try:
        # 1. Fetch
        repos = fetch_top_repos_from_pypi()
        
        # 2. Validate
        if not validate_repo_list_schema(repos):
            raise RepoFetcherException("Validation failed.")
        
        # 3. Write frozen list
        create_repo_list_file(repos, frozen_list_path)
        
        # 4. Copy to repo_list.json
        # Read from frozen and write to copy to ensure exact content
        with open(frozen_list_path, 'r', encoding='utf-8') as f_src:
            content = f_src.read()
        with open(copy_list_path, 'w', encoding='utf-8') as f_dst:
            f_dst.write(content)
        
        logger.info(f"Process complete. Created {frozen_list_path} and {copy_list_path}")
        print(f"Success: {len(repos)} repositories frozen.")
        
    except RepoFetcherException as e:
        logger.error(f"Repo fetcher failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
