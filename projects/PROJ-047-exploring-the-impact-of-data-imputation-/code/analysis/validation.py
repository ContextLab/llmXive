"""
Validation utilities for simulation outputs.
Updated T029d to use Pydantic schemas (T053).
"""
import pandas as pd
import logging
from .schemas import validate_simulation_summary

logger = logging.getLogger(__name__)


def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame contains all required columns and valid data types.
    Uses Pydantic schemas for rigorous validation (T053).
    
    Args:
        df: DataFrame to validate (expected from data/results/simulation_summary.csv)
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If validation fails
    """
    try:
        # This will raise ValidationError if validation fails
        validate_simulation_summary(df)
        logger.info("Schema validation passed")
        return True
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        raise
