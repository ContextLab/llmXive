import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import os
import logging

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        self.token = token or os.getenv('GITHUB_TOKEN', '')
        self.base_url = base_url or 'https://api.github.com'
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({'Authorization': f'token {self.token}'})
        self.session.headers.update({'Accept': 'application/vnd.github.v3+json'})
        
        # Initialize logging attributes for compatibility
        self.info = self._log_info
        self.debug = self._log_debug
        self.warning = self._log_warning
        self.error = self._log_error

    def _log_info(self, msg, *args, **kwargs):
        logger.info(msg, *args, **kwargs)
    
    def _log_debug(self, msg, *args, **kwargs):
        logger.debug(msg, *args, **kwargs)
    
    def _log_warning(self, msg, *args, **kwargs):
        logger.warning(msg, *args, **kwargs)
    
    def _log_error(self, msg, *args, **kwargs):
        logger.error(msg, *args, **kwargs)

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        url = urljoin(self.base_url, endpoint)
        retries = 3
        for attempt in range(retries):
            try:
                response = self.session.request(method, url, **kwargs)
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit hit. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    logger.error(f"Request failed after {retries} attempts: {e}")
                    return None
                time.sleep(2 ** attempt)
        return None

    def get_repo(self, owner: str, repo: str) -> Optional[Dict]:
        return self._request('GET', f'/repos/{owner}/{repo}')

    def get_pulls(self, owner: str, repo: str, state: str = 'all') -> List[Dict]:
        return self._request('GET', f'/repos/{owner}/{repo}/pulls', params={'state': state}) or []

    def get_commits(self, owner: str, repo: str, sha: Optional[str] = None) -> List[Dict]:
        return self._request('GET', f'/repos/{owner}/{repo}/commits', params={'sha': sha}) or []

    def get_contents(self, owner: str, repo: str, path: str) -> Optional[Dict]:
        return self._request('GET', f'/repos/{owner}/{repo}/contents/{path}')

    def __getattr__(self, name):
        # Tolerate any other logger-style calls
        def _noop(*args, **kwargs):
            return None
        return _noop
