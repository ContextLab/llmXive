import os
import re
from typing import Optional, List, Dict, Any, Type, Union
import pandas as pd
import numpy as np
from datetime import datetime

from data.models import StressType, RecoveryMetric, MetabolomicProfile, RecoveryIndex
from data.generator import generate_synthetic_data
from utils.logging import get_logger, DataRejectionError

logger = get_logger(__name__)


class BaseAdapter:
    """Abstract base class for data adapters."""
    def fetch(self, *args, **kwargs) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement fetch()")


class MockAdapter(BaseAdapter):
    """
    Adapter that generates synthetic data for testing and development.
    It calls the synthetic generator and returns a Pandas DataFrame
    that conforms to the dataset.schema.yaml specification.
    """
    def __init__(self, n_samples: int = 100, stress_type: Optional[str] = None):
        """
        Initialize the Mock Adapter.

        Args:
            n_samples: Number of synthetic samples to generate.
            stress_type: Specific stress type to generate, or None for random mix.
        """
        self.n_samples = n_samples
        self.stress_type = stress_type
        logger.info(f"Initialized MockAdapter with n_samples={n_samples}, stress_type={stress_type}")

    def fetch(self) -> pd.DataFrame:
        """
        Generates synthetic data using the generator and returns it as a DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing synthetic metabolomic profiles
                          matching the schema defined in contracts/dataset.schema.yaml.
        """
        try:
            logger.info(f"Generating synthetic data: n={self.n_samples}, stress={self.stress_type}")
            # The generator returns a DataFrame directly
            df = generate_synthetic_data(n_samples=self.n_samples, stress_type=self.stress_type)

            # Validation: Ensure essential columns exist to match schema
            required_cols = [
                'sample_id', 'accession_id', 'stress_type',
                'pre_stress_metabolites', 'post_stress_metabolites',
                'recovery_days', 'recovery_index', 'biomass_change',
                'survival_rate', 'experiment_date', 'source_dataset'
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise DataRejectionError(
                    f"Synthetic data missing required schema columns: {missing_cols}"
                )

            # Ensure types match schema expectations
            if 'recovery_index' in df.columns:
                df['recovery_index'] = df['recovery_index'].clip(0.0, 1.0)
            if 'survival_rate' in df.columns:
                df['survival_rate'] = df['survival_rate'].clip(0.0, 1.0)

            logger.info(f"Successfully generated {len(df)} synthetic samples.")
            return df

        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {str(e)}")
            raise e


class RealAdapter(BaseAdapter):
    """
    Adapter for fetching real data from external sources (NCBI GEO, Zenodo).
    Currently a stub that raises NotImplementedError until full implementation.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "https://example-data-source.org"
        logger.info(f"Initialized RealAdapter with base_url={self.base_url}")

    def fetch(self, accession_id: str) -> pd.DataFrame:
        """
        Fetches real data for a given accession ID.

        Args:
            accession_id: The ID of the dataset to fetch.

        Returns:
            pd.DataFrame: The fetched data.

        Raises:
            NotImplementedError: If the real fetch logic is not yet implemented.
        """
        logger.info(f"Attempting to fetch real data for accession_id: {accession_id}")
        # TODO: Implement actual HTTP request and parsing logic
        raise NotImplementedError("RealAdapter.fetch() is not yet implemented. Use MockAdapter for testing.")


class ExternalDatasetManager:
    """
    Manages ingestion, checksumming, and validation of multiple external datasets
    for Leave-One-Dataset-Out (LODO) validation.
    """
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = data_dir
        logger.info(f"Initialized ExternalDatasetManager with data_dir={data_dir}")

    def ingest_dataset(self, source_path: str) -> pd.DataFrame:
        """
        Ingests a dataset from a file path, validates checksum, and returns DataFrame.

        Args:
            source_path: Path to the dataset file.

        Returns:
            pd.DataFrame: The ingested dataset.
        """
        logger.info(f"Ingesting dataset from {source_path}")
        # Placeholder for checksum and ingestion logic
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Dataset not found at {source_path}")

        # Assume CSV for now, extend for Parquet/other formats
        if source_path.endswith('.csv'):
            df = pd.read_csv(source_path)
        elif source_path.endswith('.parquet'):
            df = pd.read_parquet(source_path)
        else:
            raise ValueError(f"Unsupported file format: {source_path}")

        logger.info(f"Ingested {len(df)} rows from {source_path}")
        return df

    def validate_and_checksum(self, df: pd.DataFrame, expected_hash: Optional[str] = None) -> bool:
        """
        Validates dataset integrity against an expected checksum.

        Args:
            df: The DataFrame to validate.
            expected_hash: Expected MD5/SHA hash.

        Returns:
            bool: True if valid.
        """
        # Placeholder for checksum validation logic
        logger.debug("Validating dataset checksum (placeholder)")
        return True


def get_adapter(
    adapter_type: str,
    n_samples: int = 100,
    stress_type: Optional[str] = None,
    **kwargs
) -> Union[MockAdapter, RealAdapter, ExternalDatasetManager]:
    """
    Factory function to retrieve the appropriate data adapter.

    Args:
        adapter_type: One of 'mock', 'real', or 'external'.
        n_samples: Number of samples for MockAdapter.
        stress_type: Stress type for MockAdapter.
        **kwargs: Additional arguments for specific adapters.

    Returns:
        An instance of the requested adapter.
    """
    if adapter_type.lower() == 'mock':
        return MockAdapter(n_samples=n_samples, stress_type=stress_type)
    elif adapter_type.lower() == 'real':
        return RealAdapter(**kwargs)
    elif adapter_type.lower() == 'external':
        return ExternalDatasetManager(**kwargs)
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")


def filter_by_recovery_time(df: pd.DataFrame, min_days: int = 7) -> pd.DataFrame:
    """
    Filters the DataFrame to include only samples with recovery time >= min_days.

    Args:
        df: Input DataFrame.
        min_days: Minimum recovery days threshold.

    Returns:
        Filtered DataFrame.
    """
    if 'recovery_days' not in df.columns:
        logger.warning("Column 'recovery_days' not found. Returning full DataFrame.")
        return df

    logger.info(f"Filtering for recovery_days >= {min_days}")
    filtered_df = df[df['recovery_days'] >= min_days]
    logger.info(f"Filtered from {len(df)} to {len(filtered_df)} samples")
    return filtered_df


def validate_and_handle_rejection(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """
    Validates the DataFrame against missing value thresholds and handles rejection.

    Args:
        df: Input DataFrame.
        threshold: Maximum allowed fraction of missing values (default 0.1).

    Returns:
        Validated DataFrame.

    Raises:
        DataRejectionError: If missing values exceed threshold.
    """
    missing_ratio = df.isnull().sum() / len(df)
    if (missing_ratio > threshold).any():
        cols_with_issues = missing_ratio[missing_ratio > threshold].index.tolist()
        msg = f"Missing values exceed {threshold} threshold in columns: {cols_with_issues}"
        logger.error(msg)
        raise DataRejectionError(msg)

    logger.info("Validation passed: missing values within threshold.")
    return df