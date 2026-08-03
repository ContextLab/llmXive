"""
GitHub API Client for fetching repository maintenance metadata.

This module implements the GithubClient to retrieve `last_commit_date` and
`last_release_date` for NPM packages by mapping them to their GitHub repositories.
It adheres to the project's backoff strategy and caching mechanisms.
"""
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import requests
import logging

from src.utils.backoff import exponential_backoff
from src.utils.cache_manager import get_cache_manager
from src.config.settings import get_config

logger = logging.getLogger(__name__)

class GithubClient:
    """
    Client for interacting with the GitHub REST API to fetch repository metadata.

    Attributes:
        api_key (str): GitHub Personal Access Token (PAT).
        rate_limit (int): Maximum requests per minute.
        session (requests.Session): Persistent HTTP session.
        cache_manager (CacheManager): Utility for caching API responses.
    """

    def __init__(self):
        config = get_config()
        self.api_key = config.github_token
        self.rate_limit = config.rate_limit
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"token {self.api_key}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "llmXive-Research-Agent"
            })
        else:
            logger.warning("No GitHub token provided. Rate limits will be strictly enforced (60 req/hr).")

        self.cache_manager = get_cache_manager()
        self.base_url = "https://api.github.com"

    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key for a given URL."""
        return f"github_{url}"

    def _fetch_with_cache(self, url: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch data from GitHub API with caching and exponential backoff.

        Args:
            url: The API endpoint URL.
            params: Optional query parameters.

        Returns:
            Parsed JSON response or None if fetch fails after retries.
        """
        cache_key = self._get_cache_key(url)
        
        # Check cache first
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for {url}")
            return cached_data

        try:
            @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
            def _request():
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 404:
                    return None # Not found, not a retryable error
                if response.status_code == 403:
                    if "rate limit" in response.text.lower():
                        raise requests.exceptions.RequestException("Rate limit exceeded")
                    raise requests.exceptions.RequestException(f"Forbidden: {response.text}")
                response.raise_for_status()
                return response.json()

            data = _request()
            
            if data:
                self.cache_manager.set(cache_key, data)
                logger.debug(f"Successfully fetched and cached {url}")
            else:
                logger.info(f"Repository not found or empty: {url}")
            
            return data

        except Exception as e:
            logger.error(f"Failed to fetch {url} after retries: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse ISO 8601 date string from GitHub API.

        Args:
            date_str: ISO 8601 formatted date string (e.g., "2023-10-01T12:00:00Z").

        Returns:
            datetime object in UTC or None if invalid/missing.
        """
        if not date_str:
            return None
        try:
            # GitHub returns ISO 8601 format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.astimezone(timezone.utc)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    def get_commit_date(self, owner: str, repo: str) -> Optional[datetime]:
        """
        Fetch the date of the most recent commit for a repository.

        Args:
            owner: GitHub repository owner (username or organization).
            repo: GitHub repository name.

        Returns:
            datetime of the last commit in UTC, or None if not found.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": 1, "sha": "HEAD"}
        
        data = self._fetch_with_cache(url, params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.debug(f"No commits found for {owner}/{repo}")
            return None

        commit_data = data[0]
        date_str = commit_data.get("commit", {}).get("author", {}).get("date")
        return self._parse_date(date_str)

    def get_release_date(self, owner: str, repo: str) -> Optional[datetime]:
        """
        Fetch the date of the most recent release for a repository.

        Args:
            owner: GitHub repository owner.
            repo: GitHub repository name.

        Returns:
            datetime of the last release in UTC, or None if no releases exist.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/releases"
        params = {"per_page": 1}
        
        data = self._fetch_with_cache(url, params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.debug(f"No releases found for {owner}/{repo}")
            return None

        release_data = data[0]
        date_str = release_data.get("published_at")
        return self._parse_date(date_str)

    def fetch_repository_metadata(self, npm_package_name: str) -> Optional[Dict[str, Any]]:
        """
        Resolve an NPM package to its GitHub repository and fetch metadata.

        This queries the NPM registry to find the GitHub URL in the package metadata,
        then parses the owner/repo and fetches commit/release dates.

        Args:
            npm_package_name: The name of the package on npm (e.g., "lodash").

        Returns:
            A dictionary containing:
                - 'last_commit_date': datetime or None
                - 'last_release_date': datetime or None
                - 'github_url': str or None
                - 'owner': str or None
                - 'repo': str or None
            Returns None if the package has no GitHub repository linked.
        """
        # 1. Fetch NPM metadata to find the GitHub URL
        # We use the NPM registry API directly here to avoid circular dependency
        # on NpmClient, though in a full pipeline NpmClient would provide this.
        npm_url = f"https://registry.npmjs.org/{npm_package_name}"
        npm_data = self._fetch_with_cache(npm_url)
        
        if not npm_data:
            logger.warning(f"Could not fetch NPM metadata for {npm_package_name}")
            return None

        # Extract GitHub URL from 'repository' field
        repository_info = npm_data.get("repository", {})
        if not isinstance(repository_info, dict):
            # Sometimes it's a string, sometimes an object with 'url'
            url_str = repository_info if isinstance(repository_info, str) else None
            if not url_str:
                return None
        else:
            url_str = repository_info.get("url")
        
        if not url_str:
            return None

        # Parse GitHub URL: github.com/owner/repo.git or git+https://github.com/owner/repo.git
        if "github.com" not in url_str:
            return None

        # Clean up URL (remove git+ prefix, .git suffix)
        url_str = url_str.replace("git+", "").replace(".git", "")
        
        # Extract owner and repo
        # Format: https://github.com/owner/repo
        parts = url_str.split("/")
        if len(parts) < 2:
            return None

        # Handle cases where URL might include protocol
        owner = parts[-2]
        repo = parts[-1]

        # 2. Fetch GitHub dates
        last_commit = self.get_commit_date(owner, repo)
        last_release = self.get_release_date(owner, repo)

        return {
            "last_commit_date": last_commit,
            "last_release_date": last_release,
            "github_url": f"https://github.com/{owner}/{repo}",
            "owner": owner,
            "repo": repo
        }

    def batch_fetch_metadata(self, package_names: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch metadata for a list of package names.

        Args:
            package_names: List of NPM package names.

        Returns:
            List of metadata dictionaries, preserving order.
        """
        results = []
        for name in package_names:
            logger.info(f"Fetching GitHub metadata for {name}")
            metadata = self.fetch_repository_metadata(name)
            results.append({
                "package_name": name,
                "metadata": metadata
            })
            # Small delay to be polite to the API if not authenticated
            if not self.api_key:
                time.sleep(1.0)
        return results