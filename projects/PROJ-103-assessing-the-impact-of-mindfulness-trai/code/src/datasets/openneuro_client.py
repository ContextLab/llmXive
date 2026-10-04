"""
OpenNeuro API client for dataset discovery.

Implements dataset discovery via the OpenNeuro GraphQL API.
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

    Uses the public GraphQL endpoint to discover datasets and retrieve metadata.
    """
    API_BASE_URL = "https://api.openneuro.org"
    GRAPHQL_ENDPOINT = f"{API_BASE_URL}/crn/graphql"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenNeuro client.

        Args:
            api_key: OpenNeuro API key. If None, attempts to load from environment.
        """
        self.api_key = api_key or get_openneuro_api_key()
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": self.api_key})
        self.session.headers.update({"Content-Type": "application/json"})

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the OpenNeuro API.

        Args:
            query: The GraphQL query string.
            variables: Optional dictionary of query variables.

        Returns:
            The JSON response data.

        Raises:
            OpenNeuroClientError: If the request fails or returns an error.
        """
        try:
            response = self.session.post(
                self.GRAPHQL_ENDPOINT,
                json={"query": query, "variables": variables or {}},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown API error")
                raise OpenNeuroClientError(f"GraphQL API error: {error_msg}")

            return result.get("data", {})

        except requests.exceptions.RequestException as e:
            raise OpenNeuroClientError(f"Network error during API request: {e}")
        except ValueError as e:
            raise OpenNeuroClientError(f"Failed to parse API response JSON: {e}")

    def list_datasets(
        self,
        limit: int = 20,
        order: str = "createdAt",
        dataset_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List datasets from OpenNeuro.

        Args:
            limit: Maximum number of datasets to return.
            order: Sorting order (e.g., 'createdAt', 'modified', 'uploadDate').
            dataset_id: Optional filter to return only a specific dataset.

        Returns:
            A list of dataset dictionaries containing metadata.
        """
        query = """
        query Datasets($first: Int, $orderBy: DatasetSort, $datasetId: ID) {
            datasets(first: $first, orderBy: $orderBy, id: $datasetId) {
                id
                label
                description
                created
                uploader {
                    id
                    name
                    orcid
                }
                permissions {
                    users {
                        id
                        name
                        email
                    }
                    public
                }
                snapshot {
                    id
                    created
                    tags
                    description
                    summary {
                        subjects
                        modalities
                        totalSubjects
                        secondaryModalities
                    }
                }
            }
        }
        """
        variables = {"first": limit, "orderBy": {"field": order, "direction": "DESC"}}
        if dataset_id:
            variables["datasetId"] = dataset_id

        data = self._execute_query(query, variables)
        return data.get("datasets", [])

    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information for a specific dataset.

        Args:
            dataset_id: The OpenNeuro dataset ID (e.g., 'ds000001').

        Returns:
            A dictionary containing comprehensive dataset metadata.

        Raises:
            OpenNeuroClientError: If the dataset is not found.
        """
        query = """
        query Dataset($id: ID!) {
            dataset(id: $id) {
                id
                label
                description
                created
                uploader {
                    id
                    name
                    orcid
                }
                permissions {
                    users {
                        id
                        name
                        email
                    }
                    public
                }
                snapshots {
                    id
                    created
                    tags
                    description
                    summary {
                        subjects
                        modalities
                        totalSubjects
                        secondaryModalities
                    }
                }
                latestSnapshot {
                    id
                    created
                    tags
                    description
                    summary {
                        subjects
                        modalities
                        totalSubjects
                        secondaryModalities
                    }
                }
            }
        }
        """
        variables = {"id": dataset_id}
        data = self._execute_query(query, variables)
        dataset = data.get("dataset")

        if not dataset:
            raise OpenNeuroClientError(f"Dataset '{dataset_id}' not found.")

        return dataset

def create_client(api_key: Optional[str] = None) -> OpenNeuroClient:
    """
    Factory function to create an OpenNeuroClient instance.

    Args:
        api_key: Optional API key. If None, loads from environment.

    Returns:
        An initialized OpenNeuroClient.
    """
    return OpenNeuroClient(api_key=api_key)
