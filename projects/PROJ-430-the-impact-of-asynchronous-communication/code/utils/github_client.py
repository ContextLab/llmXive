"""
GitHub API Client with Rate Limit Handling.

This module provides a wrapper around the GitHub REST API to handle
rate limiting, authentication, and error handling for the asynchronous
communication research pipeline.

It implements exponential backoff for 403 (rate limit) and 503 (server) errors.
"""
import time
import logging
from typing import Optional, Dict, Any, List
import requests
from requests.exceptions import RequestException, HTTPError

from utils.logger import get_logger

# Constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 5
BASE_URL = "https://api.github.com"

class GitHubRateLimitError(Exception):
    """Raised when the GitHub API rate limit is exceeded and cannot be recovered."""
    def __init__(self, message: str, reset_time: Optional[int] = None):
        super().__init__(message)
        self.reset_time = reset_time

class GitHubClient:
    """
    A client for interacting with the GitHub API with built-in rate limit handling.
    
    Attributes:
        token (Optional[str]): GitHub Personal Access Token for authentication.
        logger (logging.Logger): Logger instance for tracking API interactions.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub Client.
        
        Args:
            token: GitHub Personal Access Token. If None, requests will be unauthenticated
                   (subject to stricter rate limits: 60 req/hour vs 5000 req/hour).
        """
        self.token = token
        self.session = requests.Session()
        self.logger = get_logger(__name__)
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
        else:
            self.logger.warning("No GitHub token provided. Rate limits will be strictly enforced (60 req/hr).")

    def _handle_rate_limit(self, response: requests.Response, retry_count: int) -> None:
        """
        Handles 403 (rate limit) and 503 (service unavailable) responses.
        
        Implements exponential backoff. If the rate limit is exceeded and the
        reset time has passed, it retries. If max retries is reached, it raises
        a GitHubRateLimitError.
        
        Args:
            response: The failed response object.
            retry_count: The current retry attempt number.
            
        Raises:
            GitHubRateLimitError: If max retries are exceeded or reset time is far in future.
        """
        if response.status_code == 403:
            # Check if it's a rate limit exceeded
            if 'rate' in response.json() or 'message' in response.json() and 'rate limit' in response.json().get('message', '').lower():
                reset_time = response.headers.get('X-RateLimit-Reset')
                if reset_time:
                    reset_time = int(reset_time)
                    current_time = int(time.time())
                    wait_time = reset_time - current_time
                    
                    if wait_time > 0:
                        self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds until {time.ctime(reset_time)}")
                        time.sleep(wait_time + 1) # Add 1s buffer
                        return
                    else:
                        # Reset time passed but still 403? Maybe secondary limits or stale cache.
                        # Retry once immediately.
                        if retry_count < MAX_RETRIES:
                            return
                        else:
                            raise GitHubRateLimitError("Rate limit reset time passed but request still failed.", reset_time)
                else:
                    raise GitHubRateLimitError("Rate limit exceeded but no reset time provided.", None)
            else:
                # Forbidden for other reasons (e.g., missing permissions)
                raise HTTPError(f"403 Forbidden: {response.text}", response=response)
        
        elif response.status_code == 503:
            # Service Unavailable - usually transient
            self.logger.warning("Received 503 Service Unavailable. Retrying...")
            return
        
        # For other 4xx/5xx, let the caller handle or raise
        if response.status_code >= 400:
            response.raise_for_status()

    def _request_with_backoff(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Executes a request with exponential backoff for transient errors.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/repos/owner/repo/issues')
            params: Query parameters.
            
        Returns:
            The successful response object.
            
        Raises:
            GitHubRateLimitError: If rate limit cannot be handled.
            RequestException: For network errors.
            HTTPError: For client/server errors not handled by backoff.
        """
        url = f"{BASE_URL}{endpoint}"
        retry_count = 0
        
        while retry_count < MAX_RETRIES:
            try:
                self.logger.debug(f"Requesting {method} {url} with params {params}")
                response = self.session.request(method, url, params=params, timeout=DEFAULT_TIMEOUT)
                
                if response.status_code < 400:
                    return response
                
                # Handle specific error codes
                if response.status_code in [403, 503]:
                    self._handle_rate_limit(response, retry_count)
                    # If we return from _handle_rate_limit, we continue the loop to retry
                    retry_count += 1
                    continue
                else:
                    # Other errors (404, 422, etc.) should not be retried blindly
                    response.raise_for_status()
                    
            except (RequestException, HTTPError) as e:
                # Check if it's a 403/503 wrapped in HTTPError
                if hasattr(e, 'response') and e.response is not None and e.response.status_code in [403, 503]:
                    self._handle_rate_limit(e.response, retry_count)
                    retry_count += 1
                    continue
                else:
                    raise
        
        raise GitHubRateLimitError(f"Max retries ({MAX_RETRIES}) exceeded for {endpoint}.")

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository details."""
        response = self._request_with_backoff("GET", f"/repos/{owner}/{repo}")
        return response.json()

    def get_issues(self, owner: str, repo: str, state: str = 'all', since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch issues and PRs (PRs are issues with a pull_request key) for a repository.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            state: 'open', 'closed', or 'all'.
            since: ISO 8601 timestamp to filter issues updated after.
            
        Returns:
            List of issue/PR dictionaries.
        """
        params = {"state": state, "per_page": 100}
        if since:
            params["since"] = since
        
        all_items = []
        page = 1
        
        while True:
            params["page"] = page
            response = self._request_with_backoff("GET", f"/repos/{owner}/{repo}/issues", params=params)
            items = response.json()
            
            if not items:
                break
            
            all_items.extend(items)
            
            # Check if we got fewer than 100 items, meaning it's the last page
            if len(items) < 100:
                break
            
            page += 1
            
            # Safety break for very large repos to avoid infinite loops if API behaves oddly
            if page > 1000:
                self.logger.warning("Reached 1000 pages of issues. Stopping fetch.")
                break
        
        return all_items

    def get_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """
        Fetch comments for a specific issue/PR.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: The issue/PR number.
            
        Returns:
            List of comment dictionaries.
        """
        response = self._request_with_backoff("GET", f"/repos/{owner}/{repo}/issues/{issue_number}/comments")
        return response.json()

    def get_comments_for_all_issues(self, owner: str, repo: str, state: str = 'all', since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all comments for all issues/PRs in a repository.
        
        This is a convenience method that combines get_issues and get_comments.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Issue state filter.
            since: Issue update time filter.
            
        Returns:
            List of all comment dictionaries.
        """
        issues = self.get_issues(owner, repo, state, since)
        all_comments = []
        
        for issue in issues:
            # Skip PR comments if we only want issue comments? 
            # Usually research wants all communication. 
            # PRs are also issues in GitHub API.
            try:
                comments = self.get_comments(owner, repo, issue['number'])
                all_comments.extend(comments)
            except Exception as e:
                self.logger.error(f"Failed to fetch comments for issue #{issue['number']} in {owner}/{repo}: {e}")
                continue
        
        return all_comments

def create_client(token: Optional[str] = None) -> GitHubClient:
    """
    Factory function to create a GitHubClient instance.
    
    Args:
        token: Optional GitHub token.
        
    Returns:
        Configured GitHubClient.
    """
    return GitHubClient(token)