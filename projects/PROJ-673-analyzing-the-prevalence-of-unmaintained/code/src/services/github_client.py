"""
GitHub Client for fetching repository maintenance metadata.

Implements the GithubClient service to retrieve:
- last_commit_date: Date of the most recent commit
- last_release_date: Date of the most recent release/tag

Adheres to Constitution Principle VI (API Snapshot Integrity) by 
relying on the caching layer (src.utils.cache) for raw response storage.
"""
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import requests
from src.utils.backoff import exponential_backoff
from src.utils.cache import save_response_to_cache, load_from_cache
from src.utils.logging_config import log_api_call
from src.utils.api_metrics import APIMetricsAggregator
from src.config.settings import get_config

class GithubClient:
    """
    Client for interacting with the GitHub API to fetch repository metadata.
    
    Features:
    - Rate limit awareness and backoff
    - Local caching of API responses
    - Robust error handling for network and API errors
    """
    
    def __init__(self):
        self.config = get_config()
        self.token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.aggregator = APIMetricsAggregator()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
        else:
            # Warning for unauthenticated requests (rate limited to 60/min)
            pass

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a cache key based on endpoint and parameters."""
        return {
            "endpoint": endpoint,
            "params": params,
            "service": "github"
        }

    def _fetch_with_backoff(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Fetch data from GitHub API with exponential backoff and caching.
        
        Args:
            url: The API endpoint URL
            params: Query parameters for the request
            
        Returns:
            JSON response as a dictionary
            
        Raises:
            requests.exceptions.RequestException: If all retries fail
        """
        cache_key = self._get_cache_key(url, params or {})
        
        # Check cache first
        cached_data = load_from_cache(cache_key)
        if cached_data is not None:
            log_api_call("github", url, "cache_hit", 200)
            self.aggregator.record_success("github")
            return cached_data

        def _make_request():
            log_api_call("github", url, "request", None)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()

        try:
            data = exponential_backoff(_make_request)
            
            # Cache the successful response
            save_response_to_cache(cache_key, data)
            
            log_api_call("github", url, "success", 200)
            self.aggregator.record_success("github")
            return data
            
        except Exception as e:
            log_api_call("github", url, "error", 0, str(e))
            self.aggregator.record_failure("github")
            raise

    def get_commit_date(self, owner: str, repo: str) -> Optional[datetime]:
        """
        Fetch the date of the most recent commit for a repository.
        
        Args:
            owner: GitHub username or organization name
            repo: Repository name
            
        Returns:
            datetime object of the last commit, or None if not found
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": 1, "sha": "main"}  # Try main first, fallback logic handled by caller if needed
        
        try:
            data = self._fetch_with_backoff(url, params)
            if isinstance(data, list) and len(data) > 0:
                commit_date_str = data[0]["commit"]["committer"]["date"]
                return datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
        except (KeyError, IndexError, ValueError):
            return None

    def get_release_date(self, owner: str, repo: str) -> Optional[datetime]:
        """
        Fetch the date of the most recent release for a repository.
        
        Args:
            owner: GitHub username or organization name
            repo: Repository name
            
        Returns:
            datetime object of the last release, or None if not found
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/releases"
        params = {"per_page": 1}
        
        try:
            data = self._fetch_with_backoff(url, params)
            if isinstance(data, list) and len(data) > 0:
                release_date_str = data[0]["published_at"]
                if release_date_str:
                    return datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
        except (KeyError, IndexError, ValueError):
            return None

    def get_repository_metadata(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Fetch basic metadata for a repository (e.g., default branch).
        
        Args:
            owner: GitHub username or organization name
            repo: Repository name
            
        Returns:
            Dictionary containing repository metadata
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            data = self._fetch_with_backoff(url)
            return {
                "default_branch": data.get("default_branch"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "archived": data.get("archived"),
                "private": data.get("private")
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def fetch_maintenance_dates(self, owner: str, repo: str) -> Dict[str, Optional[datetime]]:
        """
        Convenience method to fetch both commit and release dates.
        
        Args:
            owner: GitHub username or organization name
            repo: Repository name
            
        Returns:
            Dictionary with 'last_commit_date' and 'last_release_date' keys
        """
        commit_date = self.get_commit_date(owner, repo)
        release_date = self.get_release_date(owner, repo)
        
        return {
            "last_commit_date": commit_date,
            "last_release_date": release_date
        }