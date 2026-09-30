"""
OpenNeuro API Client for dataset discovery.

Provides methods to list datasets and retrieve specific dataset information
from the OpenNeuro platform using their public API.
"""

import requests
from typing import Dict, Any, List, Optional
from src.config.env import get_openneuro_api_key

# API Configuration
OPENNEURO_API_BASE = "https://api.openneuro.org"
GRAPHQL_ENDPOINT = f"{OPENNEURO_API_BASE}/crn"


class OpenNeuroClientError(Exception):
    """Custom exception for OpenNeuro client errors."""
    pass


class OpenNeuroClient:
    """
    Client for interacting with the OpenNeuro API.

    Supports dataset discovery and retrieval of dataset metadata.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenNeuro client.

        Args:
            api_key: Optional API key for authenticated requests.
                    If not provided, attempts to load from environment.
        """
        self.api_key = api_key or get_openneuro_api_key()
        self.session = requests.Session()
        
        # Set headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add auth header if key is present
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.session.headers.update(headers)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Helper method to make HTTP requests to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            Parsed JSON response as a dictionary

        Raises:
            OpenNeuroClientError: If request fails or returns error status
        """
        url = f"{GRAPHQL_ENDPOINT}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise OpenNeuroClientError(f"API request failed: {e}")
        except ValueError as e:
            raise OpenNeuroClientError(f"Failed to parse JSON response: {e}")

    def list_datasets(
        self, 
        limit: int = 100, 
        offset: int = 0,
        dataset_id: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List datasets from OpenNeuro with optional filtering.

        Args:
            limit: Maximum number of datasets to return (default 100)
            offset: Number of datasets to skip (default 0)
            dataset_id: Optional specific dataset ID to retrieve
            keyword: Optional keyword to filter datasets

        Returns:
            Dictionary containing:
                - datasets: List of dataset metadata dictionaries
                - count: Total number of matching datasets
                - limit: Requested limit
                - offset: Requested offset

        Note:
            Uses OpenNeuro's GraphQL API for dataset listing.
        """
        query = """
        query Datasets($limit: Int!, $offset: Int!, $datasetId: ID, $keyword: String) {
            datasets(limit: $limit, offset: $offset, datasetId: $datasetId, keyword: $keyword) {
                id
                name
                description
                created
                uploader {
                    id
                    name
                    email
                }
                summary {
                    id
                    name
                    modalities
                    subjectCount
                    taskNames
                    size
                    totalFiles
                    dataProcessed
                    pet
                }
                permissions {
                    id
                    userPermissions {
                        id
                        userId
                        level
                        access
                        created
                    }
                }
                snapshots {
                    id
                    tag
                    created
                    description
                }
            }
        }
        """
        
        variables = {
            "limit": limit,
            "offset": offset
        }
        
        if dataset_id:
            variables["datasetId"] = dataset_id
        if keyword:
            variables["keyword"] = keyword

        try:
            response = self._request(
                "POST", 
                "", 
                json={"query": query, "variables": variables}
            )
            
            if "errors" in response:
                raise OpenNeuroClientError(f"API returned errors: {response['errors']}")
            
            datasets_data = response.get("data", {}).get("datasets", [])
            
            # Format response
            formatted_datasets = []
            for ds in datasets_data:
                formatted_datasets.append({
                    "id": ds.get("id"),
                    "name": ds.get("name"),
                    "description": ds.get("description", {}),
                    "created": ds.get("created"),
                    "uploader": ds.get("uploader"),
                    "summary": ds.get("summary"),
                    "permissions": ds.get("permissions"),
                    "snapshots": ds.get("snapshots")
                })

            return {
                "datasets": formatted_datasets,
                "count": len(formatted_datasets),
                "limit": limit,
                "offset": offset
            }

        except OpenNeuroClientError:
            raise
        except Exception as e:
            raise OpenNeuroClientError(f"Unexpected error listing datasets: {e}")

    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information for a specific dataset.

        Args:
            dataset_id: The OpenNeuro dataset ID (e.g., 'ds000001')

        Returns:
            Dictionary containing comprehensive dataset metadata including:
                - id: Dataset identifier
                - name: Dataset name
                - description: Dataset description
                - summary: Summary statistics (modalities, subjects, tasks, etc.)
                - snapshots: Available snapshot versions
                - latest snapshot info

        Raises:
            OpenNeuroClientError: If dataset not found or API error occurs

        Note:
            This method queries the GraphQL API for a single dataset.
        """
        query = """
        query Dataset($datasetId: ID!) {
            dataset(id: $datasetId) {
                id
                name
                description
                created
                modified
                uploader {
                    id
                    name
                    email
                }
                summary {
                    id
                    name
                    modalities
                    subjectCount
                    taskNames
                    size
                    totalFiles
                    dataProcessed
                    pet
                }
                permissions {
                    id
                    userPermissions {
                        id
                        userId
                        level
                        access
                        created
                    }
                }
                snapshots {
                    id
                    tag
                    created
                    description
                }
                analytics {
                    views
                    downloads
                }
                issues {
                    severity
                    code
                    explanation
                }
            }
        }
        """

        variables = {"datasetId": dataset_id}

        try:
            response = self._request(
                "POST",
                "",
                json={"query": query, "variables": variables}
            )

            if "errors" in response:
                raise OpenNeuroClientError(f"API returned errors: {response['errors']}")

            dataset_data = response.get("data", {}).get("dataset")
            
            if not dataset_data:
                raise OpenNeuroClientError(f"Dataset '{dataset_id}' not found")

            # Format the response
            return {
                "id": dataset_data.get("id"),
                "name": dataset_data.get("name"),
                "description": dataset_data.get("description", {}),
                "created": dataset_data.get("created"),
                "modified": dataset_data.get("modified"),
                "uploader": dataset_data.get("uploader"),
                "summary": dataset_data.get("summary"),
                "permissions": dataset_data.get("permissions"),
                "snapshots": dataset_data.get("snapshots"),
                "analytics": dataset_data.get("analytics"),
                "issues": dataset_data.get("issues"),
                "latest_snapshot": dataset_data.get("snapshots", [{}])[-1] if dataset_data.get("snapshots") else None
            }

        except OpenNeuroClientError:
            raise
        except Exception as e:
            raise OpenNeuroClientError(f"Unexpected error getting dataset info: {e}")

    def search_datasets(
        self, 
        keyword: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search for datasets by keyword.

        Args:
            keyword: Search term to find relevant datasets
            limit: Maximum number of results to return

        Returns:
            Dictionary containing search results with dataset metadata
        """
        return self.list_datasets(limit=limit, keyword=keyword)


def create_client(api_key: Optional[str] = None) -> OpenNeuroClient:
    """
    Factory function to create an OpenNeuroClient instance.

    Args:
        api_key: Optional API key. If not provided, loads from environment.

    Returns:
        Configured OpenNeuroClient instance
    """
    return OpenNeuroClient(api_key=api_key)