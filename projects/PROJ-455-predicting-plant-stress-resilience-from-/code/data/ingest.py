import os
import re
from typing import Optional, List
import pandas as pd
import numpy as np
from data.models import MetabolomicProfile, StressType
from utils.logging import get_logger, DataRejectionError

logger = get_logger(__name__)


class MockAdapter:
    """Adapter that generates synthetic data for testing."""

    def fetch(self, accession_id: str) -> pd.DataFrame:
        """Generate synthetic metabolomic data matching the schema."""
        logger.info(f"Fetching synthetic data for accession: {accession_id}")
        # Implementation from T008/T007 context
        return pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'stress_type': [StressType.DROUGHT.value, StressType.DROUGHT.value, StressType.HEAT.value],
            'recovery_days': [5.0, 10.0, 15.0],
            'biomass_change': [-0.1, 0.2, 0.5],
            'metabolite_1': [100.0, 120.0, 130.0],
            'metabolite_2': [50.0, 60.0, 70.0],
            'timestamp': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])
        })


class RealAdapter:
    """Adapter for fetching real data from external sources (NCBI GEO, Zenodo)."""

    def fetch(self, accession_id: str) -> pd.DataFrame:
        """
        Fetch real metabolomic data for a given accession ID.
        Parses XML/JSON responses into a MetabolomicProfile DataFrame.
        """
        logger.info(f"Fetching real data for accession: {accession_id}")
        
        # Validate accession ID format (basic check)
        if not re.match(r'^[A-Z0-9]+$', accession_id):
            raise ValueError(f"Invalid accession ID format: {accession_id}")
        
        # Placeholder for actual implementation (T012 context)
        # In a real scenario, this would call NCBI GEO or Zenodo APIs
        # For now, raise NotImplementedError as per task T009
        raise NotImplementedError("RealAdapter.fetch() is not yet implemented for external sources.")


def filter_by_recovery_time(df: pd.DataFrame, min_days: float = 7.0) -> pd.DataFrame:
    """
    Filter the dataset to include only samples with recovery time >= min_days.
    
    This function implements the requirement to filter datasets for samples
    with post-stress recovery metrics >= specified days (default 7).
    
    Args:
        df: Input DataFrame containing metabolomic profiles with a 'recovery_days' column.
        min_days: Minimum recovery time in days (default 7.0).
        
    Returns:
        Filtered DataFrame containing only samples meeting the recovery time threshold.
        
    Raises:
        DataRejectionError: If the required 'recovery_days' column is missing.
        ValueError: If min_days is negative.
    """
    if min_days < 0:
        raise ValueError("min_days cannot be negative")
        
    if 'recovery_days' not in df.columns:
        raise DataRejectionError(
            "Missing required column 'recovery_days' for recovery time filtering."
        )
    
    initial_count = len(df)
    filtered_df = df[df['recovery_days'] >= min_days].copy()
    filtered_count = len(filtered_df)
    
    logger.info(
        f"Filtered by recovery time >= {min_days} days: "
        f"{initial_count} -> {filtered_count} samples ({filtered_count/initial_count:.1%} retained)"
    )
    
    if filtered_count == 0:
        logger.warning("No samples met the recovery time threshold. Dataset may be empty.")
        
    return filtered_df


def validate_and_handle_rejection(df: pd.DataFrame, validation_func, validation_name: str) -> pd.DataFrame:
    """
    Wrapper function to execute a validation function, catch DataRejectionError,
    and log specific rejection reasons.
    
    This function centralizes error handling for dataset validation scenarios,
    ensuring that rejection reasons (e.g., 'Missing >10%') are logged consistently
    using the project's logging infrastructure.
    
    Args:
        df: The DataFrame to validate.
        validation_func: A callable that performs validation and raises DataRejectionError on failure.
        validation_name: A descriptive name for the validation step (e.g., 'missing_threshold').
        
    Returns:
        The validated DataFrame if successful.
        
    Raises:
        DataRejectionError: Re-raises the exception after logging the rejection reason.
    """
    try:
        logger.info(f"Starting validation: {validation_name}")
        result = validation_func(df)
        logger.info(f"Validation passed: {validation_name}")
        return result
    except DataRejectionError as e:
        reason = str(e)
        logger.error(f"Dataset rejected during {validation_name}: {reason}")
        # Re-raise to allow upstream handling
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {validation_name}: {str(e)}")
        raise
