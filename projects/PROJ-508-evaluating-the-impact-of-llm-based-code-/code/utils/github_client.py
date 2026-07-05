"""
GitHub Client with Exponential Backoff Retry Logic.
"""
import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import os

class GitHubClient:
    """
    A client for interacting with the GitHub API with built-in retry logic.
    """
    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = base_url
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
        else:
            # Warning for unauthenticated requests
            print("Warning: No GitHub token provided. Rate limits will be low.")

    def _request_with_retry(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Performs a request with exponential backoff retry logic.
        """
        url = urljoin(self.base_url, endpoint)
        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Not found, no point retrying
                    return None
                elif response.status_code == 403:
                    # Rate limited
                    if 'X-RateLimit-Remaining' in response.headers:
                        remaining = int(response.headers['X-RateLimit-Remaining'])
                        if remaining == 0:
                            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                            wait_time = max(0, reset_time - int(time.time()) + 1)
                            print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                    # If still 403, raise or return None
                    return None
                else:
                    # Other errors
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"Request failed with status {response.status_code}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Network error: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"Network error after retries: {e}")
                    return None
        
        return None

    def get_repo(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """Fetches repository metadata."""
        return self._request_with_retry("GET", f"/repos/{repo_name}")

    def get_pulls(self, repo_name: str, state: str = 'closed', per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetches pull requests for a repository."""
        url = f"/repos/{repo_name}/pulls"
        params = {"state": state, "per_page": per_page}
        
        all_pulls = []
        page = 1
        while True:
            params["page"] = page
            response = self._request_with_retry("GET", url, params=params)
            if not response:
                break
            if not response:
                break
            all_pulls.extend(response)
            if len(response) < per_page:
                break
            page += 1
            # Simple rate limit safety
            time.sleep(0.5)
        return all_pulls

    def get_commits(self, repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetches commits for a specific PR."""
        # GitHub API: /repos/{owner}/{repo}/pulls/{pull_number}/commits
        return self._request_with_retry("GET", f"/repos/{repo_name}/pulls/{pr_number}/commits") or []

    def get_review_comments(self, repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetches review comments for a specific PR."""
        return self._request_with_retry("GET", f"/repos/{repo_name}/pulls/{pr_number}/comments") or []

    def get_file_content(self, repo_name: str, path: str, ref: str = "main") -> Optional[str]:
        """Fetches the content of a file."""
        # GitHub API: /repos/{owner}/{repo}/contents/{path}
        response = self._request_with_retry("GET", f"/repos/{repo_name}/contents/{path}", params={"ref": ref})
        if response and 'content' in response:
            import base64
            return base64.b64decode(response['content']).decode('utf-8')
        return None
