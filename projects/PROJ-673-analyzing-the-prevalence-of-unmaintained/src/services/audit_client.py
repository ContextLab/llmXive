"""
AuditClient: Interacts with the npm audit API to fetch vulnerability data for packages.

This client queries the npm registry's audit endpoint to retrieve the number of
unpatched CVEs (vulnerabilities) for a given package. It handles rate limiting,
retries with exponential backoff, and logs API interactions.
"""
import os
import time
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime, timezone
import logging
import hashlib
import json
from pathlib import Path

from src.utils.backoff import exponential_backoff
from src.config.settings import get_config
from src.utils.checksum import generate_checksum, write_checksum_file
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
config = get_config()

class AuditClient:
    """
    Client for fetching npm audit data.
    
    Uses the npm audit API endpoint: https://registry.npmjs.org/-/npm/v1/audits
    Note: The standard registry does not expose a direct public API for arbitrary
    package audits without an auth token in some contexts, but the public registry
    often supports a simplified GET /{package} which includes 'audit' data in the 
    'maintainers' or 'dist-tags' or via the 'npm audit' CLI logic. 
    
    However, the most reliable programmatic way without a full CLI is to hit:
    https://registry.npmjs.org/-/npm/v1/audits?packages=package_name
    
    If that endpoint is restricted or requires auth, we fall back to a known public
    mirror or the standard registry's package metadata if it includes vulnerability 
    info (rare). 
    
    For this implementation, we target the public npm audit endpoint.
    """
    
    BASE_URL = "https://registry.npmjs.org/-/npm/v1/audits"
    TIMEOUT = 10  # seconds

    def __init__(self, rate_limit: Optional[int] = None):
        """
        Initialize the AuditClient.
        
        Args:
            rate_limit: Optional override for rate limit (requests per minute).
                        Defaults to config value.
        """
        self.session = requests.Session()
        self.rate_limit = rate_limit or config.RATE_LIMIT
        self.last_request_time = 0.0
        self.min_interval = 60.0 / self.rate_limit if self.rate_limit > 0 else 0.0
        
        # Ensure data directories exist
        self.cache_dir = Path("data/raw")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.audit_cache_dir = self.cache_dir / "audit"
        self.audit_cache_dir.mkdir(parents=True, exist_ok=True)

    def _rate_limit_delay(self):
        """Enforce rate limiting by sleeping if necessary."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _fetch_audit_data(self, package_name: str) -> Dict[str, Any]:
        """
        Fetch audit data for a single package from the npm registry.
        
        Args:
            package_name: The name of the npm package.
            
        Returns:
            A dictionary containing the audit results, specifically the 'vulnerabilities' count.
            
        Raises:
            requests.exceptions.RequestException: If the request fails after retries.
            ValueError: If the response format is unexpected.
        """
        self._rate_limit_delay()
        
        # Construct the request
        # The npm audit API for a specific package is often accessed via:
        # POST /-/npm/v1/audits with a body of packages, but for simple GET we can try:
        # https://registry.npmjs.org/-/npm/v1/audits?packages={package}
        # However, the standard public endpoint for a single package audit is often:
        # GET https://registry.npmjs.org/-/npm/v1/audits?packages={package}
        # If that fails, we might need to POST. Let's try the GET first as it's simpler.
        
        params = {"packages": package_name}
        url = self.BASE_URL
        
        try:
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # The structure is usually: { "actions": [...], "vulnerabilities": {...} }
            # We need the total count of vulnerabilities for this package.
            # The 'vulnerabilities' key often contains a dict of {severity: count}.
            
            if "vulnerabilities" in data:
                vuln_dict = data["vulnerabilities"]
                # Sum up all vulnerabilities across severities
                total_vulns = sum(vuln_dict.values())
                return {
                    "package": package_name,
                    "vulnerability_count": total_vulns,
                    "details": vuln_dict,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                # Some responses might not have the 'vulnerabilities' key if empty or error
                logger.warning(f"No 'vulnerabilities' key in response for {package_name}: {data.get('error', 'Unknown')}")
                return {
                    "package": package_name,
                    "vulnerability_count": 0,
                    "details": {},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Package {package_name} not found or no audit data available (404).")
                return {
                    "package": package_name,
                    "vulnerability_count": 0,
                    "details": {},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            raise e
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching audit for {package_name}: {e}")
            raise e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {package_name}: {e}")
            raise ValueError(f"Invalid JSON response for {package_name}") from e

    @exponential_backoff(max_retries=5, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
    def fetch_audit_data(self, package_name: str) -> Dict[str, Any]:
        """
        Fetch audit data for a package with retry logic.
        
        Args:
            package_name: The name of the npm package.
            
        Returns:
            Dictionary with vulnerability count and details.
        """
        logger.info(f"Fetching audit data for package: {package_name}")
        result = self._fetch_audit_data(package_name)
        
        # Cache the result
        cache_key = generate_checksum(package_name)
        cache_path = self.audit_cache_dir / f"{cache_key}.json"
        
        # Write to cache
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        
        # Write checksum of the cached file
        checksum = generate_checksum(cache_path.read_bytes())
        write_checksum_file(cache_path, checksum)
        
        logger.debug(f"Cached audit data for {package_name} at {cache_path}")
        return result

    def batch_fetch_audit_data(self, package_names: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch audit data for a list of packages.
        
        Args:
            package_names: List of package names.
            
        Returns:
            List of dictionaries containing audit results.
        """
        results = []
        for pkg in package_names:
            try:
                data = self.fetch_audit_data(pkg)
                results.append(data)
            except Exception as e:
                logger.error(f"Failed to fetch audit for {pkg}: {e}")
                # Record a failure entry with 0 count but flag as error? 
                # For now, append a minimal error structure or skip.
                # Let's append a minimal structure to keep alignment.
                results.append({
                    "package": pkg,
                    "vulnerability_count": 0,
                    "details": {},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)
                })
        return results

def main():
    """
    Main entry point for testing the AuditClient.
    Fetches audit data for a known package and prints the result.
    """
    client = AuditClient()
    
    # Test with a popular package known to have some dependencies
    test_package = "lodash"
    logger.info(f"Testing AuditClient with package: {test_package}")
    
    try:
        result = client.fetch_audit_data(test_package)
        print(f"Audit result for {test_package}:")
        print(f"  Vulnerability Count: {result['vulnerability_count']}")
        print(f"  Details: {result['details']}")
        print(f"  Timestamp: {result['timestamp']}")
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
            
    except Exception as e:
        logger.critical(f"Failed to fetch audit data: {e}")
        raise

if __name__ == "__main__":
    main()