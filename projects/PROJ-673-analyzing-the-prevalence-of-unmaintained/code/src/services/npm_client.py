import os
import time
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime, timezone
from src.utils.backoff import exponential_backoff
from src.config.settings import get_config
import logging

logger = logging.getLogger(__name__)
config = get_config()

class NpmClient:
    """Client for interacting with the NPM registry API."""

    def __init__(self):
        self.base_url = "https://registry.npmjs.org"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "llmXive-NPM-Research-Client/1.0"
        })

    def _handle_request_error(self, error: Exception, package_name: str) -> None:
        """Log detailed error information for debugging."""
        if isinstance(error, requests.HTTPError):
            status_code = error.response.status_code if error.response else "Unknown"
            logger.error(f"HTTP {status_code} while fetching data for package '{package_name}'")
            if error.response and error.response.status_code == 404:
                logger.warning(f"Package '{package_name}' not found in NPM registry.")
            elif error.response and error.response.status_code == 429:
                logger.warning(f"Rate limit exceeded for package '{package_name}'. Retrying...")
        elif isinstance(error, requests.ConnectionError):
            logger.error(f"Connection error while fetching data for package '{package_name}'")
        elif isinstance(error, requests.Timeout):
            logger.error(f"Timeout error while fetching data for package '{package_name}'")
        else:
            logger.error(f"Unexpected error '{type(error).__name__}' for package '{package_name}': {str(error)}")

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def get_package_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific NPM package.
        
        Args:
            package_name: The name of the NPM package.
            
        Returns:
            Dictionary containing package metadata or None if not found/error.
        """
        url = f"{self.base_url}/{package_name}"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Package '{package_name}' not found (404). Skipping.")
                return None
            self._handle_request_error(e, package_name)
            return None
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, package_name)
            return None

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def get_top_packages(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch a list of top packages by weekly downloads.
        
        Args:
            count: Number of packages to retrieve.
            
        Returns:
            List of dictionaries containing package information.
        """
        url = "https://www.npmjs.com/api/v1/search"
        params = {
            "text": "downloads:>0",
            "size": count,
            "from": 0
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            packages = []
            for obj in data.get("objects", []):
                pkg = obj.get("package", {})
                if pkg:
                    packages.append({
                        "name": pkg.get("name"),
                        "version": pkg.get("version"),
                        "description": pkg.get("description"),
                        "links": pkg.get("links", {}),
                        "keywords": pkg.get("keywords", [])
                    })
            return packages
        except requests.exceptions.HTTPError as e:
            self._handle_request_error(e, "top_packages_query")
            return []
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, "top_packages_query")
            return []

    def fetch_dependencies(self, package_name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch dependency tree for a specific package version.
        
        Args:
            package_name: Name of the package.
            version: Specific version (optional, defaults to latest).
            
        Returns:
            Dictionary containing dependency tree or None on error.
        """
        if version:
            url = f"{self.base_url}/{package_name}/{version}"
        else:
            url = f"{self.base_url}/{package_name}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract dependencies from the 'versions' section
            versions = data.get("versions", {})
            if version:
                target_version = version
            else:
                target_version = data.get("dist-tags", {}).get("latest")
            
            if target_version and target_version in versions:
                return versions[target_version].get("dependencies", {})
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Version or package '{package_name}' not found.")
                return None
            self._handle_request_error(e, package_name)
            return None
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, package_name)
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Unexpected data structure for package '{package_name}': {str(e)}")
            return None
