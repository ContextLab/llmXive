"""
Base class for unified dataset loaders.

This module defines the abstract base class for data loading from various sources
(Materials Project, AFLOW, OQMD) to ensure a consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataLoader(ABC):
    """
    Abstract base class for dataset loaders.

    Subclasses must implement fetch_data(), validate_source(), and get_metadata().
    """

    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch data from the configured source.

        Returns:
            DataFrame containing the raw data.
        """
        pass

    @abstractmethod
    def validate_source(self) -> bool:
        """
        Validate that the source is accessible and returns valid data.

        Returns:
            True if validation passes, False otherwise.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the loaded dataset.

        Returns:
            Dictionary with source info, record count, and column names.
        """
        pass

    def __init__(self, source: str, output_dir: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            source: The data source identifier.
            output_dir: Directory to save data.
        """
        self.source = source
        self.output_dir = output_dir
        logger.info(f"Initialized {self.__class__.__name__} for source: {source}")
