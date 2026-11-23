"""
GitHub API Client with Rate Limit Handling.

Implements robust rate-limit handling, exponential backoff, and 
automatic retry logic for GitHub API interactions.
"""
import time
import logging
from typing import Optional, Dict, Any, List
import requests
from requests.exceptions import RequestException, HTTPError
from utils.logger import get_logger

logger = get_logger(__name__)

class GitHubRateLimitError(Exception):
    """Raised when GitHub API rate limit is exceeded after max retries."""
    def __init__(self, message: str, retry_after: Optional[int] = None, remaining: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.remaining = remaining

class GitHubClient:
    """
    Wrapper for GitHub API requests with automatic rate limit handling.
    
    Features:
    - Automatic retry on 403 rate limit errors with respect for Retry-After header
    - Exponential backoff for network errors
    - Token authentication support
    - Pagination helper (iter_pages)
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "llmXive-Research-Agent"
        })
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            logger.info("GitHubClient initialized with authentication token.")
        else:
            logger.warning("GitHubClient initialized WITHOUT authentication token. Rate limits may be low.")

    def _handle_rate_limit(self, response: requests.Response) -> int:
        """
        Handles 403 rate limit responses.
        Returns the number of seconds to sleep.
        Raises GitHubRateLimitError if max retries exceeded.
        """
        retry_after = int(response.headers.get('Retry-After', 60))
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        
        logger.warning(
            f"Rate limit exceeded. Retry-After: {retry_after}s, "
            f"Remaining: {remaining}, "
            f"Reset: {response.headers.get('X-RateLimit-Reset', 'unknown')}"
        )
        
        return retry_after

    def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Performs a GET request to the GitHub API.
        Handles rate limiting by sleeping and retrying.
        
        Args:
            endpoint: API endpoint (e.g., '/repos/{owner}/{repo}/issues')
            params: Query parameters
            max_retries: Maximum number of retry attempts for rate limits
        
        Returns:
            List of JSON objects from the API response.
        
        Raises:
            GitHubRateLimitError: If rate limit is exceeded after max retries.
            HTTPError: For other HTTP errors (4xx, 5xx).
        """
        url = f"{self.base_url}{endpoint}"
        retries = 0
        backoff_factor = 2
        
        while True:
            try:
                response = self.session.get(url, params=params)
                
                # Success
                if response.status_code == 200:
                    # Handle pagination links if present
                    return response.json()
                
                # Rate Limit Exceeded (403)
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    if retries >= max_retries:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        raise GitHubRateLimitError(
                            f"Max retries ({max_retries}) exceeded for rate limit.",
                            retry_after=retry_after
                        )
                    
                    sleep_time = self._handle_rate_limit(response)
                    logger.info(f"Sleeping for {sleep_time} seconds before retry {retries + 1}...")
                    time.sleep(sleep_time)
                    retries += 1
                    continue
                
                # Resource Not Found (404)
                if response.status_code == 404:
                    logger.warning(f"Resource not found: {endpoint}")
                    return []
                
                # Server Error (5xx) - Retry with backoff
                if 500 <= response.status_code < 600:
                    if retries >= max_retries:
                        response.raise_for_status()
                    sleep_time = (backoff_factor ** retries)
                    logger.warning(f"Server error {response.status_code}. Retrying after {sleep_time}s...")
                    time.sleep(sleep_time)
                    retries += 1
                    continue
                
                # Other Client Errors
                response.raise_for_status()
                
            except HTTPError as e:
                if e.response is not None and e.response.status_code == 403:
                    if retries >= max_retries:
                        retry_after = int(e.response.headers.get('Retry-After', 60))
                        raise GitHubRateLimitError(
                            f"Max retries ({max_retries}) exceeded for rate limit (HTTPError).",
                            retry_after=retry_after
                        )
                    sleep_time = self._handle_rate_limit(e.response)
                    logger.info(f"Sleeping for {sleep_time} seconds before retry {retries + 1}...")
                    time.sleep(sleep_time)
                    retries += 1
                    continue
                
                logger.error(f"HTTP Error: {e}")
                raise
            
            except RequestException as e:
                # Network error
                if retries >= max_retries:
                    raise
                sleep_time = (backoff_factor ** retries)
                logger.warning(f"Request Exception: {e}. Retrying after {sleep_time}s...")
                time.sleep(sleep_time)
                retries += 1
                continue

    def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches all pages of a paginated endpoint.
        
        Args:
            endpoint: API endpoint
            params: Base query parameters
            per_page: Items per page (max 100 for GitHub API)
            max_pages: Maximum number of pages to fetch (None for unlimited)
        
        Returns:
            List of all items across all pages.
        """
        all_items: List[Dict[str, Any]] = []
        current_params = params.copy() if params else {}
        current_params['per_page'] = min(per_page, 100)
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max pages limit ({max_pages}). Stopping pagination.")
                break
            
            try:
                # Add page number to params
                current_params['page'] = page
                items = self.get(endpoint, params=current_params)
                
                if not items:
                    logger.info(f"No more items found on page {page}.")
                    break
                
                all_items.extend(items)
                logger.info(f"Fetched page {page}: {len(items)} items. Total: {len(all_items)}")
                
                # Check for 'Link' header for next page
                # GitHub API uses Link header for pagination
                # If we got fewer items than per_page, we are likely at the end
                if len(items) < current_params['per_page']:
                    break
                
                page += 1
                
            except GitHubRateLimitError:
                # Re-raise if we hit rate limits in pagination
                raise
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        return all_items

def create_client() -> GitHubClient:
    """
    Factory function to create a GitHubClient instance.
    Reads token from environment variable GITHUB_TOKEN.
    
    Returns:
        GitHubClient instance.
    """
    import os
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN environment variable not set. Using unauthenticated requests.")
    return GitHubClient(token=token)
