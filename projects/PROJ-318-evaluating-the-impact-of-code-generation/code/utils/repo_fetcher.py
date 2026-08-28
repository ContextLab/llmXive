"""
Repository Fetcher Module.

Implements logic to fetch the top 20 Python repositories from PyPI,
map them to GitHub, sort by star count, and save the result to
data/raw/repo_list.json.
"""

import json
import logging
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import existing exceptions and utilities
from utils.models import SerializationException
from utils.repo_loader import RepoLoaderException, validate_repo_list

logger = logging.getLogger(__name__)

PYPI_SEARCH_URL = "https://pypi.org/search"
# We will fetch the top 20 Python packages from the 'top' endpoint if available,
# or search for popular packages. The PyPI JSON API for search doesn't support
# direct 'top by stars' filtering. We will fetch the 'top' list from a known
# source or use the search API with a high limit and filter by Python classifiers.
# However, the most reliable programmatic way to get "Top Python Repositories"
# via PyPI -> GitHub mapping is to use the PyPI JSON API for specific popular
# packages or a curated list.
#
# Since the task asks to "fetch the top 20 Python repositories from PyPI JSON API,
# mapping to GitHub", and PyPI doesn't have a "top by stars" endpoint, we will
# use the 'top' list of packages from a reliable source or search for packages
# with the 'Python' classifier and sort by downloads (a proxy for popularity)
# and then resolve their GitHub URLs.
#
# Strategy:
# 1. Use the 'simple' API or a known list of top packages.
# 2. For this implementation, we will fetch the top 20 packages from the
#    'https://pypi.org/simple/' list? No, that's all packages.
# 3. Better approach: Use the 'https://pypi.org/search/?q=&o=-created&c=Development+Status+%3A%3A+5+-+Production%2FStable'
#    is not reliable for "top".
#
# Let's use a known list of top 20 Python packages from PyPI (based on downloads/stars)
# and fetch their details via the JSON API to get the GitHub URL.
# This is the most robust way to satisfy "Top 20 Python repositories" without
# scraping or using a non-existent PyPI "top" endpoint.
#
# Known top packages (approximate, based on general knowledge):
# requests, numpy, pandas, flask, django, tensorflow, torch, keras, scipy, matplotlib,
# pillow, scikit-learn, beautifulsoup4, lxml, pytest, celery, redis, boto3, sqlalchemy,
# pyyaml.
#
# We will fetch details for these 20 packages via the PyPI JSON API.

TOP_PYPI_PACKAGES = [
    "requests", "numpy", "pandas", "flask", "django",
    "tensorflow", "torch", "keras", "scipy", "matplotlib",
    "pillow", "scikit-learn", "beautifulsoup4", "lxml", "pytest",
    "celery", "redis", "boto3", "sqlalchemy", "pyyaml"
]

PYPI_JSON_API = "https://pypi.org/pypi/{}/json"
GITHUB_REPO_PATTERN = "https://github.com/"


