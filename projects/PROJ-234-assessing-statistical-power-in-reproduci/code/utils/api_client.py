"""
API Client for OpenML with exponential backoff retry logic.
Handles HTTP 429 (Too Many Requests) specifically.
"""
import time
import requests
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class OpenMLClient:
    """
    A client for interacting with the OpenML API with robust retry logic.
    """

    def __init__(
        self,
        base_url: str = "https://www.openml.org/api/v1",
        max_retries: int = 5,
        backoff_factor: float = 0.5,
        status_forcelist: Optional[List[int]] = None
    ):
        """
        Initialize the OpenML client.

        Args:
            base_url: The base URL for the OpenML API.
            max_retries: Maximum number of retry attempts.
            backoff_factor: Factor to increase wait time between retries.
            status_forcelist: List of HTTP status codes to retry on. Defaults to 429, 500, 502, 503, 504.
        """
        self.base_url = base_url
        self.session = requests.Session()

        if status_forcelist is None:
            status_forcelist = [429, 500, 502, 503, 504]

        # Configure Retry strategy with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["GET", "POST", "HEAD"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Perform a GET request to the specified endpoint.

        Args:
            endpoint: The API endpoint path (e.g., '/data/list').
            params: Optional query parameters.
            timeout: Request timeout in seconds.

        Returns:
            The JSON response as a dictionary.

        Raises:
            requests.exceptions.RequestException: If the request fails after all retries.
            ValueError: If the response is not valid JSON.
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            
            # Explicitly handle 429 if it slips through (though Retry handles most)
            if response.status_code == 429:
                # Log or handle specific 429 logic if needed before raising
                response.raise_for_status()

            response.raise_for_status()
            
            try:
                return response.json()
            except ValueError as e:
                raise ValueError(f"Response was not valid JSON: {response.text[:200]}") from e

        except requests.exceptions.RequestException as e:
            # Re-raise to be caught by caller if needed
            raise e

def fetch_top_classification_datasets(limit: int = 50) -> List[Dict]:
    """
    Helper function to fetch top classification datasets using the OpenMLClient.
    This wraps the client logic for easy access in ingestion scripts.

    Args:
        limit: Maximum number of datasets to fetch.

    Returns:
        List of dataset metadata dictionaries.
    """
    client = OpenMLClient()
    params = {
        'limit': limit,
        'data_feature': 'classification',
        'sort': 'downloads',
        'order': 'desc'
    }
    
    # OpenML API v1 endpoint for listing datasets
    response_data = client.get('/data/list', params=params)
    
    if 'datasets' in response_data:
        return response_data['datasets']
    return []
