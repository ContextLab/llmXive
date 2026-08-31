"""
Abstract base class for data loaders.

This module defines the `DataLoader` interface, which standardizes the interaction
between the pipeline and various data sources (e.g., Materials Project, AFLOW).

WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. 
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""
from __future__ import annotations

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

    def __init__(self, source: str, output_dir: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            source: The data source identifier (e.g., 'materials_project', 'aflow').
            output_dir: Directory to save data.
        """
        self.source = source
        self.output_dir = output_dir
        logger.info(f"Initialized {self.__class__.__name__} for source: {source}")

    @abstractmethod
    def fetch_data(self, output_dir: str, limit: Optional[int] = None) -> Any:
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
        raise NotImplementedError("Subclasses must implement fetch_data()")

    @abstractmethod
    def validate_source(self) -> bool:
        """
        Validate the source configuration and connectivity.
        
        Returns:
            True if the source is valid and accessible, False otherwise.
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement validate_source()")

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
        raise NotImplementedError("Subclasses must implement get_metadata()")