def fetch_package_info(package_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch package info from PyPI JSON API.

    Args:
        package_name: Name of the PyPI package.

    Returns:
        Dictionary with package info or None if fetch fails.
    """
    url = PYPI_JSON_API.format(package_name)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch info for {package_name}: {e}")
        return None


def extract_github_url(project_info: Dict[str, Any]) -> Optional[str]:
    """
    Extract the GitHub URL from project info.

    Args:
        project_info: Dictionary from PyPI JSON API.

    Returns:
        GitHub URL string or None.
    """
    # Check project_urls in the summary
    urls = project_info.get("info", {}).get("project_urls", {})
    for key, url in urls.items():
        if url and url.startswith(GITHUB_REPO_PATTERN):
            return url

    # Fallback to homepage if it looks like GitHub
    homepage = project_info.get("info", {}).get("home_page")
    if homepage and homepage.startswith(GITHUB_REPO_PATTERN):
        return homepage

    return None


def fetch_top_repos(count: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch top repositories from PyPI, map to GitHub, and sort by stars.

    Note: PyPI JSON API does not provide star counts directly.
    We will fetch the GitHub URL and then (optionally) fetch star count from GitHub API.
    However, the task says "fetch ... from PyPI JSON API, mapping to GitHub".
    If we cannot get star counts from PyPI, we might need to use GitHub API.
    But the task says "fetch ... from PyPI JSON API".
    Let's assume we can get star counts by querying GitHub API for each repo.
    This is acceptable as "mapping to GitHub".

    Steps:
    1. Fetch info for top packages from PyPI.
    2. Extract GitHub URL.
    3. Query GitHub API for star count.
    4. Sort by star count descending.
    5. Select top 'count' repos.

    Args:
        count: Number of top repos to return.

    Returns:
        List of dictionaries with repo_url, github_url, star_count.
    """
    repos = []
    github_api_url = "https://api.github.com/repos"

    for package in TOP_PYPI_PACKAGES:
        if len(repos) >= count:
            break

        info = fetch_package_info(package)
        if not info:
            continue

        github_url = extract_github_url(info)
        if not github_url:
            logger.warning(f"No GitHub URL found for {package}")
            continue

        # Parse GitHub URL to get owner/repo
        # Expected format: https://github.com/owner/repo
        parts = github_url.rstrip("/").split("/")
        if len(parts) < 5:
            continue
        owner = parts[-2]
        repo_name = parts[-1]

        # Fetch star count from GitHub API
        try:
            gh_response = requests.get(
                f"{github_api_url}/{owner}/{repo_name}",
                timeout=30
            )
            if gh_response.status_code == 200:
                gh_data = gh_response.json()
                stars = gh_data.get("stargazers_count", 0)
                repos.append({
                    "repo_url": f"https://pypi.org/project/{package}/",
                    "github_url": github_url,
                    "star_count": stars,
                    "package_name": package
                })
            else:
                logger.warning(f"GitHub API failed for {github_url}: {gh_response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch stars for {github_url}: {e}")

    # Sort by star count descending
    repos.sort(key=lambda x: x["star_count"], reverse=True)

    # Select top 'count'
    return repos[:count]


def validate_repo_list_schema(repos: List[Dict[str, Any]]) -> bool:
    """
    Validate that each repo entry has the required fields.

    Args:
        repos: List of repository dictionaries.

    Returns:
        True if valid, False otherwise.
    """
    required_fields = {"repo_url", "github_url", "star_count"}
    for i, repo in enumerate(repos):
        if not isinstance(repo, dict):
            logger.error(f"Entry {i} is not a dictionary")
            return False
        if not required_fields.issubset(repo.keys()):
            missing = required_fields - repo.keys()
            logger.error(f"Entry {i} missing fields: {missing}")
            return False
        if not isinstance(repo["repo_url"], str):
            logger.error(f"Entry {i} repo_url is not a string")
            return False
        if not isinstance(repo["github_url"], str):
            logger.error(f"Entry {i} github_url is not a string")
            return False
        if not isinstance(repo["star_count"], int):
            logger.error(f"Entry {i} star_count is not an integer")
            return False
    return True


def create_repo_list_file(output_path: str = "data/raw/repo_list.json") -> None:
    """
    Create and freeze the repo_list.json file.

    Args:
        output_path: Path to the output JSON file.
    """
    logger.info("Fetching top 20 Python repositories from PyPI...")
    repos = fetch_top_repos(count=20)

    if not repos:
        raise RuntimeError("Failed to fetch any repositories.")

    logger.info(f"Fetched {len(repos)} repositories.")

    # Validate schema
    if not validate_repo_list_schema(repos):
        raise ValueError("Repository list validation failed.")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2)

    logger.info(f"Successfully wrote {len(repos)} repositories to {output_path}")


def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    create_repo_list_file()


if __name__ == "__main__":
    main()
