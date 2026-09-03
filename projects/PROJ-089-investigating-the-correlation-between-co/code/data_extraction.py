"""
data_extraction.py
Implements GitHub repository selection, cloning, and initial metric extraction.
"""
import os
import time
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd

from config import get_config_summary, ensure_directories
from utils import get_logger, validate_tools_and_log_wrapper

# Configure logging
logger = get_logger(__name__)

# Constants
GITHUB_API_URL = "https://api.github.com/search/repositories"
DEFAULT_TIMEOUT = 30  # seconds

def query_github_repos(
    min_stars: int = 500,
    min_age_years: int = 2,
    languages: Optional[List[str]] = None,
    per_page: int = 100,
    max_repos: int = 10
) -> List[Dict[str, Any]]:
    """
    Query GitHub API for repositories matching criteria.

    Args:
        min_stars: Minimum number of stars (default 500)
        min_age_years: Minimum age in years (default 2)
        languages: List of languages to filter by (e.g., ['Python', 'Java'])
        per_page: Results per page (max 100)
        max_repos: Maximum number of repos to return

    Returns:
        List of repository metadata dictionaries
    """
    config = get_config_summary()
    # Use config values if available, otherwise defaults
    min_stars = config.get('github_min_stars', min_stars)
    min_age_years = config.get('github_min_age_years', min_age_years)
    languages = config.get('github_languages', languages or ['Python', 'Java', 'JavaScript', 'Go', 'Rust'])

    logger.info(f"Querying GitHub API for repos with >= {min_stars} stars, "
                f"age >= {min_age_years} years, languages: {languages}")

    all_repos = []
    page = 1
    current_year = time.localtime().tm_year
    min_created_timestamp = time.mktime(time.strptime(f"{current_year - min_age_years}-01-01", "%Y-%m-%d"))

    while len(all_repos) < max_repos:
        query_parts = []
        for lang in languages:
            query_parts.append(f"language:{lang}")
        query_parts.append(f"stars:>{min_stars - 1}")
        query = " OR ".join(query_parts)

        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page,
            'page': page
        }

        try:
            response = requests.get(GITHUB_API_URL, params=params, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if 'items' not in data:
                logger.warning("No 'items' in GitHub API response")
                break

            items = data['items']
            if not items:
                logger.info("No more repositories found")
                break

            for item in items:
                if len(all_repos) >= max_repos:
                    break

                created_at_str = item.get('created_at', '')
                try:
                    created_at = time.mktime(time.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ"))
                except ValueError:
                    continue

                repo_age_years = (time.time() - created_at) / (365.25 * 24 * 3600)
                if repo_age_years < min_age_years:
                    continue

                all_repos.append({
                    'repo_id': item['id'],
                    'full_name': item['full_name'],
                    'html_url': item['html_url'],
                    'stargazers_count': item['stargazers_count'],
                    'language': item.get('language', 'Unknown'),
                    'created_at': created_at_str,
                    'age_years': round(repo_age_years, 2),
                    'clone_url': item['clone_url']
                })

            if not data.get('next_page'):
                break
            page += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            break

    logger.info(f"Found {len(all_repos)} repositories matching criteria")
    return all_repos

def clone_repository(clone_url: str, target_dir: Path) -> bool:
    """
    Clone a repository to the target directory.

    Args:
        clone_url: Git clone URL
        target_dir: Destination directory

    Returns:
        True if successful, False otherwise
    """
    if target_dir.exists():
        logger.warning(f"Directory {target_dir} already exists, skipping clone")
        return True

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        # Use git clone with depth 1 for efficiency (we need recent history)
        # However, for full history analysis later, we might need full clone
        # For T010, we just need to verify cloning works
        cmd = ['git', 'clone', '--depth', '100', clone_url, str(target_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"Git clone failed: {result.stderr}")
            shutil.rmtree(target_dir, ignore_errors=True)
            return False
        logger.info(f"Successfully cloned {clone_url} to {target_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        return False

def extract_git_metrics(repo_path: Path) -> Dict[str, Any]:
    """
    Extract basic git metrics from a repository.
    Placeholder for T011 implementation.
    """
    return {
        'repo_path': str(repo_path),
        'total_commits': 0,
        'files_analyzed': 0
    }

def aggregate_file_metrics(repos_data: List[Dict]) -> pd.DataFrame:
    """
    Aggregate file-level metrics into a DataFrame.
    Placeholder for T011 implementation.
    """
    return pd.DataFrame()

def save_repos_metadata(repos: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save repository metadata to a CSV file.

    Args:
        repos: List of repository metadata dictionaries
        output_path: Path to output CSV file
    """
    if not repos:
        logger.warning("No repositories to save")
        return

    df = pd.DataFrame(repos)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(repos)} repositories to {output_path}")

def process_single_repo(repo_data: Dict[str, Any], base_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single repository: clone and extract metrics.

    Args:
        repo_data: Repository metadata
        base_dir: Base directory for clones

    Returns:
        Processed repository data or None if failed
    """
    repo_id = repo_data['repo_id']
    clone_dir = base_dir / f"repo_{repo_id}"

    if not clone_repository(repo_data['clone_url'], clone_dir):
        return None

    metrics = extract_git_metrics(clone_dir)
    metrics.update(repo_data)
    return metrics

def run_data_extraction(
    output_dir: Path,
    min_stars: int = 500,
    min_age_years: int = 2,
    languages: Optional[List[str]] = None,
    max_repos: int = 5
) -> List[Dict[str, Any]]:
    """
    Main function to run data extraction pipeline.

    Args:
        output_dir: Directory for outputs
        min_stars: Minimum stars threshold
        min_age_years: Minimum age threshold
        languages: Languages to filter
        max_repos: Maximum repos to process

    Returns:
        List of processed repository data
    """
    ensure_directories(output_dir)
    logger.info("Starting data extraction pipeline")

    # Query GitHub
    repos = query_github_repos(
        min_stars=min_stars,
        min_age_years=min_age_years,
        languages=languages,
        max_repos=max_repos
    )

    if not repos:
        logger.warning("No repositories found matching criteria")
        return []

    # Save metadata
    metadata_path = output_dir / "repos_metadata.csv"
    save_repos_metadata(repos, metadata_path)

    # Process repos (clone and extract)
    processed_repos = []
    clone_base = output_dir / "clones"
    ensure_directories(clone_base)

    for repo_data in repos:
        result = process_single_repo(repo_data, clone_base)
        if result:
            processed_repos.append(result)

    logger.info(f"Data extraction complete. Processed {len(processed_repos)} repos.")
    return processed_repos

def run_data_extraction_wrapper(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Wrapper function for integration with main pipeline.
    """
    import json
    from config import get_config_summary

    cfg = config if config else get_config_summary()
    output_dir = Path(cfg.get('output_dir', 'data/raw'))
    max_repos = cfg.get('max_repos', 5)

    run_data_extraction(
        output_dir=Path(output_dir),
        max_repos=max_repos
    )

def main():
    """Entry point for script execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract repository data from GitHub")
    parser.add_argument('--output-dir', type=str, default='data/raw', help='Output directory')
    parser.add_argument('--min-stars', type=int, default=500, help='Minimum stars')
    parser.add_argument('--min-age', type=int, default=2, help='Minimum age in years')
    parser.add_argument('--languages', type=str, nargs='+', default=None, help='Languages to filter')
    parser.add_argument('--max-repos', type=int, default=5, help='Max repos to process')

    args = parser.parse_args()

    run_data_extraction(
        output_dir=Path(args.output_dir),
        min_stars=args.min_stars,
        min_age_years=args.min_age,
        languages=args.languages,
        max_repos=args.max_repos
    )

if __name__ == "__main__":
    main()
