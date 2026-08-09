"""
GitHub API Client with Rate Limit Handling.
"""
import time
import logging
from typing import Optional, Dict, Any, List
import requests
from requests.exceptions import RequestException, HTTPError
from utils.logger import get_logger

logger = get_logger(__name__)

class GitHubRateLimitError(Exception):
    """Raised when GitHub API rate limit is exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after

class GitHubClient:
    """
    Wrapper for GitHub API requests with automatic rate limit handling.
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
        else:
            # Unauthenticated requests have lower rate limits
            self.session.headers.update({
                "Accept": "application/vnd.github.v3+json"
            })
        
        logger.info("GitHubClient initialized.")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs a GET request to the GitHub API.
        Handles rate limiting by sleeping and retrying.
        """
        url = f"{self.base_url}{endpoint}"
        retries = 0
        max_retries = 5
        
        while retries < max_retries:
            try:
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                
                if response.status_code == 404:
                    logger.warning(f"Resource not found: {endpoint}")
                    return []
                
                # Other errors
                response.raise_for_status()
                
            except HTTPError as e:
                if e.response.status_code == 403:
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit exceeded (HTTPError). Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                logger.error(f"HTTP Error: {e}")
                return []
            except RequestException as e:
                logger.error(f"Request Exception: {e}")
                retries += 1
                time.sleep(2 ** retries) # Exponential backoff
                continue
        
        raise GitHubRateLimitError("Max retries exceeded due to rate limits.")

def create_client() -> GitHubClient:
    """
    Factory function to create a GitHubClient instance.
    Reads token from environment or config.
    """
    import os
    token = os.getenv("GITHUB_TOKEN")
    return GitHubClient(token=token)
