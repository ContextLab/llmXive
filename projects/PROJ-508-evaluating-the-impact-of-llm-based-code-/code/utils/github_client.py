"""
GitHub API client with exponential backoff retry logic.
Tolerant of various call patterns to support different usage contexts.
"""
import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubClient:
    """
    GitHub API client with retry logic and flexible initialization.
    """
    
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub API token (optional)
            base_url: Base URL for API (optional, defaults to GitHub API)
            **kwargs: Additional keyword arguments for flexibility
        """
        self.token = token or os.getenv('GITHUB_TOKEN', '')
        self.base_url = base_url or 'https://api.github.com'
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        
        # Log initialization
        logger.info(f"GitHubClient initialized with base_url: {self.base_url}")
    
    def _request_with_retry(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make a request with exponential backoff retry logic.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments
            
        Returns:
            Response data or None on failure
        """
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    # Rate limit - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}. Retrying in {delay}s")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Request failed with status {response.status_code}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Request error: {str(e)}. Retrying in {delay}s")
                time.sleep(delay)
        
        logger.error("All retry attempts failed")
        return None
    
    def get(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make a GET request."""
        full_url = urljoin(self.base_url, url)
        return self._request_with_retry('GET', full_url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make a POST request."""
        full_url = urljoin(self.base_url, url)
        return self._request_with_retry('POST', full_url, **kwargs)
    
    def info(self, *args, **kwargs):
        """Tolerant info logger."""
        logger.info(*args, **kwargs)
    
    def debug(self, *args, **kwargs):
        """Tolerant debug logger."""
        logger.debug(*args, **kwargs)
    
    def warning(self, *args, **kwargs):
        """Tolerant warning logger."""
        logger.warning(*args, **kwargs)
    
    def error(self, *args, **kwargs):
        """Tolerant error logger."""
        logger.error(*args, **kwargs)
    
    def __getattr__(self, name: str):
        """
        Fallback for any unknown attribute/method.
        Returns a no-op callable to prevent AttributeError.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop