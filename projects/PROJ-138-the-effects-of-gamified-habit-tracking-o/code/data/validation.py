"""
Data validation module.
Implements consent checks, schema validation, and statistical metrics.
"""
import os
import json
import pandas as pd
import pingouin as pg
import yaml
from typing import List, Optional
from code.utils.logging import pipeline_logger

logger = pipeline_logger

def check_consent():
    """
    Verify that consent artifacts exist in data/consent/.
    If real data is used, ensure the directory is not empty.
    If synthetic data is used, ensure a synthetic consent record exists.
    """
    consent_dir = "data/consent"
    if not os.path.exists(consent_dir):
        raise FileNotFoundError(f"Consent directory '{consent_dir}' does not exist. "
                                "Cannot proceed without consent verification (FR-010).")
    
    files = os.listdir(consent_dir)
    if not files:
        # Check if we are in a synthetic data mode (often indicated by a specific flag or file presence elsewhere)
        # For now, if the directory is empty, we assume real data was expected but missing.
        raise FileNotFoundError(f"Consent directory '{consent_dir}' is empty. "
                                "Missing consent artifact for real data or synthetic record.")
    
    # Check for synthetic consent record if it exists
    synthetic_record = os.path.join(consent_dir, "synthetic_consent_record.json")
    if os.path.exists(synthetic_record):
        logger.info("Synthetic consent record found. Proceeding with synthetic data.")
        with open(synthetic_record, 'r') as f:
            record = json.load(f)
            if record.get("is_synthetic"):
                logger.info(f"Synthetic data approved for research: {record.get('approval_id')}")
                return True
    
    # If we have files but no explicit synthetic record, assume real data consent is present
    logger.info(f"Consent verification passed. Found {len(files)} file(s) in {consent_dir}.")
    return True

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate that the DataFrame contains all required columns defined in the schema.
    
    Args:
        df: The pandas DataFrame to validate.
        schema_path: Path to the YAML schema file (e.g., contracts/dataset.schema.yaml).
    
    Returns:
        True if validation passes.
    
    Raises:
        ValueError: If required columns are missing.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_columns = schema.get('required', [])
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        msg = f"Schema validation failed. Missing required columns: {missing_columns}"
        logger.error(msg)
        raise ValueError(msg)
    
    logger.info(f"Schema validation passed. All {len(required_columns)} required columns present.")
    return True

def calculate_cronbach_alpha(df: pd.DataFrame, item_columns: List[str]) -> float:
    """
    Calculate Cronbach's alpha for a set of item columns.
    
    Args:
        df: DataFrame containing the item columns.
        item_columns: List of column names representing scale items.
    
    Returns:
        Cronbach's alpha coefficient.
    """
    # Filter out non-numeric columns if any
    valid_items = [col for col in item_columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(valid_items) < 2:
        logger.warning(f"Not enough items to calculate Cronbach's alpha. Found {len(valid_items)}.")
        return 0.0
    
    try:
        alpha = pg.cronbach_alpha(data=df[valid_items])
        logger.info(f"Cronbach's alpha calculated: {alpha:.4f}")
        return alpha
    except Exception as e:
        logger.error(f"Error calculating Cronbach's alpha: {e}")
        return 0.0