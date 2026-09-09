"""
OpenNeuro API Client for dataset discovery.

Implements dataset discovery using the OpenNeuro GraphQL API.
Provides methods to list datasets and retrieve detailed information
for specific datasets.
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
    
    Uses the OpenNeuro GraphQL API endpoint to query datasets.
    """
    BASE_URL = "https://api.openneuro.org/graphql"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenNeuro client.
        
        Args:
            api_key: OpenNeuro API key. If None, attempts to retrieve
                    from environment variables via get_openneuro_api_key().
        
        Raises:
            OpenNeuroClientError: If no API key is provided or found.
        """
        self.api_key = api_key or get_openneuro_api_key()
        if not self.api_key:
            raise OpenNeuroClientError(
                "API key is required. Provide it via constructor or "
                "set OPENNEURO_API_KEY environment variable."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the OpenNeuro API.
        
        Args:
            query: GraphQL query string.
            variables: Optional query variables.
        
        Returns:
            Dict containing the API response data.
        
        Raises:
            OpenNeuroClientError: If the request fails or returns an error.
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = self.session.post(self.BASE_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown API error")
                raise OpenNeuroClientError(f"API Error: {error_msg}")
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            raise OpenNeuroClientError(f"Request failed: {str(e)}")
    
    def list_datasets(
        self,
        limit: int = 100,
        dataset_id: Optional[str] = None,
        order: str = "created"
    ) -> Dict[str, Any]:
        """
        List datasets from OpenNeuro.
        
        Args:
            limit: Maximum number of datasets to return.
            dataset_id: Optional filter for specific dataset ID.
            order: Sorting order ('created', 'modified', 'label').
        
        Returns:
            Dict with 'datasets' key containing list of dataset summaries.
            Each dataset summary includes: id, label, created, modified,
            uploader, public, snapshot.
        
        Example:
            >>> client = OpenNeuroClient()
            >>> result = client.list_datasets(limit=10)
            >>> print(result['datasets'][0]['id'])
            'ds000001'
        """
        query = """
        query GetDatasets($limit: Int!, $datasetId: ID, $order: DatasetSort) {
            datasets(limit: $limit, datasetId: $datasetId, order: $order) {
                id
                label
                created
                modified
                uploader {
                    id
                    name
                    orcid
                }
                public
                snapshot {
                    id
                    tag
                    created
                }
            }
        }
        """
        
        variables = {
            "limit": limit,
            "datasetId": dataset_id,
            "order": order
        }
        
        data = self._execute_query(query, variables)
        return {"datasets": data.get("datasets", [])}
    
    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific dataset.
        
        Args:
            dataset_id: The OpenNeuro dataset ID (e.g., 'ds000001').
        
        Returns:
            Dict containing detailed dataset information including:
            - id, label, description
            - created, modified timestamps
            - uploader information
            - public status
            - snapshot details (tag, created)
            - summary (subject count, modalities, etc.)
        
        Raises:
            OpenNeuroClientError: If dataset not found or API error occurs.
        
        Example:
            >>> client = OpenNeuroClient()
            >>> info = client.get_dataset_info('ds000001')
            >>> print(info['description']['Name'])
            'Dataset Name'
        """
        query = """
        query GetDataset($datasetId: ID!) {
            dataset(id: $datasetId) {
                id
                label
                created
                modified
                public
                uploader {
                    id
                    name
                    orcid
                }
                description {
                    Name
                    Authors
                    License
                    Funding
                    ReferencesAndLinks
                    DatasetDOI
                }
                snapshot {
                    id
                    tag
                    created
                }
                summary {
                    modalities
                    subjectCount
                    subjectMetadata {
                        age
                        sex
                        group
                    }
                }
                issues {
                    severity
                    code
                    reason
                }
            }
        }
        """
        
        variables = {"datasetId": dataset_id}
        data = self._execute_query(query, variables)
        
        dataset_data = data.get("dataset")
        if not dataset_data:
            raise OpenNeuroClientError(f"Dataset '{dataset_id}' not found")
        
        return dataset_data


def create_client(api_key: Optional[str] = None) -> OpenNeuroClient:
    """
    Factory function to create an OpenNeuroClient instance.
    
    Args:
        api_key: Optional API key. If None, retrieves from environment.
    
    Returns:
        Configured OpenNeuroClient instance.
    
    Raises:
        OpenNeuroClientError: If API key cannot be obtained.
    """
    return OpenNeuroClient(api_key=api_key)
