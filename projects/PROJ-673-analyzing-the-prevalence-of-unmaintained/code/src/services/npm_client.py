"""
NPM Client Service
Implements fetching top packages by weekly downloads and retrieving package metadata.
"""
import os
import time
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime, timezone
from src.utils.backoff import exponential_backoff
from src.utils.cache import save_response_to_cache, load_from_cache
from src.utils.logging_config import log_api_call
from src.config.settings import get_config
import logging

logger = logging.getLogger(__name__)

class NpmClient:
    """Client for interacting with the NPM Registry API."""

    def __init__(self):
        self.config = get_config()
        self.base_url = "https://registry.npmjs.org"
        self.search_url = "https://registry.npmjs.org/-/v1/search"
        self.session = requests.Session()
        # Set a default timeout to prevent hanging
        self.timeout = 30

    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        """Generate a cache key based on request parameters."""
        import hashlib
        import json
        key_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _fetch_top_packages(self, size: int = 250) -> List[Dict[str, Any]]:
        """
        Fetch top packages by weekly downloads using the NPM search API.
        
        Args:
            size: Number of packages to fetch (max 250 per request).
            
        Returns:
            List of package metadata dictionaries.
        """
        params = {
            "text": "downloads:>10000", # Filter for popular packages
            "size": size,
            "from": "0",
            "quality": 0.0,
            "popularity": 0.98,
            "maintenance": 0.0
        }

        @exponential_backoff(max_retries=3, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
        def _make_request():
            cache_key = self._get_cache_key(params)
            
            # Check cache first
            cached_data = load_from_cache(params)
            if cached_data is not None:
                logger.info(f"Cache hit for top packages query: {cache_key}")
                return cached_data

            logger.info(f"Fetching top packages from NPM API with params: {params}")
            response = self.session.get(self.search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            save_response_to_cache(params, data)
            
            log_api_call("npm_search", status="success", params=params)
            return data

        try:
            result = _make_request()
            packages = result.get("objects", [])
            return packages
        except Exception as e:
            log_api_call("npm_search", status="error", error=str(e), params=params)
            logger.error(f"Failed to fetch top packages: {e}")
            raise

    def get_package_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed metadata for a specific package.
        
        Args:
            package_name: The name of the package (e.g., 'lodash').
            
        Returns:
            Package metadata dictionary or None if not found.
        """
        url = f"{self.base_url}/{package_name}"
        params = {"_fields": "name,version,description,license,repository,keywords,readme"}
        
        cache_key = self._get_cache_key({"url": url, "params": params})
        cached_data = load_from_cache({"url": url, "params": params})
        
        if cached_data is not None:
            logger.debug(f"Cache hit for package {package_name}")
            return cached_data

        @exponential_backoff(max_retries=3, initial_delay=1.0, multiplier=2.0, max_delay=60.0)
        def _make_request():
            logger.debug(f"Fetching metadata for {package_name}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            
            save_response_to_cache({"url": url, "params": params}, data)
            log_api_call("npm_metadata", status="success", params={"package": package_name})
            return data

        try:
            result = _make_request()
            return result
        except Exception as e:
            log_api_call("npm_metadata", status="error", error=str(e), params={"package": package_name})
            logger.error(f"Failed to fetch metadata for {package_name}: {e}")
            raise

    def get_top_packages_list(self, top_n: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve a list of the top N packages by weekly downloads.
        
        Args:
            top_n: Number of top packages to retrieve.
            
        Returns:
            List of dictionaries containing package name, version, and download stats.
        """
        if top_n > 250:
            logger.warning(f"Requested {top_n} packages, but API limit is 250. Fetching 250.")
            top_n = 250
        
        packages = self._fetch_top_packages(size=top_n)
        
        # Extract relevant fields
        result = []
        for pkg_obj in packages:
            package_info = pkg_obj.get("package", {})
            downloads = pkg_obj.get("downloads", {})
            
            result.append({
                "name": package_info.get("name"),
                "version": package_info.get("version"),
                "description": package_info.get("description"),
                "downloads": downloads.get("downloads", 0),
                "score": pkg_obj.get("score", {}),
                "searchScore": pkg_obj.get("searchScore")
            })
        
        logger.info(f"Retrieved {len(result)} top packages.")
        return result

    def fetch_all_metadata_batch(self, package_names: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch metadata for a batch of package names.
        
        Args:
            package_names: List of package names.
            
        Returns:
            List of metadata dictionaries.
        """
        results = []
        for name in package_names:
            try:
                meta = self.get_package_metadata(name)
                if meta:
                    results.append(meta)
            except Exception as e:
                logger.warning(f"Skipping {name} due to error: {e}")
                continue
        return results