"""
OpenNeuro API Client for dataset discovery and metadata retrieval.

This module provides a client to interact with the OpenNeuro GraphQL API
to list datasets, retrieve dataset information, and download dataset metadata.
"""

import requests
import logging
from typing import Dict, Any, List, Optional

from src.config.env import get_openneuro_api_key

logger = logging.getLogger(__name__)

# OpenNeuro GraphQL API endpoint
OPENNEURO_API_URL = "https://api.openneuro.org/graphql"

class OpenNeuroClientError(Exception):
    """Custom exception for OpenNeuro client errors."""
    pass

class OpenNeuroClient:
    """
    Client for interacting with the OpenNeuro API.

    This client handles authentication, API requests, and response parsing
    for dataset discovery and metadata retrieval.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenNeuro client.

        Args:
            api_key: OpenNeuro API key. If None, attempts to retrieve from
                     environment variables via get_openneuro_api_key().

        Raises:
            OpenNeuroClientError: If no API key is provided or found.
        """
        self.api_key = api_key or get_openneuro_api_key()
        if not self.api_key:
            raise OpenNeuroClientError(
                "OpenNeuro API key not provided and not found in environment. "
                "Set OPENNEURO_API_KEY or pass api_key to constructor."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        })
        logger.info("OpenNeuroClient initialized successfully")

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the OpenNeuro API.

        Args:
            query: GraphQL query string.
            variables: Optional dictionary of query variables.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            OpenNeuroClientError: If the API request fails.
        """
        try:
            payload = {"query": query, "variables": variables or {}}
            response = self.session.post(OPENNEURO_API_URL, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown API error")
                raise OpenNeuroClientError(f"API Error: {error_msg}")

            return result.get("data", {})

        except requests.RequestException as e:
            raise OpenNeuroClientError(f"Network error during API call: {e}")
        except ValueError as e:
            raise OpenNeuroClientError(f"Failed to parse JSON response: {e}")

    def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List available datasets from OpenNeuro.

        Args:
            limit: Maximum number of datasets to return (default: 100).
            offset: Number of datasets to skip for pagination (default: 0).

        Returns:
            List of dictionaries containing dataset metadata:
            - id: Dataset ID (e.g., 'ds000001')
            - label: Human-readable label
            - name: Dataset name
            - uploaded: Upload timestamp
            - modified: Last modification timestamp
            - snapshot: Latest snapshot version

        Raises:
            OpenNeuroClientError: If the API call fails.
        """
        query = """
        query GetDatasets($limit: Int!, $offset: Int!) {
            datasets(limit: $limit, offset: $offset) {
                id
                label
                name
                uploaded
                modified
                snapshot {
                    id
                    tag
                }
            }
        }
        """

        variables = {"limit": limit, "offset": offset}
        result = self._execute_query(query, variables)

        datasets = result.get("datasets", [])
        logger.info(f"Retrieved {len(datasets)} datasets (offset={offset}, limit={limit})")

        return datasets

    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific dataset.

        Args:
            dataset_id: OpenNeuro dataset ID (e.g., 'ds000001').

        Returns:
            Dictionary containing detailed dataset metadata including:
            - id, label, name, description
            - uploader information
            - summary statistics (subject count, modalities)
            - latest snapshot version

        Raises:
            OpenNeuroClientError: If the dataset is not found or API fails.
        """
        query = """
        query GetDataset($datasetId: ID!) {
            dataset(id: $datasetId) {
                id
                label
                name
                description {
                    Name
                    Authors
                    Version
                    DOI
                }
                uploader {
                    id
                    name
                    email
                }
                summary {
                    subjectCount
                    modalities
                    sessions
                    tasks
                }
                snapshot {
                    id
                    tag
                    created
                }
            }
        }
        """

        variables = {"datasetId": dataset_id}
        result = self._execute_query(query, variables)

        dataset = result.get("dataset")
        if not dataset:
            raise OpenNeuroClientError(f"Dataset '{dataset_id}' not found")

        logger.info(f"Retrieved info for dataset: {dataset_id}")
        return dataset

def create_client(api_key: Optional[str] = None) -> OpenNeuroClient:
    """
    Factory function to create an OpenNeuroClient instance.

    Args:
        api_key: Optional API key. If None, uses environment variable.

    Returns:
        Configured OpenNeuroClient instance.
    """
    return OpenNeuroClient(api_key=api_key)
