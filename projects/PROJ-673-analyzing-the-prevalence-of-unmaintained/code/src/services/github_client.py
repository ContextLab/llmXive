import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import requests
from src.utils.backoff import exponential_backoff
from src.config.settings import get_config
import logging

logger = logging.getLogger(__name__)
config = get_config()

class GithubClient:
    """Client for interacting with the GitHub API."""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "llmXive-GitHub-Research-Client/1.0"
        })
        
        token = config.github_token
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})

    def _handle_request_error(self, error: Exception, repo_name: str, operation: str) -> None:
        """Log detailed error information for debugging."""
        if isinstance(error, requests.HTTPError):
            status_code = error.response.status_code if error.response else "Unknown"
            logger.error(f"HTTP {status_code} during '{operation}' for repo '{repo_name}'")
            if error.response and error.response.status_code == 404:
                logger.warning(f"Repository '{repo_name}' not found.")
            elif error.response and error.response.status_code == 403:
                rate_limit_remaining = error.response.headers.get("X-RateLimit-Remaining", "Unknown")
                logger.warning(f"Rate limit issue for '{repo_name}'. Remaining: {rate_limit_remaining}")
            elif error.response and error.response.status_code == 422:
                logger.warning(f"Validation error for '{repo_name}' during '{operation}'.")
        elif isinstance(error, requests.ConnectionError):
            logger.error(f"Connection error during '{operation}' for repo '{repo_name}'")
        elif isinstance(error, requests.Timeout):
            logger.error(f"Timeout error during '{operation}' for repo '{repo_name}'")
        else:
            logger.error(f"Unexpected error '{type(error).__name__}' for repo '{repo_name}' during '{operation}': {str(error)}")

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def get_repository_info(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch basic repository information.
        
        Args:
            repo_name: The full name of the repository (owner/repo).
            
        Returns:
            Dictionary with repo info or None if not found.
        """
        url = f"{self.base_url}/repos/{repo_name}"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Repository '{repo_name}' not found (404).")
                return None
            self._handle_request_error(e, repo_name, "get_repository_info")
            return None
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, repo_name, "get_repository_info")
            return None

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def get_last_commit_date(self, repo_name: str) -> Optional[datetime]:
        """
        Fetch the date of the most recent commit.
        
        Args:
            repo_name: The full name of the repository (owner/repo).
            
        Returns:
            datetime object of the last commit or None if not found/error.
        """
        url = f"{self.base_url}/repos/{repo_name}/commits"
        params = {"per_page": 1, "sha": "main"}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 404:
                # Try master branch if main fails
                params["sha"] = "master"
                response = self.session.get(url, params=params, timeout=30)
            
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                commit_data = data[0].get("commit", {})
                date_str = commit_data.get("committer", {}).get("date")
                if date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Commits not found for '{repo_name}'.")
                return None
            self._handle_request_error(e, repo_name, "get_last_commit_date")
            return None
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, repo_name, "get_last_commit_date")
            return None
        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"Error parsing commit date for '{repo_name}': {str(e)}")
            return None

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def get_last_release_date(self, repo_name: str) -> Optional[datetime]:
        """
        Fetch the date of the most recent release.
        
        Args:
            repo_name: The full name of the repository (owner/repo).
            
        Returns:
            datetime object of the last release or None if not found/error.
        """
        url = f"{self.base_url}/repos/{repo_name}/releases"
        params = {"per_page": 1}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                release_data = data[0]
                date_str = release_data.get("published_at")
                if date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Releases not found for '{repo_name}'.")
                return None
            self._handle_request_error(e, repo_name, "get_last_release_date")
            return None
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, repo_name, "get_last_release_date")
            return None
        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"Error parsing release date for '{repo_name}': {str(e)}")
            return None

    def fetch_repository_metadata(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive metadata for a repository.
        
        Args:
            repo_name: The full name of the repository (owner/repo).
            
        Returns:
            Dictionary containing commit date, release date, and other metadata.
        """
        try:
            repo_info = self.get_repository_info(repo_name)
            if not repo_info:
                return None
            
            commit_date = self.get_last_commit_date(repo_name)
            release_date = self.get_last_release_date(repo_name)
            
            return {
                "name": repo_name,
                "description": repo_info.get("description"),
                "language": repo_info.get("language"),
                "stars": repo_info.get("stargazers_count"),
                "forks": repo_info.get("forks_count"),
                "last_commit_date": commit_date,
                "last_release_date": release_date,
                "created_at": repo_info.get("created_at"),
                "updated_at": repo_info.get("updated_at")
            }
        except Exception as e:
            logger.error(f"Failed to fetch metadata for '{repo_name}': {str(e)}")
            return None
