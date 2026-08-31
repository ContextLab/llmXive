"""
Data Ingestion Module for Plant Stress Resilience Project.

Provides adapters for fetching metabolomic data from various sources
(Mock, Real/NCBI, External/LODO) via a factory pattern.
"""
import os
import re
from typing import Optional, List, Dict, Any, Type, Union
import pandas as pd
import numpy as np
from datetime import datetime

from data.models import MetabolomicProfile, StressType, RecoveryMetric
from utils.logging import get_logger, DataRejectionError

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Base Adapter Class
# ----------------------------------------------------------------------

class BaseAdapter:
    """Abstract base class for data ingestion adapters."""
    
    def fetch(self, access_id: str) -> pd.DataFrame:
        """
        Fetch data for a given access ID.
        
        Args:
            access_id: Identifier for the dataset (e.g., GEO accession, file path).
        
        Returns:
            Pandas DataFrame containing the metabolomic profile.
        
        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement fetch()")

# ----------------------------------------------------------------------
# Mock Adapter
# ----------------------------------------------------------------------

class MockAdapter(BaseAdapter):
    """
    Adapter that generates synthetic data using the project's generator.
    Used for testing and development.
    """
    
    def __init__(self):
        super().__init__()
        # Import here to avoid circular dependencies if generator needs ingest
        from data.generator import generate_synthetic_data
        self._generator = generate_synthetic_data

    def fetch(self, access_id: str) -> pd.DataFrame:
        """
        Generate synthetic data. The access_id is ignored, but we use it 
        to seed the generator for reproducibility if needed.
        """
        logger.info(f"MockAdapter: Generating synthetic data for '{access_id}'")
        
        # Determine stress type based on access_id prefix if possible, else default
        stress = StressType.DROUGHT
        if "drought" in access_id.lower():
            stress = StressType.DROUGHT
        elif "heat" in access_id.lower():
            stress = StressType.HEAT
        elif "salt" in access_id.lower():
            stress = StressType.SALT
        
        # Generate 100 samples by default
        df = self._generator(n_samples=100, stress_type=stress)
        
        logger.info(f"MockAdapter: Generated {len(df)} samples")
        return df

# ----------------------------------------------------------------------
# Real Adapter (NCBI GEO / Zenodo)
# ----------------------------------------------------------------------

class RealAdapter(BaseAdapter):
    """
    Adapter for fetching real data from NCBI GEO or Zenodo.
    Currently implements validation and stub logic as per project status.
    """
    
    def __init__(self):
        super().__init__()
        # In a real implementation, this would initialize API clients
        # e.g., Biopython Entrez, requests session for Zenodo
        self._api_base = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"

    def _validate_accession(self, access_id: str) -> bool:
        """
        Validates the format of a GEO accession ID.
        Examples: GSE12345, GSM123456
        """
        pattern = r"^(GSE|GSM|GPL|GXD)\d+$"
        return bool(re.match(pattern, access_id))

    def fetch(self, access_id: str) -> pd.DataFrame:
        """
        Fetches data from the real source.
        
        Currently raises NotImplementedError as the full parsing logic 
        for XML/JSON responses is under active development (T012).
        """
        if not self._validate_accession(access_id):
            raise ValueError(f"Invalid accession ID format: {access_id}")
        
        logger.info(f"RealAdapter: Attempting to fetch real data for '{access_id}'")
        
        # TODO: Implement actual API call and XML/JSON parsing
        # This is where T012 logic would reside
        raise NotImplementedError(
            "RealAdapter.fetch is not fully implemented. "
            "Please ensure T012 (NCBI GEO parsing) is completed before using this adapter with real data."
        )

# ----------------------------------------------------------------------
# External Dataset Manager (LODO Support)
# ----------------------------------------------------------------------

class ExternalDatasetManager(BaseAdapter):
    """
    Adapter for managing multiple independent external datasets for LODO validation.
    Handles ingestion, checksumming, and validation of local files or remote archives.
    """
    
    def __init__(self, data_dir: str = "data/raw"):
        super().__init__()
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        self._datasets: Dict[str, pd.DataFrame] = {}

    def _validate_checksum(self, file_path: str, expected_md5: Optional[str] = None) -> bool:
        """
        Validates the MD5 checksum of a file if expected_md5 is provided.
        Returns True if valid or if no checksum provided.
        """
        if not expected_md5:
            return True
        
        import hashlib
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        calculated = hash_md5.hexdigest()
        if calculated != expected_md5:
            logger.error(f"Checksum mismatch for {file_path}: {calculated} != {expected_md5}")
            return False
        return True

    def _load_local_parquet(self, file_path: str) -> pd.DataFrame:
        """Loads a local Parquet file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        logger.info(f"Loading local dataset from {file_path}")
        return pd.read_parquet(file_path)

    def fetch(self, access_id: str) -> pd.DataFrame:
        """
        Fetches a dataset by access_id.
        
        The access_id can be:
        - A local file path (absolute or relative to data_dir)
        - A registered dataset key (if pre-loaded)
        
        For remote URLs, this would trigger a download (not fully implemented yet).
        """
        if access_id in self._datasets:
            logger.info(f"Returning cached dataset for {access_id}")
            return self._datasets[access_id]

        # Check if it's a local file path
        full_path = access_id
        if not os.path.isabs(access_id):
            full_path = os.path.join(self.data_dir, access_id)
        
        if os.path.exists(full_path):
            df = self._load_local_parquet(full_path)
            # Basic validation
            if df.empty:
                raise DataRejectionError(f"Dataset {access_id} is empty")
            
            self._datasets[access_id] = df
            logger.info(f"Successfully loaded external dataset: {access_id} ({len(df)} rows)")
            return df

        # If not local and not cached, it might be a remote ID
        # For now, we raise an error requiring T009.1 implementation for remote fetching
        raise NotImplementedError(
            f"Remote fetching for '{access_id}' is not implemented. "
            "Please ensure T009.1 (ExternalDatasetManager remote logic) is completed."
        )

