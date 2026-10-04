"""
Custom error classes for GitHub API interactions and pipeline errors.
"""
import time
from typing import Optional, Dict, Any

class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class RateLimitExceeded(GitHubAPIError):
    """Exception raised when GitHub rate limit is exceeded."""
    def __init__(self, message: str, reset_time: Optional[float] = None):
        super().__init__(message)
        self.reset_time = reset_time

class AuthError(GitHubAPIError):
    """Exception raised for authentication failures."""
    pass

class ResourceNotFoundError(GitHubAPIError):
    """Exception raised when a requested resource is not found."""
    pass

class WatchdogTimeoutError(Exception):
    """Exception raised when execution exceeds the time limit."""
    pass

def handle_github_error(
    response: Any,
    default_message: str = "GitHub API error"
) -> GitHubAPIError:
    """
    Convert a GitHub API response into the appropriate exception.
    
    Args:
        response: The requests.Response object
        default_message: Default message if status code is unknown
        
    Returns:
        The appropriate exception instance
    """
    status_code = response.status_code
    text = response.text.lower()
    
    if status_code == 404:
        return ResourceNotFoundError(f"Resource not found: {response.url}")
    elif status_code == 403:
        if "rate limit" in text:
            reset_time = response.headers.get("X-RateLimit-Reset")
            return RateLimitExceeded(
                "GitHub rate limit exceeded",
                reset_time=float(reset_time) if reset_time else None
            )
        elif "bad credentials" in text:
            return AuthError("Authentication failed")
        else:
            return GitHubAPIError(f"Forbidden: {text}", status_code)
    elif status_code == 401:
        return AuthError("Unauthorized")
    elif status_code >= 500:
        return GitHubAPIError(f"Server error: {status_code}", status_code)
    else:
        return GitHubAPIError(default_message, status_code)
