"""
GitHub API client for fetching repository maintenance metadata.

This client fetches last_commit_date and last_release_date for repositories
associated with NPM packages. It implements exponential backoff for rate
limiting and handles missing repositories gracefully.
"""
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import requests
from src.utils.backoff import exponential_backoff
from src.utils.logging_config import get_logger
from src.utils.security import secure_function_logger
from src.config.settings import get_config

logger = get_logger(__name__)

class GithubClient:
    """
    Client for interacting with the GitHub API to fetch repository metadata.
    
    Attributes:
        token: GitHub API token for authentication (optional but recommended).
        rate_limit: Requests per minute limit (default 60 for unauthenticated, 5000 for authenticated).
        timeout: Request timeout in seconds.
    """
    
    def __init__(self, token: Optional[str] = None, rate_limit: Optional[int] = None):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub API token. If not provided, uses environment variable GITHUB_TOKEN.
            rate_limit: Optional override for rate limit.
        """
        config = get_config()
        self.token = token or config.github_token
        self.rate_limit = rate_limit or config.rate_limit
        self.timeout = 30
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
            logger.info("GitHub client initialized with authenticated token")
        else:
            logger.warning("GitHub client initialized without token - using unauthenticated requests")
    
    @secure_function_logger(logger)
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a rate-limited request to the GitHub API with exponential backoff.
        
        Args:
            url: The API endpoint URL.
            params: Optional query parameters.
            
        Returns:
            JSON response as a dictionary, or None if request fails after retries.
        """
        @exponential_backoff(
            max_retries=5,
            initial_delay=1.0,
            multiplier=2.0,
            max_delay=60.0,
            exceptions=(requests.exceptions.RequestException,)
        )
        def _request_with_backoff():
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 404:
                    logger.warning(f"Repository not found: {url}")
                    return None
                elif response.status_code == 403:
                    # Check for rate limit
                    if "X-RateLimit-Remaining" in response.headers:
                        remaining = int(response.headers["X-RateLimit-Remaining"])
                        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                        if remaining == 0:
                            wait_time = reset_time - int(time.time())
                            logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds.")
                            time.sleep(wait_time)
                            return _request_with_backoff()
                    
                    # Forbidden for other reasons
                    logger.error(f"Forbidden response from GitHub: {response.status_code}")
                    return None
                elif response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Unexpected status code {response.status_code} from GitHub")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                raise
        
        try:
            return _request_with_backoff()
        except Exception as e:
            logger.error(f"Failed to fetch from GitHub after retries: {str(e)}")
            return None

    def get_commit_date(self, repo_name: str) -> Optional[datetime]:
        """
        Fetch the last commit date for a repository.
        
        Args:
            repo_name: GitHub repository name in format 'owner/repo'.
            
        Returns:
            datetime object representing the last commit date, or None if not found.
        """
        if not repo_name or '/' not in repo_name:
            logger.warning(f"Invalid repo name format: {repo_name}")
            return None
        
        url = f"{self.base_url}/repos/{repo_name}/commits"
        params = {"per_page": 1, "sort": "committer-date", "direction": "desc"}
        
        logger.debug(f"Fetching commit date for {repo_name}")
        data = self._make_request(url, params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No commits found for {repo_name}")
            return None
        
        try:
            commit_date_str = data[0]["commit"]["committer"]["date"]
            commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
            logger.debug(f"Found commit date for {repo_name}: {commit_date}")
            return commit_date
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse commit date for {repo_name}: {str(e)}")
            return None

    def get_release_date(self, repo_name: str) -> Optional[datetime]:
        """
        Fetch the last release date for a repository.
        
        Args:
            repo_name: GitHub repository name in format 'owner/repo'.
            
        Returns:
            datetime object representing the last release date, or None if not found.
        """
        if not repo_name or '/' not in repo_name:
            logger.warning(f"Invalid repo name format: {repo_name}")
            return None
        
        url = f"{self.base_url}/repos/{repo_name}/releases"
        params = {"per_page": 1, "sort": "published_at", "direction": "desc"}
        
        logger.debug(f"Fetching release date for {repo_name}")
        data = self._make_request(url, params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            logger.warning(f"No releases found for {repo_name}")
            return None
        
        try:
            release_date_str = data[0]["published_at"]
            release_date = datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
            logger.debug(f"Found release date for {repo_name}: {release_date}")
            return release_date
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse release date for {repo_name}: {str(e)}")
            return None

    def fetch_repository_metadata(self, repo_name: str) -> Dict[str, Any]:
        """
        Fetch comprehensive repository metadata including commit and release dates.
        
        Args:
            repo_name: GitHub repository name in format 'owner/repo'.
            
        Returns:
            Dictionary containing repository metadata with keys:
                - repo_name: str
                - last_commit_date: datetime or None
                - last_release_date: datetime or None
                - is_private: bool (if available)
                - has_issues: bool (if available)
        """
        if not repo_name or '/' not in repo_name:
            logger.warning(f"Invalid repo name format: {repo_name}")
            return {
                "repo_name": repo_name,
                "last_commit_date": None,
                "last_release_date": None,
                "is_private": True,
                "has_issues": False,
                "error": "Invalid repo name format"
            }
        
        logger.info(f"Fetching metadata for {repo_name}")
        
        # Fetch basic repo info
        url = f"{self.base_url}/repos/{repo_name}"
        repo_data = self._make_request(url)
        
        if not repo_data:
            return {
                "repo_name": repo_name,
                "last_commit_date": None,
                "last_release_date": None,
                "is_private": True,
                "has_issues": False,
                "error": "Repository not found or inaccessible"
            }
        
        is_private = repo_data.get("private", False)
        has_issues = repo_data.get("has_issues", True)
        
        # Fetch commit and release dates
        commit_date = self.get_commit_date(repo_name)
        release_date = self.get_release_date(repo_name)
        
        return {
            "repo_name": repo_name,
            "last_commit_date": commit_date.isoformat() if commit_date else None,
            "last_release_date": release_date.isoformat() if release_date else None,
            "is_private": is_private,
            "has_issues": has_issues,
            "description": repo_data.get("description"),
            "homepage": repo_data.get("homepage"),
            "forks_count": repo_data.get("forks_count"),
            "stargazers_count": repo_data.get("stargazers_count"),
            "language": repo_data.get("language"),
            "updated_at": repo_data.get("updated_at"),
            "created_at": repo_data.get("created_at")
        }

    def batch_fetch_metadata(self, repo_names: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch metadata for multiple repositories with rate limit awareness.
        
        Args:
            repo_names: List of repository names in 'owner/repo' format.
            
        Returns:
            List of metadata dictionaries for each repository.
        """
        results = []
        rate_limit_remaining = self.rate_limit
        
        for i, repo_name in enumerate(repo_names):
            # Add delay if approaching rate limit
            if rate_limit_remaining <= 5:
                logger.info("Approaching rate limit, adding delay")
                time.sleep(1.2)  # Slightly more than 1 second to account for API updates
                rate_limit_remaining = self.rate_limit
            
            result = self.fetch_repository_metadata(repo_name)
            results.append(result)
            rate_limit_remaining -= 1
            
            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(repo_names)} repositories")
        
        return results

    def close(self):
        """Close the session."""
        self.session.close()
        logger.info("GitHub client session closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False