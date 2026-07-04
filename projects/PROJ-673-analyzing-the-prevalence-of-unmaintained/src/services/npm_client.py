"""
NPM Client Service

Implements interaction with the NPM Registry API to:
1. Query top packages by weekly downloads.
2. Fetch detailed package metadata.
"""
import requests
import time
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

from src.utils.backoff import exponential_backoff
from src.utils.logging_config import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


class NpmClient:
    """
    Client for interacting with the NPM Registry API.
    """

    BASE_URL = "https://registry.npmjs.org"
    SEARCH_ENDPOINT = "/-/v1/search"
    PACKAGE_ENDPOINT = "/{package_name}"

    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        # Set a reasonable timeout for API calls
        self.timeout = 30
        self._rate_limit_delay = 0.0  # Will be adjusted based on settings

    def _get_rate_limit_delay(self) -> float:
        """
        Calculate delay to respect rate limits.
        """
        rate_limit = self.settings.get("RATE_LIMIT", 60)
        if rate_limit > 0:
            return 60.0 / rate_limit
        return 0.1  # Default small delay

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def fetch_package_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific NPM package.

        Args:
            package_name: The name of the package (e.g., 'lodash').

        Returns:
            Dictionary containing package metadata, or None if not found/failure.
        """
        url = f"{self.BASE_URL}{self.PACKAGE_ENDPOINT.format(package_name=package_name)}"
        
        try:
            logger.debug(f"Fetching metadata for package: {package_name}")
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                logger.warning(f"Package not found: {package_name}")
                return None
            elif response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch metadata for {package_name}: HTTP {response.status_code}")
                # Raise for backoff to handle
                response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {package_name}: {e}")
            raise e

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def get_top_packages(self, size: int = 100) -> List[Dict[str, Any]]:
        """
        Query the top packages by weekly downloads.

        Args:
            size: Number of packages to retrieve.

        Returns:
            List of dictionaries containing package name and download count.
        """
        # NPM Search API query for top downloads
        # Note: The search API returns a list of objects with 'package' and 'downloads'
        url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"
        
        params = {
            "text": "downloads:>10000", # Filter for popular packages
            "size": size,
            "from": 0
        }

        try:
            logger.info(f"Fetching top {size} packages by weekly downloads...")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("objects", [])
            
            parsed_packages = []
            for obj in results:
                pkg_info = obj.get("package", {})
                downloads_info = obj.get("downloads", {})
                
                if pkg_info and "name" in pkg_info:
                    parsed_packages.append({
                        "name": pkg_info["name"],
                        "weekly_downloads": downloads_info.get("downloads", 0)
                    })
            
            logger.info(f"Successfully retrieved {len(parsed_packages)} packages.")
            return parsed_packages

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching top packages: {e}")
            raise e

    def get_package_details(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Wrapper to fetch full details including dependencies.
        
        Args:
            package_name: The name of the package.
            
        Returns:
            Full metadata dict including 'dependencies' and 'time' fields.
        """
        return self.fetch_package_metadata(package_name)

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
