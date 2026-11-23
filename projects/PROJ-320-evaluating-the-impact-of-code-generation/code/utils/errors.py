"""
Custom Error Classes for the project.
"""
import time
from typing import Optional, Dict, Any

class GitHubAPIError(Exception):
    """Base error for GitHub API issues."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class RateLimitExceeded(GitHubAPIError):
    """Raised when GitHub rate limit is hit."""
    pass

class AuthError(GitHubAPIError):
    """Raised when authentication fails."""
    pass

class ResourceNotFoundError(GitHubAPIError):
    """Raised when a resource (repo, PR) is not found."""
    pass

class WatchdogTimeoutError(Exception):
    """Raised when the watchdog timer expires."""
    pass

def handle_github_error(response: Any) -> None:
    """
    Handles GitHub API errors based on response object.
    """
    if response is None:
        raise GitHubAPIError("No response received from GitHub API.")
    
    status_code = getattr(response, 'status_code', 0)
    text = getattr(response, 'text', '')
    
    if status_code == 401:
        raise AuthError("Authentication failed (401).")
    elif status_code == 403:
        if 'rate limit' in text.lower():
            raise RateLimitExceeded("Rate limit exceeded (403).")
        else:
            raise AuthError("Forbidden (403) - check permissions.")
    elif status_code == 404:
        raise ResourceNotFoundError("Resource not found (404).")
    elif status_code >= 500:
        raise GitHubAPIError(f"Server error (5xx): {text}")
    else:
        raise GitHubAPIError(f"Unexpected error (status={status_code}): {text}")
