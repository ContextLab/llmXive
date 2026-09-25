import hashlib
import json
import logging
import inspect
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

def derive_primary_dimension_from_metadata(prompt_text: str) -> int:
    """
    Derive primary dimension index from prompt_text.
    Rule: int(hashlib.sha256(prompt_text.encode()).hexdigest(), 16) % 4
    """
    if prompt_text is None or not isinstance(prompt_text, str):
        return None
    hash_hex = hashlib.sha256(prompt_text.encode()).hexdigest()
    hash_int = int(hash_hex, 16)
    return hash_int % 4

def get_derivation_rule_hash(rule_string: str) -> str:
    """
    Compute SHA-256 hash of the derivation rule string for the lineage report.
    """
    return hashlib.sha256(rule_string.encode()).hexdigest()

def process_dataframe_primary_dimensions(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Apply derive_primary_dimension_from_metadata to the 'prompt_text' column
    and add 'primary_dimension' column to the dataframe.
    """
    if "prompt_text" not in df.columns:
        logger.error("Column 'prompt_text' not found in dataframe.")
        return df

    logger.info("Applying primary dimension derivation to prompt_text column...")
    
    # Use apply for clarity, vectorization is possible but apply is safer for mixed types
    df["primary_dimension"] = df["prompt_text"].apply(derive_primary_dimension_from_metadata)
    
    # Check for failures (None values)
    null_count = df["primary_dimension"].isna().sum()
    if null_count > 0:
        logger.warning(f"Found {null_count} samples with null primary_dimension.")
    
    return df
