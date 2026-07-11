"""
Base Memory Store Interface for llmXive.

Defines the abstract base class for Coarse, Medium, and Fine stores.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class MemoryStore(ABC):
    """
    Abstract base class for memory stores.
    Each store implementation defines a different level of abstraction for context retrieval.
    """

    def __init__(self):
        self.index: List[Dict[str, Any]] = []
        self.faiss_index = None
        self.valid_ids: List[str] = []

    @abstractmethod
    def load_data(self, data_path: str) -> None:
        """
        Load and process data from the specified path.
        
        Args:
            data_path: Path to the data source.
        """
        pass

    @abstractmethod
    def get_context(self, query_id: str, top_k: int = 5) -> str:
        """
        Retrieve context for a given query.
        
        Args:
            query_id: The ID of the query.
            top_k: Number of top results to retrieve.
            
        Returns:
            Context string for the query.
        """
        pass

    @abstractmethod
    def build_index(self) -> None:
        """
        Build the retrieval index (e.g., FAISS) for the loaded data.
        """
        pass

    @abstractmethod
    def save(self, output_path: str) -> None:
        """
        Save the store state to disk.
        
        Args:
            output_path: Path to save the store.
        """
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "MemoryStore":
        """
        Load a store from disk.
        
        Args:
            path: Path to the saved store.
            
        Returns:
            Loaded store instance.
        """
        pass
