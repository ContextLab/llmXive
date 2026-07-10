import os
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)

class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""
    pass

class RepositoryNotFoundError(GitHubClientError):
    """Raised when a repository is not found."""
    pass

class RateLimitExceededError(GitHubClientError):
    """Raised when GitHub API rate limit is exceeded."""
    pass

class GitHubClient:
    """GitHub API client with rate-limit handling and shallow clone support."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
    
    def _check_rate_limit(self):
        """Check and handle rate limits."""
        # Get current rate limit info
        try:
            resp = self.session.get(f"{self.BASE_URL}/rate_limit")
            if resp.status_code == 200:
                data = resp.json()
                core = data.get('resources', {}).get('core', {})
                self.rate_limit_remaining = core.get('remaining', 0)
                self.rate_limit_reset = core.get('reset', 0)
                
                if self.rate_limit_remaining < 10:
                    reset_time = datetime.fromtimestamp(self.rate_limit_reset)
                    wait_time = max(0, int((reset_time - datetime.now()).total_seconds()))
                    if wait_time > 0:
                        logger.warning(f"Rate limit low. Waiting {wait_time}s until {reset_time}")
                        time.sleep(min(wait_time, 60))  # Wait max 60s
            else:
                logger.warning(f"Failed to check rate limit: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error checking rate limit: {e}")
    
    def search_repos(self, query: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Search for repositories."""
        self._check_rate_limit()
        
        url = f"{self.BASE_URL}/search/repositories"
        params = {"q": query, "per_page": per_page}
        
        try:
            resp = self.session.get(url, params=params)
            if resp.status_code == 404:
                raise RepositoryNotFoundError(f"Repository not found for query: {query}")
            elif resp.status_code == 403:
                raise RateLimitExceededError("GitHub API rate limit exceeded")
            elif resp.status_code != 200:
                raise GitHubClientError(f"Search failed: {resp.status_code} - {resp.text}")
            
            data = resp.json()
            return data.get('items', [])
        except requests.exceptions.RequestException as e:
            raise GitHubClientError(f"Network error during search: {e}")
    
    def get_repo(self, full_name: str) -> Dict[str, Any]:
        """Get repository details."""
        self._check_rate_limit()
        
        url = f"{self.BASE_URL}/repos/{full_name}"
        try:
            resp = self.session.get(url)
            if resp.status_code == 404:
                raise RepositoryNotFoundError(f"Repository not found: {full_name}")
            elif resp.status_code == 403:
                raise RateLimitExceededError("GitHub API rate limit exceeded")
            elif resp.status_code != 200:
                raise GitHubClientError(f"Get repo failed: {resp.status_code}")
            
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise GitHubClientError(f"Network error: {e}")
    
    def shallow_clone(self, repo_name: str, target_dir: Path, depth: int = 100) -> Path:
        """Shallow clone a repository to target directory."""
        # Sanitize repo name for filesystem
        safe_name = repo_name.replace("/", "_").replace("\\", "_")
        repo_path = target_dir / safe_name
        
        if repo_path.exists():
            logger.info(f"Repo {repo_name} already exists at {repo_path}, skipping clone.")
            return repo_path
        
        repo_path.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/{repo_name}.git"
        
        try:
            # Attempt shallow clone
            cmd = ["git", "clone", "--depth", str(depth), "--no-tags", url, str(repo_path)]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Successfully cloned {repo_name} (depth={depth}) to {repo_path}")
            return repo_path
        except subprocess.CalledProcessError as e:
            stderr_msg = e.stderr if e.stderr else "Unknown error"
            # Check for 404/Not Found in git output or stderr
            if "not found" in stderr_msg.lower() or "404" in stderr_msg:
                logger.error(f"Repository not found or deleted: {repo_name} ({stderr_msg.strip()})")
                raise RepositoryNotFoundError(f"Repository not found or deleted: {repo_name}")
            
            logger.error(f"Failed to clone {repo_name}: {stderr_msg}")
            raise GitHubClientError(f"Clone failed: {stderr_msg}")
        except FileNotFoundError:
            raise GitHubClientError("Git command not found. Please ensure git is installed and in PATH.")
    
    def get_commits(self, repo_name: str, since: Optional[datetime] = None, until: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get commit history for a repository."""
        self._check_rate_limit()
        
        url = f"{self.BASE_URL}/repos/{repo_name}/commits"
        params = {}
        if since:
            params['since'] = since.isoformat()
        if until:
            params['until'] = until.isoformat()
        
        try:
            resp = self.session.get(url, params=params)
            if resp.status_code == 404:
                raise RepositoryNotFoundError(f"Repository not found: {repo_name}")
            elif resp.status_code == 403:
                raise RateLimitExceededError("GitHub API rate limit exceeded")
            elif resp.status_code != 200:
                raise GitHubClientError(f"Get commits failed: {resp.status_code}")
            
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise GitHubClientError(f"Network error: {e}")