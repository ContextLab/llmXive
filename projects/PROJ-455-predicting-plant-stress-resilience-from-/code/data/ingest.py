import os
import re
import json
import hashlib
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any, Type, Union
import pandas as pd
import numpy as np

from utils.logging import get_logger, DataRejectionError
from data.models import MetabolomicProfile, StressType

logger = get_logger(__name__)


class BaseAdapter:
    """Abstract base class for data adapters."""
    
    def fetch(self, accession_id: str, source: str) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch()")
    
    def parse(self, raw_data: Any, source: str) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement parse()")


class MockAdapter(BaseAdapter):
    """Adapter that wraps the synthetic generator for testing."""
    
    def fetch(self, accession_id: str, source: str) -> pd.DataFrame:
        """
        Generate synthetic data via the generator module.
        Expects accession_id to encode stress type and seed if needed.
        """
        logger.info(f"MockAdapter fetching synthetic data for {accession_id}")
        
        # Parse accession_id to determine stress type (simplified)
        # Format: "synthetic_<stress_type>_<seed>" or just "synthetic_<stress_type>"
        parts = accession_id.split('_')
        if len(parts) < 2 or parts[0] != 'synthetic':
            stress_type = 'drought'
            seed = 42
        else:
            stress_type = parts[1] if len(parts) > 1 else 'drought'
            seed = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 42
        
        # Import here to avoid circular dependencies
        from data.generator import generate_synthetic_data
        
        # Generate with default missing rate (0.05) - T015 handles rejection for >10%
        output_path = f"data/raw/synthetic_{stress_type}_{seed}.parquet"
        df = generate_synthetic_data(n_samples=100, stress_type=stress_type, 
                                   missing_rate=0.05, seed=seed)
        
        # Save to expected path
        df.to_parquet(output_path, index=False)
        logger.info(f"MockAdapter generated and saved synthetic data to {output_path}")
        
        return df
    
    def parse(self, raw_data: Any, source: str) -> pd.DataFrame:
        """Mock parsing - returns data as-is since generator already outputs DataFrame."""
        if isinstance(raw_data, pd.DataFrame):
            return raw_data
        raise DataRejectionError("MockAdapter expects DataFrame input")


class RealAdapter(BaseAdapter):
    """
    Adapter for fetching real external datasets from NCBI GEO, Zenodo, etc.
    
    CURRENT STATUS: STUB IMPLEMENTATION
    
    This class is a placeholder to prevent accidental execution of unverified
    real-data fetch logic. Real dataset fetching requires:
    1. Verified API keys/credentials
    2. Tested parsing logic for specific source formats
    3. Validation against actual dataset schemas
    
    For current testing, please use the synthetic data generator via MockAdapter.
    """
    
    def fetch(self, accession_id: str, source: str) -> pd.DataFrame:
        """
        Stub implementation that raises NotImplementedError.
        
        Args:
            accession_id: The dataset accession ID (e.g., GEO GSM ID, Zenodo DOI)
            source: The data source ('ncbi_geo', 'zenodo', etc.)
        
        Raises:
            NotImplementedError: Always raised with guidance to use synthetic data
        """
        raise NotImplementedError(
            "RealAdapter.fetch() is not yet implemented. "
            "Real data fetching requires verified API integration and parsing logic. "
            "For current testing and development, please use the synthetic data generator "
            "via MockAdapter or the generate_synthetic_data() function directly. "
            "To enable real data fetching, complete tasks T009.1.1 and T009.1.2 which "
            "implement the ExternalDatasetManager with proper API integration."
        )
    
    def parse(self, raw_data: Any, source: str) -> pd.DataFrame:
        """
        Stub implementation that raises NotImplementedError.
        
        Args:
            raw_data: Raw data from fetch()
            source: The data source
        
        Raises:
            NotImplementedError: Always raised
        """
        raise NotImplementedError(
            "RealAdapter.parse() is not yet implemented. "
            "Real data parsing requires source-specific logic for NCBI GEO, Zenodo, etc. "
            "Please use MockAdapter for testing with synthetic data."
        )


