import os
import time
import logging
from typing import Any, Dict, Generator, List, Optional, Union
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

class GitHubRateLimitExceeded(Exception):
    """Exception raised when GitHub API rate limit is exceeded."""
    pass

class GitHubClient:
    """
    GitHub REST API client with rate limit handling and pagination.
    """
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token
            base_url: GitHub API base URL
        """
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'llmXive-research-agent'
        })
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
    
    def _check_rate_limit(self):
        """Check and handle rate limits."""
        response = self.session.get(f'{self.base_url}/rate_limit')
        if response.status_code == 200:
            data = response.json()
            self.rate_limit_remaining = data['resources']['core']['remaining']
            self.rate_limit_reset = data['resources']['core']['reset']
            
            if self.rate_limit_remaining < 10:
                logger.warning(f"Rate limit low: {self.rate_limit_remaining} requests remaining")
                if self.rate_limit_remaining == 0:
                    reset_time = time.time() + (self.rate_limit_reset - time.time())
                    raise GitHubRateLimitExceeded(
                        f"Rate limit exceeded. Reset in {reset_time:.0f} seconds"
                    )
        else:
            logger.warning(f"Could not check rate limit: {response.status_code}")
    
    def _wait_for_rate_limit(self):
        """Wait if rate limit is exceeded."""
        if self.rate_limit_remaining < 10:
            wait_time = max(0, self.rate_limit_reset - time.time())
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.0f} seconds for rate limit reset")
                time.sleep(wait_time + 1)
            self._check_rate_limit()
    
    def _paginate(self, url: str, params: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Paginate through GitHub API results.
        
        Args:
            url: API endpoint URL
            params: Query parameters
        
        Yields:
            Individual items from the paginated results
        """
        self._wait_for_rate_limit()
        
        page = 1
        per_page = 100
        
        while True:
            params = params or {}
            params['page'] = page
            params['per_page'] = per_page
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                
                for item in data:
                    yield item
                
                # Check if there are more pages
                if len(data) < per_page:
                    break
                page += 1
            elif response.status_code == 403:
                raise GitHubRateLimitExceeded("Rate limit exceeded")
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                break
    
    def get_repos(self, owner: str, per_page: int = 100) -> Generator[Dict[str, Any], None, None]:
        """
        Get all repositories for a user/organization.
        
        Args:
            owner: GitHub username or organization name
            per_page: Number of repos per page
        
        Yields:
            Repository dictionaries
        """
        url = f'{self.base_url}/users/{owner}/repos'
        yield from self._paginate(url)
    
    def get_pulls(self, owner: str, repo: str, state: str = 'all') -> Generator[Dict[str, Any], None, None]:
        """
        Get pull requests for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
        
        Yields:
            Pull request dictionaries
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/pulls'
        params = {'state': state}
        yield from self._paginate(url, params)
    
    def get_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get review comments for a specific pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
        
        Returns:
            List of review comment dictionaries
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments'
        comments = []
        for comment in self._paginate(url):
            comments.append(comment)
        return comments
    
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed information about a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            Repository dictionary
        """
        url = f'{self.base_url}/repos/{owner}/{repo}'
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get repo: {response.status_code}")
            return {}

def create_client(token: Optional[str] = None, base_url: Optional[str] = None) -> GitHubClient:
    """
    Create a GitHub client instance.
    
    Args:
        token: GitHub token (defaults to GITHUB_TOKEN env var)
        base_url: GitHub API base URL (defaults to env var or GitHub default)
    
    Returns:
        GitHubClient instance
    """
    if token is None:
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    if base_url is None:
        base_url = os.getenv('GITHUB_API_BASE_URL', 'https://api.github.com')
    
    return GitHubClient(token, base_url)

def main():
    """Main entry point for testing the GitHub client."""
    client = create_client()
    
    # Test: Get rate limit info
    try:
        client._check_rate_limit()
        logger.info(f"Rate limit: {client.rate_limit_remaining} requests remaining")
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
    
    # Test: Fetch some repos (example)
    try:
        repos = list(client.get_repos('facebook', per_page=5))
        logger.info(f"Found {len(repos)} repos for facebook")
    except Exception as e:
        logger.error(f"Failed to fetch repos: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
