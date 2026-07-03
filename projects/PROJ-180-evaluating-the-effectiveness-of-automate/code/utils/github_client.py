"""
Authenticated GitHub REST API client with rate limit handling and pagination.

This module provides a robust client for interacting with the GitHub API,
handling authentication, rate limit monitoring, automatic retries, and
pagination of results.
"""
import os
import time
import logging
from typing import Any, Dict, Generator, List, Optional, Union
from pathlib import Path

import requests
from requests.exceptions import RequestException, Timeout

# Configure logging
logger = logging.getLogger(__name__)


class GitHubRateLimitExceeded(Exception):
    """Raised when GitHub API rate limit is exceeded and cannot be recovered."""
    pass


class GitHubClient:
    """
    Client for authenticated GitHub REST API interactions.
    
    Features:
    - Bearer token or Basic authentication
    - Automatic rate limit detection and waiting
    - Exponential backoff retry logic
    - Automatic pagination handling
    - Request timeout management
    """
    
    BASE_URL = "https://api.github.com"
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 5
    BACKOFF_FACTOR = 2.0  # seconds
    
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token. If None, tries to load from
                   GITHUB_TOKEN environment variable.
            base_url: GitHub API base URL (default: https://api.github.com)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for rate limit errors
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Authentication
        if token is None:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                raise ValueError(
                    "GitHub token not provided and GITHUB_TOKEN environment "
                    "variable is not set."
                )
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "llmXive-research-client"
        })
        
        # Rate limit tracking
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_reset: Optional[float] = None
        
        logger.info(f"GitHub client initialized with base URL: {base_url}")
    
    def _handle_rate_limit(self, response: requests.Response) -> None:
        """
        Check response for rate limit headers and update internal state.
        
        Args:
            response: The API response to check
        
        Raises:
            GitHubRateLimitExceeded: If rate limit is exceeded and max retries
                                     exhausted
        """
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
            self.rate_limit_reset = float(response.headers.get("X-RateLimit-Reset", 0))
        
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
            reset_time = self.rate_limit_reset or time.time() + 60
            wait_time = max(0, reset_time - time.time())
            
            logger.warning(
                f"GitHub rate limit exceeded. Waiting {wait_time:.1f} seconds "
                f"until reset at {time.ctime(reset_time)}"
            )
            
            if wait_time > 0:
                time.sleep(wait_time)
                # Reset session to ensure fresh connection
                self.session.close()
                self.session = requests.Session()
                self.session.headers.update({
                    "Authorization": self.session.headers.get("Authorization", ""),
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "llmXive-research-client"
                })
        
        if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
            raise GitHubRateLimitExceeded(
                "GitHub API rate limit exceeded and retry attempts exhausted."
            )
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Make an authenticated request to the GitHub API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path (e.g., '/search/repositories')
            params: Query parameters
            data: Request body (dict or string)
            headers: Additional headers
        
        Returns:
            The API response object
        
        Raises:
            GitHubRateLimitExceeded: If rate limit is exceeded
            RequestException: If request fails after all retries
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if isinstance(data, dict) else None,
                    data=data if isinstance(data, str) else None,
                    headers=headers,
                    timeout=self.timeout
                )
                
                self._handle_rate_limit(response)
                
                # Handle successful responses
                if response.status_code < 400:
                    return response
                
                # Handle client errors
                if response.status_code == 404:
                    response.raise_for_status()
                
                # Handle rate limit errors with retry
                if response.status_code == 403 and (
                    "rate limit" in response.text.lower() or
                    self.rate_limit_remaining == 0
                ):
                    wait_time = self.BACKOFF_FACTOR ** attempt
                    logger.warning(
                        f"Rate limit detected on attempt {attempt + 1}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                    continue
                
                # Other errors
                response.raise_for_status()
                
            except (Timeout, RequestException) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise
                wait_time = self.BACKOFF_FACTOR ** attempt
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
        
        raise GitHubRateLimitExceeded("Max retries exceeded")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a GET request to the GitHub API."""
        return self._request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a POST request to the GitHub API."""
        return self._request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a PUT request to the GitHub API."""
        return self._request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request to the GitHub API."""
        return self._request("DELETE", endpoint, **kwargs)
    
    def get_json(self, endpoint: str, **kwargs) -> Any:
        """
        Make a GET request and return the JSON response.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments passed to _request
        
        Returns:
            Parsed JSON response
        """
        response = self.get(endpoint, **kwargs)
        return response.json()
    
    def paginate(
        self,
        endpoint: str,
        per_page: int = 100,
        **kwargs
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Iterate through paginated results from the GitHub API.
        
        Args:
            endpoint: API endpoint path (e.g., '/repos/owner/repo/pulls')
            per_page: Number of items per page (max 100)
            **kwargs: Additional arguments passed to _request
        
        Yields:
            Lists of items for each page
        
        Example:
            for page in client.paginate('/search/repositories', q='language:python'):
                for repo in page:
                    process_repo(repo)
        """
        page = 1
        while True:
            params = kwargs.get("params", {})
            params["per_page"] = min(per_page, 100)
            params["page"] = page
            kwargs["params"] = params
            
            response = self.get(endpoint, **kwargs)
            data = response.json()
            
            if not data:
                break
            
            yield data
            
            # Check if there are more pages
            link_header = response.headers.get("Link", "")
            if "rel=\"next\"" not in link_header:
                break
            
            page += 1
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get the current rate limit status from GitHub.
        
        Returns:
            Dictionary containing rate limit information
        """
        response = self.get("/rate_limit")
        return response.json()
    
    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for repositories on GitHub.
        
        Args:
            query: Search query string
            sort: Sort field (stars, forks, updated)
            order: Sort order (asc, desc)
            per_page: Items per page
        
        Yields:
            Repository dictionaries
        """
        for page in self.paginate(
            "/search/repositories",
            q=query,
            sort=sort,
            order=order,
            per_page=per_page
        ):
            for repo in page["items"]:
                yield repo
    
    def get_repository(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Get details for a specific repository.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
        
        Returns:
            Repository details dictionary
        """
        endpoint = f"/repos/{owner}/{repo}"
        return self.get_json(endpoint)
    
    def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "closed",
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get pull requests for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            per_page: Items per page
        
        Yields:
            Pull request dictionaries
        """
        endpoint = f"/repos/{owner}/{repo}/pulls"
        for page in self.paginate(
            endpoint,
            state=state,
            per_page=per_page
        ):
            for pr in page:
                yield pr
    
    def get_pull_request_comments(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get review comments for a specific pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            per_page: Items per page
        
        Yields:
            Comment dictionaries
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}/comments"
        for page in self.paginate(endpoint, per_page=per_page):
            for comment in page:
                yield comment
    
    def get_commit_comments(
        self,
        owner: str,
        repo: str,
        sha: str,
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get comments for a specific commit.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA
            per_page: Items per page
        
        Yields:
            Comment dictionaries
        """
        endpoint = f"/repos/{owner}/{repo}/commits/{sha}/comments"
        for page in self.paginate(endpoint, per_page=per_page):
            for comment in page:
                yield comment
    
    def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get issues for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            per_page: Items per page
        
        Yields:
            Issue dictionaries
        """
        endpoint = f"/repos/{owner}/{repo}/issues"
        for page in self.paginate(
            endpoint,
            state=state,
            per_page=per_page
        ):
            for issue in page:
                yield issue
    
    def get_branches(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get branches for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Items per page
        
        Yields:
            Branch dictionaries
        """
        endpoint = f"/repos/{owner}/{repo}/branches"
        for page in self.paginate(endpoint, per_page=per_page):
            for branch in page:
                yield branch
    
    def get_contents(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get file contents from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            ref: Branch/tag/commit (optional)
        
        Returns:
            File content dictionary (includes base64 encoded content)
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if ref:
            params["ref"] = ref
        
        return self.get_json(endpoint, params=params)
    
    def compare_commits(
        self,
        owner: str,
        repo: str,
        base: str,
        head: str
    ) -> Dict[str, Any]:
        """
        Compare two commits/branches.
        
        Args:
            owner: Repository owner
            repo: Repository name
            base: Base commit/branch
            head: Head commit/branch
        
        Returns:
            Comparison result dictionary
        """
        endpoint = f"/repos/{owner}/{repo}/compare/{base}...{head}"
        return self.get_json(endpoint)
    
    def get_languages(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, int]:
        """
        Get programming languages used in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            Dictionary mapping language names to bytes used
        """
        endpoint = f"/repos/{owner}/{repo}/languages"
        return self.get_json(endpoint)
    
    def get_stargazers(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get stargazers for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Items per page
        
        Yields:
            User dictionaries
        """
        endpoint = f"/repos/{owner}/{repo}/stargazers"
        for page in self.paginate(endpoint, per_page=per_page):
            for user in page:
                yield user
    
    def get_contributors(
        self,
        owner: str,
        repo: str,
        per_page: int = 100
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get contributors for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Items per page
        
        Yields:
            Contributor dictionaries
        """
        endpoint = f"/repos/{owner}/{repo}/contributors"
        for page in self.paginate(endpoint, per_page=per_page):
            for contributor in page:
                yield contributor


def create_client(token: Optional[str] = None) -> GitHubClient:
    """
    Factory function to create a GitHub client.
    
    Args:
        token: Optional GitHub token (defaults to GITHUB_TOKEN env var)
    
    Returns:
        Configured GitHubClient instance
    """
    return GitHubClient(token=token)


def main():
    """
    Main function for testing the GitHub client.
    
    This function demonstrates basic usage of the GitHub client by:
    1. Creating a client instance
    2. Checking rate limit status
    3. Searching for repositories
    4. Getting repository details
    """
    import json
    
    try:
        # Create client (will use GITHUB_TOKEN from environment)
        client = create_client()
        
        # Check rate limit
        rate_limit = client.get_rate_limit_status()
        print("Rate Limit Status:")
        print(json.dumps(rate_limit, indent=2))
        
        # Search for repositories
        print("\nSearching for Python repositories...")
        count = 0
        for repo in client.search_repositories(
            query="language:python stars:>1000",
            per_page=5
        ):
            print(f"  - {repo['full_name']} ({repo['stargazers_count']} stars)")
            count += 1
            if count >= 5:
                break
        
        # Get a specific repository
        print("\nGetting repository details...")
        repo = client.get_repository("llmXive", "research-implementer")
        print(f"  Repository: {repo['full_name']}")
        print(f"  Description: {repo['description']}")
        print(f"  Language: {repo['language']}")
        print(f"  Stars: {repo['stargazers_count']}")
        
        print("\nGitHub client test completed successfully!")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set the GITHUB_TOKEN environment variable.")
    except GitHubRateLimitExceeded as e:
        print(f"Rate limit error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