class ExternalDatasetManager:
    """
    Manager for fetching, parsing, and validating external datasets.
    
    Currently delegates to RealAdapter which is a stub.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.adapters: Dict[str, BaseAdapter] = {
            'mock': MockAdapter(),
            'real': RealAdapter(),
            'ncbi_geo': RealAdapter(),
            'zenodo': RealAdapter()
        }
    
    def get_adapter(self, source: str) -> BaseAdapter:
        """Get the appropriate adapter for the source."""
        return self.adapters.get(source.lower(), self.adapters['real'])
    
    def fetch(self, accession_id: str, source: str = 'mock') -> pd.DataFrame:
        """
        Fetch dataset from the specified source.
        
        Args:
            accession_id: Dataset identifier
            source: Data source ('mock', 'ncbi_geo', 'zenodo', etc.)
        
        Returns:
            DataFrame with metabolomic data
        
        Raises:
            NotImplementedError: If source is not 'mock'
            DataRejectionError: If data fails validation
        """
        adapter = self.get_adapter(source)
        return adapter.fetch(accession_id, source)
    
    def parse(self, raw_data: Any, source: str) -> pd.DataFrame:
        """Parse raw data from the specified source."""
        adapter = self.get_adapter(source)
        return adapter.parse(raw_data, source)
    
    def ingest(self, accession_id: str, source: str = 'mock') -> pd.DataFrame:
        """
        Complete ingestion pipeline: fetch and parse.
        
        Args:
            accession_id: Dataset identifier
            source: Data source
        
        Returns:
            Validated DataFrame
        """
        raw_data = self.fetch(accession_id, source)
        parsed_data = self.parse(raw_data, source)
        
        # Basic validation
        required_cols = ['sample_id', 'metabolite_name', 'concentration']
        missing_cols = [col for col in required_cols if col not in parsed_data.columns]
        if missing_cols:
            raise DataRejectionError(f"Missing required columns: {missing_cols}")
        
        return parsed_data


def get_adapter(source: str) -> BaseAdapter:
    """
    Factory function to get an adapter instance.
    
    Args:
        source: Data source identifier
    
    Returns:
        Appropriate adapter instance
    """
    manager = ExternalDatasetManager()
    return manager.get_adapter(source)


def filter_by_recovery_time(df: pd.DataFrame, min_days: int = 7) -> pd.DataFrame:
    """
    Filter datasets for samples with recovery time >= min_days.
    
    Args:
        df: Input DataFrame with 'recovery_time_days' column
        min_days: Minimum recovery time in days (default: 7)
    
    Returns:
        Filtered DataFrame
    
    Raises:
        DataRejectionError: If required column is missing
    """
    logger = get_logger(__name__)
    
    if 'recovery_time_days' not in df.columns:
        raise DataRejectionError("DataFrame missing required column: 'recovery_time_days'")
    
    filtered_df = df[df['recovery_time_days'] >= min_days].copy()
    logger.info(f"Filtered {len(df) - len(filtered_df)} samples with recovery time < {min_days} days")
    
    return filtered_df


def validate_and_handle_rejection(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Validate dataset and handle rejection scenarios with logging.
    
    Args:
        df: Input DataFrame
        source: Data source identifier
    
    Returns:
        Validated DataFrame
    
    Raises:
        DataRejectionError: If validation fails
    """
    logger = get_logger(__name__)
    
    # Check for required columns
    required_cols = ['sample_id', 'metabolite_name', 'concentration', 'stress_type']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        error_msg = f"Missing required columns: {missing}"
        logger.error(f"Data rejection for {source}: {error_msg}")
        raise DataRejectionError(error_msg)
    
    # Check for empty dataframe
    if df.empty:
        error_msg = "Dataset is empty after filtering"
        logger.error(f"Data rejection for {source}: {error_msg}")
        raise DataRejectionError(error_msg)
    
    logger.info(f"Dataset from {source} passed validation: {len(df)} samples")
    return df