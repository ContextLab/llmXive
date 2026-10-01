"""
OpenML API Client with retry logic.
"""
import time
import requests
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)

class OpenMLClient:
    """
    A client for interacting with the OpenML API with exponential backoff retry logic.
    """
    def __init__(self, base_url: str = "https://www.openml.org/api/v1", max_retries: int = 3):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configure retry strategy for 429 (Too Many Requests) and 5xx errors
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the OpenML API with retry logic.
        
        Args:
            endpoint: The API endpoint (e.g., '/dataset/list').
            params: Query parameters.
            
        Returns:
            The JSON response as a dictionary.
            
        Raises:
            requests.HTTPError: If the request fails after retries.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Accept": "application/json"}
        
        logger.debug(f"Requesting {url} with params {params}")
        
        response = self.session.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()

def fetch_top_classification_datasets(limit: int = 50) -> List[Dict]:
    """
    Fetch top classification datasets from OpenML.
    
    Args:
        limit: Maximum number of datasets to fetch.
        
    Returns:
        A list of dataset dictionaries.
    """
    client = OpenMLClient()
    
    try:
        # OpenML API endpoint for dataset listing
        # task_type=3 corresponds to classification
        data = client._request("/dataset/list", {
            "limit": limit,
            "task_type": "3", # Classification
            "sort": "downloads" # Sort by downloads to get "top" datasets
        })
        
        datasets = data.get("datasets", {}).get("dataset", [])
        
        # Normalize the response (sometimes it's a list, sometimes a single dict)
        if isinstance(datasets, dict):
            datasets = [datasets]
            
        return datasets
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch datasets from OpenML: {e}")
        raise

# Alias for backward compatibility if needed, though main usage is via function
__all__ = ["OpenMLClient", "fetch_top_classification_datasets"]
