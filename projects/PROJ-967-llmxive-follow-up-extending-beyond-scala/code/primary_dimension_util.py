"""
Primary Dimension Identification Utility.

This module implements the logic to identify the primary quality dimension
for a sample based on metadata rules, as required by T014.
"""
import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple

# Define the valid dimensions as per the schema
VALID_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

logger = logging.getLogger(__name__)


def identify_primary_dimension(
    sample: Dict[str, Any],
    metadata_key: str = "prompt_metadata"
) -> Optional[str]:
    """
    Derive the primary_dimension from prompt metadata using a fixed schema rule.

    Rule 1: Check for explicit metadata field (e.g., prompt_metadata.primary_dimension).
    Rule 2: If metadata rule yields no result, return None (Exclusion Rule).
            Do NOT use a fallback column value or hash the prompt text unless
            explicitly configured in the schema (currently not configured).

    Args:
        sample: A dictionary representing a single row from the dataset.
        metadata_key: The key in the sample dict where metadata is stored.

    Returns:
        The primary dimension string if found, or None if the rule yields no result.
    """
    # Attempt to extract from metadata
    metadata = sample.get(metadata_key)
    
    if not isinstance(metadata, dict):
        # Metadata structure is invalid or missing
        return None

    # Check for explicit primary_dimension in metadata
    dim = metadata.get("primary_dimension")
    
    if dim is not None and isinstance(dim, str):
        # Normalize to Title Case to match schema expectations
        dim_normalized = dim.title()
        if dim_normalized in VALID_DIMENSIONS:
            return dim_normalized
        else:
            # Value exists but is not a valid dimension
            logger.warning(f"Invalid dimension value '{dim}' found in metadata. Excluding sample.")
            return None

    # If the metadata rule yields no result, EXCLUDE the sample.
    # Do not fall back to hashing or other heuristics.
    return None


def process_dataframe_primary_dimensions(
    df: Any,
    metadata_key: str = "prompt_metadata"
) -> Tuple[Any, List[int]]:
    """
    Process a Pandas DataFrame to derive and assign primary_dimension.
    
    This function applies the identification logic to every row.
    It returns a new DataFrame (or modified copy) with the 'primary_dimension'
    column populated, and a list of indices for samples that were excluded
    because they failed the derivation rule.

    Args:
        df: A Pandas DataFrame containing the dataset.
        metadata_key: The column name containing the metadata dictionary.

    Returns:
        Tuple of (processed_df, excluded_indices).
        processed_df: The dataframe with 'primary_dimension' added.
        excluded_indices: List of row indices where primary_dimension could not be derived.
    """
    import pandas as pd

    if "primary_dimension" in df.columns:
        logger.warning("Column 'primary_dimension' already exists. Overwriting based on metadata rule.")

    derived_dims = []
    excluded_indices = []

    for idx, row in df.iterrows():
        dim = identify_primary_dimension(row, metadata_key=metadata_key)
        if dim is None:
            derived_dims.append(None)
            excluded_indices.append(idx)
            logger.debug(f"Sample at index {idx} excluded: No valid primary_dimension derived from metadata.")
        else:
            derived_dims.append(dim)

    # Create a copy to avoid SettingWithCopyWarning
    df_out = df.copy()
    df_out["primary_dimension"] = derived_dims

    logger.info(f"Processed {len(df)} samples. Excluded {len(excluded_indices)} samples due to missing primary dimension.")

    return df_out, excluded_indices