# ----------------------------------------------------------------------
# Factory Pattern
# ----------------------------------------------------------------------

ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {
    "mock": MockAdapter,
    "real": RealAdapter,
    "external": ExternalDatasetManager
}

def get_adapter(adapter_type: str) -> BaseAdapter:
    """
    Factory function to instantiate the appropriate adapter.
    
    Args:
        adapter_type: One of 'mock', 'real', 'external'.
    
    Returns:
        An instance of the requested adapter.
    
    Raises:
        ValueError: If the adapter type is unknown.
    """
    adapter_type = adapter_type.lower()
    if adapter_type not in ADAPTER_REGISTRY:
        raise ValueError(
            f"Unknown adapter type: {adapter_type}. "
            f"Available types: {list(ADAPTER_REGISTRY.keys())}"
        )
    
    logger.info(f"Instantiating adapter: {adapter_type}")
    return ADAPTER_REGISTRY[adapter_type]()

# ----------------------------------------------------------------------
# Helper Functions (Existing API Surface)
# ----------------------------------------------------------------------

def filter_by_recovery_time(df: pd.DataFrame, min_days: int = 7) -> pd.DataFrame:
    """
    Filters the DataFrame for samples with recovery time >= min_days.
    
    Args:
        df: Input DataFrame with a 'recovery_days' column.
        min_days: Minimum recovery days required.
    
    Returns:
        Filtered DataFrame.
    """
    if 'recovery_days' not in df.columns:
        logger.warning("Column 'recovery_days' not found. Returning full DataFrame.")
        return df
    
    mask = df['recovery_days'] >= min_days
    filtered = df[mask]
    logger.info(f"Filtered by recovery time >= {min_days}: {len(filtered)} rows remaining")
    return filtered

def validate_and_handle_rejection(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """
    Validates the DataFrame against missing data thresholds.
    
    Args:
        df: Input DataFrame.
        threshold: Maximum allowed fraction of missing values (default 0.1).
    
    Returns:
        The DataFrame if valid.
    
    Raises:
        DataRejectionError: If missing data exceeds threshold.
    """
    if 'recovery_days' not in df.columns:
        # If we can't even check basic metrics, reject
        raise DataRejectionError("Missing 'recovery_days' column. Cannot validate dataset.")
    
    # Calculate missing percentage per column
    missing_pct = df.isnull().mean()
    max_missing = missing_pct.max()
    
    if max_missing > threshold:
        worst_col = missing_pct.idxmax()
        raise DataRejectionError(
            f"Dataset rejected: Missing data exceeds {threshold*100}% "
            f"(Max: {max_missing:.2%} in column '{worst_col}')"
        )
    
    logger.info(f"Validation passed: Max missing {max_missing:.2%}")
    return df