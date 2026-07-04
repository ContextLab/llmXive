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

class AuditClient:
    """Client for interacting with the NPM Audit API."""

    def __init__(self):
        self.base_url = "https://registry.npmjs.org/-/npm/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "llmXive-Audit-Research-Client/1.0"
        })

    def _handle_request_error(self, error: Exception, package_name: str, operation: str) -> None:
        """Log detailed error information for debugging."""
        if isinstance(error, requests.HTTPError):
            status_code = error.response.status_code if error.response else "Unknown"
            logger.error(f"HTTP {status_code} during '{operation}' for package '{package_name}'")
            if error.response and error.response.status_code == 404:
                logger.warning(f"Audit data not found for package '{package_name}'.")
            elif error.response and error.response.status_code == 429:
                logger.warning(f"Rate limit exceeded for package '{package_name}'. Retrying...")
        elif isinstance(error, requests.ConnectionError):
            logger.error(f"Connection error during '{operation}' for package '{package_name}'")
        elif isinstance(error, requests.Timeout):
            logger.error(f"Timeout error during '{operation}' for package '{package_name}'")
        else:
            logger.error(f"Unexpected error '{type(error).__name__}' for package '{package_name}' during '{operation}': {str(error)}")

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def fetch_audit_data(self, package_name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch audit data for a specific package.
        
        Args:
            package_name: Name of the package.
            version: Specific version (optional).
            
        Returns:
            Dictionary containing audit findings or None if not found/error.
        """
        url = f"{self.base_url}/security/advisories"
        params = {"package": package_name}
        if version:
            params["version"] = version
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # The API returns a list of advisories
            advisories = data.get("advisories", [])
            return {
                "package": package_name,
                "version": version,
                "advisories": advisories,
                "vulnerability_count": len(advisories)
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Audit data not found for '{package_name}'.")
                return None
            self._handle_request_error(e, package_name, "fetch_audit_data")
            return None
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, package_name, "fetch_audit_data")
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Unexpected data structure for audit of '{package_name}': {str(e)}")
            return None

    def batch_fetch_audit_data(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetch audit data for a list of packages.
        
        Args:
            packages: List of package dictionaries with 'name' and optionally 'version'.
            
        Returns:
            List of audit data dictionaries.
        """
        results = []
        for pkg in packages:
            name = pkg.get("name")
            version = pkg.get("version")
            
            if not name:
                logger.warning("Package name missing in batch fetch, skipping.")
                continue
            
            audit_data = self.fetch_audit_data(name, version)
            if audit_data:
                results.append(audit_data)
            else:
                # Include entry with zero vulnerabilities if fetch fails but package exists
                results.append({
                    "package": name,
                    "version": version,
                    "advisories": [],
                    "vulnerability_count": 0
                })
        return results
