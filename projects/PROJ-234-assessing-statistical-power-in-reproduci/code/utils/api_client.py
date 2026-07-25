"""
OpenML API client with exponential backoff retry logic.
"""
import time
import requests
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class OpenMLClient:
    """
    A client for interacting with the OpenML API, featuring automatic retry
    logic for HTTP 429 (Too Many Requests) errors.
    """

    def __init__(self, base_url: str = "https://www.openml.org/api/v1", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_retry_adapter()

    def _setup_retry_adapter(self):
        """Configure retry strategy with exponential backoff for 429 errors."""
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a GET request to the specified endpoint.

        Args:
            endpoint: API endpoint path (e.g., 'data/list')
            params: Query parameters

        Returns:
            JSON response as a dictionary.

        Raises:
            requests.exceptions.RequestException: If the request fails after retries.
        """
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()


def fetch_top_classification_datasets(limit: int = 50) -> List[Dict]:
    """
    Fetch top classification datasets from OpenML.

    Args:
        limit: Maximum number of datasets to fetch.

    Returns:
        List of dataset metadata dictionaries.
    """
    client = OpenMLClient()
    try:
        # OpenML API endpoint for listing datasets
        # sort by number of downloads (descending) to get 'top' datasets
        params = {
            'limit': limit,
            'sort': 'downloads',
            'order': 'desc',
            'status': 'active',
            'tag': 'OpenML-Python' # Optional: filter for Python-tagged if desired, or remove for all
        }
        # Note: OpenML API v1 might require specific parameters for classification tasks.
        # A common query is: /data/list/limit/50/sort/number_of_downloads/order/desc
        # We'll use the standard list endpoint with filters.
        # If 'tag' is not needed, we can remove it. The spec implies 'top' usually means downloads.
        
        # Correcting params for standard OpenML data list:
        # https://openml.org/api/v1/json/data/list/limit/50/sort/number_of_downloads/order/desc
        # We need to construct the URL manually or use the client correctly.
        # The client's get method expects an endpoint.
        
        # Let's use the specific endpoint for data listing
        # endpoint: data/list
        # params: limit, sort, order
        
        # Overwriting params to match standard API usage for "top"
        params = {
            'limit': limit,
            'sort': 'number_of_downloads',
            'order': 'desc',
            'status': 'active'
        }
        
        response_data = client.get("data/list", params)
        
        datasets = []
        if "datasets" in response_data:
            for ds in response_data["datasets"]:
                datasets.append(ds)
        
        return datasets

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch datasets from OpenML: {e}")
