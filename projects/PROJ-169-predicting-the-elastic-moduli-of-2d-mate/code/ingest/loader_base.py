"""
Abstract base class for data loaders.

This module defines the `DataLoader` interface, which standardizes the interaction
between the pipeline and various data sources (e.g., Materials Project, AFLOW).

WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. 
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class DataLoader(ABC):
    """Abstract base class for data loaders.
    
    This class must support dynamic switching between 'materials_project' and 'aflow'
    via a configuration key. Concrete implementations for each source must inherit 
    from this base.
    """

    def __init__(self, source: str):
        """
        Initialize the data loader.
        
        Args:
            source: The data source identifier ('materials_project' or 'aflow').
        """
        self.source = source
        logger.info(f"Initializing DataLoader for source: {source}")

    @abstractmethod
    def fetch_data(self, output_dir, limit: Optional[int] = None) -> Any:
        """
        Fetch data from the source.
        
        Args:
            output_dir: Directory to save fetched data.
            limit: Optional limit on number of entries to fetch.
        
        Returns:
            Manifest or metadata object describing the fetched data.
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
            RuntimeError: If the real data source is unreachable.
        """
        pass

    @abstractmethod
    def validate_source(self) -> bool:
        """
        Validate the source configuration and connectivity.
        
        Returns:
            True if the source is valid and accessible, False otherwise.
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the source.
        
        Returns:
            A dictionary containing source metadata (e.g., version, last_updated, 
            total_entries, source_name).
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass

    def _check_source_env(self) -> None:
        """
        Helper to verify the source matches the environment configuration.
        
        This ensures that the loader is not instantiated with a source that
        conflicts with the global DATA_SOURCE environment variable if set.
        """
        env_source = os.getenv('DATA_SOURCE')
        if env_source and env_source != self.source:
            logger.warning(
                f"Source mismatch: Environment variable DATA_SOURCE={env_source} "
                f"but loader initialized with source={self.source}. "
                f"This may indicate a configuration error."
            )

    def _ensure_output_dir(self, output_dir) -> None:
        """
        Ensure the output directory exists.
        
        Args:
            output_dir: Path to the output directory.
        """
        path = output_dir if isinstance(output_dir, str) else str(output_dir)
        os.makedirs(path, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {path}")