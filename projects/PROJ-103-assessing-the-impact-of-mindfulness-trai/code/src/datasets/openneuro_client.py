import requests
from typing import Dict, Any, List, Optional
import logging
from src.config.env import get_openneuro_api_key

logger = logging.getLogger(__name__)

class OpenNeuroClientError(Exception):
    """Base exception for OpenNeuro client errors."""
    pass


class DatasetNotFoundError(OpenNeuroClientError):
    """Raised when a requested dataset is not found."""
    pass


class DatasetAccessError(OpenNeuroClientError):
    """Raised when access to a dataset is denied or fails."""
    pass


class OpenNeuroClient:
    """
    Client for interacting with the OpenNeuro API.
    
    Provides methods to list datasets and retrieve detailed information
    about specific datasets.
    """
    
    API_BASE_URL = "https://api.openneuro.org"
    GRAPHQL_ENDPOINT = f"{API_BASE_URL}/crn/graphql"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenNeuro client.
        
        Args:
            api_key: OpenNeuro API key. If not provided, attempts to load
                    from environment variable OPENNEURO_API_KEY.
        """
        self.api_key = api_key or get_openneuro_api_key()
        if not self.api_key:
            raise OpenNeuroClientError(
                "OpenNeuro API key is required. Set OPENNEURO_API_KEY "
                "environment variable or pass it to the client."
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
            query: GraphQL query string
            variables: Optional query variables
        
        Returns:
            Parsed JSON response
        
        Raises:
            OpenNeuroClientError: If the request fails
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = self.session.post(
                self.GRAPHQL_ENDPOINT,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown API error")
                raise OpenNeuroClientError(f"API Error: {error_msg}")
            
            return result
        
        except requests.exceptions.Timeout:
            raise OpenNeuroClientError("Request to OpenNeuro API timed out")
        except requests.exceptions.RequestException as e:
            raise OpenNeuroClientError(f"Request failed: {str(e)}")
    
    def list_datasets(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List available datasets from OpenNeuro.
        
        Args:
            limit: Maximum number of datasets to return
            offset: Number of datasets to skip (for pagination)
        
        Returns:
            List of dataset dictionaries containing id, label, and snapshot information
        """
        query = """
        query DatasetList($limit: Int, $offset: Int) {
            datasets(limit: $limit, offset: $offset) {
                id
                label
                snapshot {
                    id
                    created
                }
            }
        }
        """
        
        variables = {"limit": limit, "offset": offset}
        result = self._execute_query(query, variables)
        
        datasets = result.get("data", {}).get("datasets", [])
        return [
            {
                "id": ds["id"],
                "label": ds["label"],
                "snapshot_id": ds.get("snapshot", {}).get("id"),
                "created": ds.get("snapshot", {}).get("created")
            }
            for ds in datasets
        ]
    
    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific dataset.
        
        Args:
            dataset_id: The OpenNeuro dataset ID (e.g., 'ds000001')
        
        Returns:
            Dictionary containing dataset metadata including:
            - id: Dataset identifier
            - label: Human-readable name
            - description: Dataset description
            - created: Creation timestamp
            - modified: Last modification timestamp
            - snapshot: Snapshot information
            - uploader: Uploader information
        
        Raises:
            DatasetNotFoundError: If the dataset does not exist
            DatasetAccessError: If the dataset cannot be accessed
            OpenNeuroClientError: For other API errors
        
        Examples:
            >>> client = OpenNeuroClient()
            >>> info = client.get_dataset_info("ds000001")
            >>> print(info['label'])
            'Dataset Name'
        """
        if not dataset_id or not isinstance(dataset_id, str):
            raise OpenNeuroClientError("Dataset ID must be a non-empty string")
        
        query = """
        query Dataset($datasetId: ID!) {
            dataset(id: $datasetId) {
                id
                label
                description
                created
                modified
                snapshot {
                    id
                    created
                    description
                    summary {
                        totalSubjects
                        totalSessions
                        modalities
                    }
                }
                uploader {
                    id
                    name
                    email
                }
                permissions {
                    public
                    users {
                        id
                        role
                    }
                    groups {
                        id
                        role
                    }
                }
            }
        }
        """
        
        variables = {"datasetId": dataset_id}
        
        try:
            result = self._execute_query(query, variables)
            dataset = result.get("data", {}).get("dataset")
            
            if dataset is None:
                raise DatasetNotFoundError(
                    f"Dataset '{dataset_id}' not found. "
                    "Please verify the dataset ID exists on OpenNeuro."
                )
            
            # Extract and structure the response
            snapshot = dataset.get("snapshot") or {}
            description = dataset.get("description") or {}
            uploader = dataset.get("uploader") or {}
            permissions = dataset.get("permissions") or {}
            
            return {
                "id": dataset["id"],
                "label": dataset["label"],
                "description": description.get("description") or description.get("Name", "No description available"),
                "created": dataset.get("created"),
                "modified": dataset.get("modified"),
                "snapshot": {
                    "id": snapshot.get("id"),
                    "created": snapshot.get("created"),
                    "description": snapshot.get("description"),
                    "summary": snapshot.get("summary") or {
                        "totalSubjects": 0,
                        "totalSessions": 0,
                        "modalities": []
                    }
                },
                "uploader": {
                    "id": uploader.get("id"),
                    "name": uploader.get("name"),
                    "email": uploader.get("email")
                },
                "public": permissions.get("public", False),
                "num_subjects": snapshot.get("summary", {}).get("totalSubjects", 0),
                "modalities": snapshot.get("summary", {}).get("modalities", [])
            }
        
        except DatasetNotFoundError:
            raise
        except OpenNeuroClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving dataset {dataset_id}: {str(e)}")
            raise OpenNeuroClientError(f"Failed to retrieve dataset info: {str(e)}")


def create_client(api_key: Optional[str] = None) -> OpenNeuroClient:
    """
    Factory function to create an OpenNeuroClient instance.
    
    Args:
        api_key: Optional API key. If not provided, uses environment variable.
    
    Returns:
        Configured OpenNeuroClient instance
    """
    return OpenNeuroClient(api_key=api_key)
