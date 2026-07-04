"""
OpenNeuro API client for dataset discovery.

Provides methods to list available datasets and retrieve detailed information
for specific datasets using the OpenNeuro GraphQL API.
"""

import requests
from typing import Dict, Any, List, Optional

from src.config.env import get_openneuro_api_key


class OpenNeuroClientError(Exception):
    """Custom exception for OpenNeuro client errors."""
    pass


class OpenNeuroClient:
    """
    Client for interacting with the OpenNeuro API.

    Attributes:
        api_key (str): The API key for authentication.
        base_url (str): The base URL for the OpenNeuro API.
    """

    BASE_URL = "https://api.openneuro.org"
    GRAPHQL_ENDPOINT = "/crn/graphql"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenNeuroClient.

        Args:
            api_key: Optional API key. If not provided, attempts to load from env.

        Raises:
            OpenNeuroClientError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or get_openneuro_api_key()
        if not self.api_key:
            raise OpenNeuroClientError(
                "OpenNeuro API key is required. Provide it via argument or set OPENNEURO_API_KEY env var."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _post_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the OpenNeuro API.

        Args:
            query: The GraphQL query string.
            variables: Optional dictionary of query variables.

        Returns:
            The JSON response from the API.

        Raises:
            OpenNeuroClientError: If the request fails or returns an error.
        """
        payload = {"query": query, "variables": variables or {}}
        try:
            response = self.session.post(
                f"{self.BASE_URL}{self.GRAPHQL_ENDPOINT}",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown API error")
                raise OpenNeuroClientError(f"API Error: {error_msg}")
            
            return result
        except requests.exceptions.RequestException as e:
            raise OpenNeuroClientError(f"Network error: {e}")

    def list_datasets(self, limit: int = 20, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available datasets on OpenNeuro.

        Args:
            limit: Maximum number of datasets to return.
            dataset_id: Optional specific dataset ID to filter by (exact match).
                        If provided, returns a list with at most one item.

        Returns:
            A list of dictionaries, where each dict represents a dataset with keys:
            'id', 'label', 'name', 'snapshot', 'created'.

        Raises:
            OpenNeuroClientError: If the API call fails.
        """
        # Query to fetch datasets with basic metadata
        query = """
        query GetDatasets($limit: Int, $datasetId: ID) {
            datasets(limit: $limit, datasetId: $datasetId) {
                id
                label
                name
                created
                snapshot {
                    id
                    tag
                    summary {
                        modalities
                        sessions
                        subjects
                        subjectMetadata {
                            participantId
                            age
                            sex
                            group
                        }
                    }
                }
            }
        }
        """
        
        variables = {"limit": limit}
        if dataset_id:
            variables["datasetId"] = dataset_id

        result = self._post_query(query, variables)
        
        datasets = result.get("data", {}).get("datasets", [])
        formatted_list = []
        
        for ds in datasets:
            snapshot = ds.get("snapshot", {})
            formatted_list.append({
                "id": ds.get("id"),
                "label": ds.get("label"),
                "name": ds.get("name"),
                "created": ds.get("created"),
                "snapshot_id": snapshot.get("id"),
                "snapshot_tag": snapshot.get("tag"),
                "summary": snapshot.get("summary", {})
            })
        
        return formatted_list

    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information for a specific dataset.

        Args:
            dataset_id: The unique identifier of the dataset (e.g., 'ds000001').

        Returns:
            A dictionary containing detailed dataset information including:
            'id', 'name', 'description', 'license', 'created', 'modified',
            'snapshot', 'downloads', 'publishers'.

        Raises:
            OpenNeuroClientError: If the dataset is not found or API fails.
        """
        query = """
        query GetDataset($datasetId: ID!) {
            dataset(datasetId: $datasetId) {
                id
                name
                description
                license
                created
                modified
                downloads
                snapshots {
                    id
                    tag
                    created
                }
                permissions {
                    users {
                        id
                        email
                        role
                    }
                }
                analytics {
                    views
                    downloads
                }
            }
        }
        """
        
        result = self._post_query(query, {"datasetId": dataset_id})
        
        dataset = result.get("data", {}).get("dataset")
        
        if not dataset:
            raise OpenNeuroClientError(f"Dataset '{dataset_id}' not found.")
        
        return {
            "id": dataset.get("id"),
            "name": dataset.get("name"),
            "description": dataset.get("description"),
            "license": dataset.get("license"),
            "created": dataset.get("created"),
            "modified": dataset.get("modified"),
            "downloads": dataset.get("downloads"),
            "snapshots": dataset.get("snapshots", []),
            "analytics": dataset.get("analytics", {})
        }


def create_client(api_key: Optional[str] = None) -> OpenNeuroClient:
    """
    Factory function to create an OpenNeuroClient instance.

    Args:
        api_key: Optional API key.

    Returns:
        An instance of OpenNeuroClient.
    """
    return OpenNeuroClient(api_key=api_key)
