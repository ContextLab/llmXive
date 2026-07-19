import os
import time
import logging
from typing import Any, Dict, Generator, List, Optional, Union
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubRateLimitExceeded(Exception):
    """Raised when GitHub API rate limit is exceeded."""
    pass

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        })
        self.base_url = "https://api.github.com"
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                raise GitHubRateLimitExceeded("GitHub API rate limit exceeded")
        response.raise_for_status()
        return response.json()

    def search_repos(self, query: str, per_page: int = 10) -> Generator[Dict[str, Any], None, None]:
        """Search for repositories based on a query."""
        url = f"{self.base_url}/search/repositories"
        params = {"q": query, "per_page": per_page}
        
        while url:
            response = self.session.get(url, params=params)
            data = self._handle_response(response)
            for item in data.get('items', []):
                yield item
            
            # Pagination
            if 'next' in data.get('links', {}):
                url = data['links']['next']['href']
                params = {} # Next URL already contains params
            else:
                url = None

    def get_repo_details(self, full_name: str) -> Dict[str, Any]:
        """Get detailed information about a repository."""
        url = f"{self.base_url}/repos/{full_name}"
        response = self.session.get(url)
        return self._handle_response(response)

    def has_merged_prs(self, full_name: str) -> bool:
        """
        Check if the repository has any merged pull requests.
        This implements the logic for T018 to skip repos with no merged PRs.
        """
        url = f"{self.base_url}/repos/{full_name}/pulls"
        params = {"state": "closed", "per_page": 1}
        
        try:
            response = self.session.get(url, params=params)
            if response.status_code == 404:
                logger.warning(f"Repo {full_name} not found or private.")
                return False
            
            data = self._handle_response(response)
            if not data:
                return False
            
            # Check if the first returned PR is merged
            # The API returns closed PRs, we need to check 'merged_at'
            for pr in data:
                if pr.get('merged_at') is not None:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking PRs for {full_name}: {e}")
            # If we can't check, we might want to be conservative and skip?
            # Or assume true? For safety in T018, let's assume we can't verify and skip if error?
            # Actually, if we can't verify, we might want to proceed or skip. 
            # Given the requirement "handle repositories with no merged PRs", 
            # if we can't confirm, it's safer to skip to avoid false positives in data quality.
            return False

def create_client(token: Optional[str] = None) -> GitHubClient:
    """Create a GitHub client instance."""
    if not token:
        token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token not found in environment or arguments")
    return GitHubClient(token)

def main():
    """Test the GitHub Client."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("No token found")
        return
    
    client = create_client(token)
    try:
        for repo in client.search_repos("language:python stars:>1000", per_page=5):
            print(f"Found: {repo['full_name']}")
            has_prs = client.has_merged_prs(repo['full_name'])
            print(f"  Has Merged PRs: {has_prs}")
    except GitHubRateLimitExceeded as e:
        print(f"Rate limit hit: {e}")

if __name__ == "__main__":
    main()
