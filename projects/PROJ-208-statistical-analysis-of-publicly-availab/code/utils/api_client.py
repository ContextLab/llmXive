"""
GitHub API Client with rate limit handling and exponential backoff.
Implements explicit wait >= 60 seconds upon rate limit hits (FR-001).
"""
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from utils.config import get_config

logger = logging.getLogger(__name__)

class GitHubAPIClient:
    """
    A client for interacting with the GitHub API.
    Handles rate limiting, authentication, and retries.
    """

    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.token = token or get_config().get("github_token")
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})
        self.session.headers.update({"Accept": "application/vnd.github.v3+json"})

    def _handle_rate_limit(self, response: requests.Response) -> bool:
        """
        Handles 403 Forbidden responses (rate limit).
        Waits >= 60 seconds as per requirement.
        Returns True if handled and caller should retry, False otherwise.
        """
        if response.status_code != 403:
            return False

        logger.warning("Rate limit hit. Checking reset time...")
        try:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            now = int(time.time())
            wait_seconds = max(60, reset_time - now)
            if wait_seconds <= 0:
                wait_seconds = 60
            logger.info(f"Waiting {wait_seconds} seconds for rate limit reset.")
            time.sleep(wait_seconds)
            return True
        except Exception as e:
            logger.error(f"Error parsing rate limit headers: {e}")
            # Fallback to fixed wait
            logger.info("Waiting 60 seconds as fallback.")
            time.sleep(60)
            return True

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        Performs a GET request with rate limit handling.
        """
        full_url = f"{self.base_url}{url}"
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                response = self.session.get(full_url, params=params, headers=headers)
                
                if response.status_code == 403:
                    if self._handle_rate_limit(response):
                        attempt += 1
                        continue
                
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed on attempt {attempt+1}: {e}")
                attempt += 1
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        raise RuntimeError(f"Failed after {max_retries} attempts")

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Gets current rate limit status.
        """
        response = self.session.get(f"{self.base_url}/rate_limit")
        response.raise_for_status()
        return response.json()
