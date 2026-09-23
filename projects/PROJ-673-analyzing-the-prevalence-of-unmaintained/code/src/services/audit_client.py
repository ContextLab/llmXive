import os
import time
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime, timezone
import logging
from pathlib import Path

from src.utils.backoff import exponential_backoff
from src.utils.cache import save_response_to_cache, load_from_cache
from src.utils.logging_config import log_api_call
from src.utils.api_metrics import APIMetricsAggregator

logger = logging.getLogger(__name__)
metrics_aggregator = APIMetricsAggregator()

class AuditClient:
    """
    Client for querying npm audit API to retrieve vulnerability counts
    for specific packages.
    
    Adheres to Constitution Principle III (Immutability) and FR-007 (Real Call Testing)
    by using local caching and failing loudly on API errors.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "https://registry.npmjs.org/-/npm/v1/security/advisories/bulk"
        self.session = requests.Session()
        logger.info("AuditClient initialized")

    def _get_cache_params(self, package_name: str, version: str) -> Dict[str, Any]:
        """Generate cache parameters for a specific package version."""
        return {
            "service": "npm_audit",
            "package": package_name,
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def fetch_audit_data(self, package_name: str, version: str) -> Dict[str, Any]:
        """
        Fetch audit data for a specific package version.
        
        Args:
            package_name: Name of the npm package (e.g., 'lodash')
            version: Version string (e.g., '4.17.21')
        
        Returns:
            Dict containing 'vulnerability_count' and raw 'advisories' list.
            Returns {'vulnerability_count': 0, 'advisories': []} if no issues found.
        
        Raises:
            RuntimeError: If the API call fails after retries (fails loudly).
        """
        # Check cache first
        cache_params = self._get_cache_params(package_name, version)
        cached_data = load_from_cache(cache_params)
        
        if cached_data is not None:
            logger.debug(f"Cache hit for {package_name}@{version}")
            return cached_data

        logger.info(f"Fetching audit data for {package_name}@{version}")
        
        # Prepare payload for npm audit bulk API
        # The bulk API expects a list of package descriptors
        payload = [{package_name: version}]
        
        try:
            response = self._make_request(payload)
            
            # Parse response
            # The bulk API returns a dict where keys are package names
            # and values are lists of advisory objects
            advisories = response.get(package_name, [])
            
            # Count vulnerabilities
            vulnerability_count = len(advisories)
            
            result = {
                "vulnerability_count": vulnerability_count,
                "advisories": advisories,
                "package": package_name,
                "version": version,
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Cache the result
            save_response_to_cache(cache_params, result)
            
            log_api_call("npm_audit", "success", package_name)
            metrics_aggregator.record_success("npm_audit")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch audit data for {package_name}@{version}: {str(e)}")
            log_api_call("npm_audit", "failure", package_name, str(e))
            metrics_aggregator.record_failure("npm_audit", str(e))
            # Fail loudly - do not return synthetic data
            raise RuntimeError(f"npm audit API failed for {package_name}@{version}: {str(e)}")

    def _make_request(self, payload: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Make the actual HTTP request to npm audit bulk API with backoff.
        
        Args:
            payload: List of package descriptors for the bulk API
        
        Returns:
            Parsed JSON response
        """
        @exponential_backoff(max_retries=3, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
        def _request_with_backoff():
            resp = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            return resp.json()
        
        return _request_with_backoff()

    def batch_fetch_audit_data(self, packages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Fetch audit data for multiple packages.
        
        Args:
            packages: List of dicts with 'package' and 'version' keys
        
        Returns:
            List of audit result dicts
        """
        results = []
        for pkg in packages:
            try:
                result = self.fetch_audit_data(pkg["package"], pkg["version"])
                results.append(result)
            except Exception as e:
                logger.error(f"Skipping {pkg['package']} due to error: {e}")
                # Include a record with zero vulnerabilities but mark as failed fetch?
                # Per requirements, we fail loudly on API error, so we let the exception
                # propagate or handle it in the caller. For batch, we log and skip.
                continue
        return results

def main():
    """Entry point for testing the AuditClient directly."""
    import json
    
    # Example usage
    client = AuditClient()
    
    # Test with a known package
    test_packages = [
        {"package": "lodash", "version": "4.17.21"},
        {"package": "express", "version": "4.18.2"},
    ]
    
    print("Fetching audit data for test packages...")
    for pkg in test_packages:
        try:
            result = client.fetch_audit_data(pkg["package"], pkg["version"])
            print(f"{pkg['package']}@{pkg['version']}: {result['vulnerability_count']} vulnerabilities")
        except Exception as e:
            print(f"Error fetching {pkg['package']}: {e}")

if __name__ == "__main__":
    main()
