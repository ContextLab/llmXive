"""
Centralized error handling and custom exceptions for the llmXive pipeline.
"""
import time
from typing import Optional, Dict, Any
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError


class GitHubAPIError(Exception):
    """Base class for GitHub API related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitExceeded(GitHubAPIError):
    """Raised when GitHub rate limits are exceeded."""
    def __init__(self, message: str = "GitHub API rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthError(GitHubAPIError):
    """Raised when authentication fails."""
    pass


class ResourceNotFoundError(GitHubAPIError):
    """Raised when a requested resource (PR, repo) is not found."""
    pass


class WatchdogTimeoutError(Exception):
    """Raised when the global watchdog timer expires."""
    def __init__(self, message: str = "Pipeline execution exceeded maximum allowed time"):
        super().__init__(message)


def handle_github_error(e: Exception, attempt: int = 1, max_retries: int = 3) -> float:
    """
    Centralized error handling logic for GitHub API requests.
    
    Implements exponential backoff for transient errors and raises 
    specific exceptions for non-retryable failures.
    
    Args:
        e: The caught exception
        attempt: Current retry attempt number (1-based)
        max_retries: Maximum number of retries allowed
    
    Returns:
        float: Seconds to wait before retrying (0 if no retry)
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
        GitHubAPIError: For other HTTP errors
        Exception: Re-raises non-retryable errors
    """
    if isinstance(e, (Timeout, ConnectionError)):
        # Transient network error
        if attempt >= max_retries:
            raise GitHubAPIError(f"Network error after {max_retries} retries") from e
        
        wait_time = (2 ** attempt) + 1
        return wait_time
    
    elif isinstance(e, HTTPError):
        status_code = getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0
        
        if status_code == 403:
            # Rate limit
            retry_after = getattr(e.response, 'headers', {}).get('Retry-After', 60)
            raise RateLimitExceeded(retry_after=int(retry_after)) from e
        
        elif status_code == 401:
            raise AuthError("Authentication failed", status_code=401) from e
        
        elif status_code == 404:
            raise ResourceNotFoundError("Resource not found", status_code=404) from e
        
        elif 500 <= status_code < 600:
            # Server error - retryable
            if attempt >= max_retries:
                raise GitHubAPIError(f"Server error {status_code} after {max_retries} retries") from e
            wait_time = (2 ** attempt) + 1
            return wait_time
        
        else:
            raise GitHubAPIError(f"HTTP Error {status_code}", status_code=status_code) from e
    
    else:
        # Unknown error - re-raise immediately
        raise e
