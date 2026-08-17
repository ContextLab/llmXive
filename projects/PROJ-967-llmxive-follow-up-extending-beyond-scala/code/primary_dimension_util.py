"""
Shared utility for identifying the primary quality dimension.

Implements the logic required by T014:
1. Primary Rule: Derive from prompt metadata (e.g., prompt_metadata.primary_dimension).
2. Secondary Rule: Use the value of the column 'primary_dimension' if present.
3. Fallback Rule: Default to 'Alignment' if both fail.

This utility is used by T024 to ensure target independence (SC-004).
"""
import logging
import hashlib
from typing import Optional, Dict, Any, List

# The four valid dimensions
VALID_DIMENSIONS = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
FALLBACK_DIMENSION = 'Alignment'

logger = logging.getLogger(__name__)

def _parse_metadata_dimension(prompt_metadata: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Primary Rule: Derive dimension from prompt metadata.
    
    Checks for 'primary_dimension' key in the metadata dict.
    If the metadata is a string or nested in a specific way, attempts to extract.
    """
    if not prompt_metadata:
        return None
    
    if isinstance(prompt_metadata, dict):
        # Check direct key
        if 'primary_dimension' in prompt_metadata:
            val = prompt_metadata['primary_dimension']
            if val in VALID_DIMENSIONS:
                return val
        
        # Check nested 'metadata' key if it exists
        if 'metadata' in prompt_metadata and isinstance(prompt_metadata['metadata'], dict):
            val = prompt_metadata['metadata'].get('primary_dimension')
            if val in VALID_DIMENSIONS:
                return val
    
    return None

def _hash_prompt_to_dimension(prompt_text: str) -> str:
    """
    Deterministic hash of prompt text mapping to one of the four dimensions.
    Used if metadata is missing but we need a deterministic fallback before the final default.
    """
    if not prompt_text:
        return FALLBACK_DIMENSION
    
    # Hash the prompt string
    hash_obj = hashlib.md5(prompt_text.encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Map to index 0-3
    index = hash_int % 4
    return VALID_DIMENSIONS[index]

def identify_primary_dimension(
    row: Dict[str, Any],
    fallback_to_hash: bool = True
) -> str:
    """
    Identify the primary dimension for a single sample row.
    
    Args:
        row: A dictionary representing a single dataset row.
        fallback_to_hash: If True, uses hash of prompt if metadata/col are missing.
                         If False, uses 'Alignment' immediately.
    
    Returns:
        A string from VALID_DIMENSIONS.
    
    Side Effects:
        Logs a warning if the fallback rule is used.
    """
    # 1. Primary Rule: Metadata
    prompt_metadata = row.get('prompt_metadata')
    # Also check if the key is just 'metadata' (common variation)
    if prompt_metadata is None:
        prompt_metadata = row.get('metadata')
        
    dim = _parse_metadata_dimension(prompt_metadata)
    if dim:
        return dim

    # 2. Secondary Rule: Column 'primary_dimension'
    if 'primary_dimension' in row:
        val = row['primary_dimension']
        if isinstance(val, str) and val in VALID_DIMENSIONS:
            return val
        # If column exists but is invalid/null, we treat it as missing and fall through

    # 3. Fallback Rule
    if fallback_to_hash and 'prompt' in row and row['prompt']:
        dim = _hash_prompt_to_dimension(row['prompt'])
        logger.warning(
            f"Primary dimension derived from prompt hash (fallback) for sample. "
            f"Prompt preview: {str(row['prompt'])[:50]}..."
        )
        return dim
    
    # Final Default
    logger.warning(
        f"Primary dimension defaulted to '{FALLBACK_DIMENSION}' (no metadata, no column, no prompt)."
    )
    return FALLBACK_DIMENSION

def process_dataframe_primary_dimensions(df) -> List[str]:
    """
    Apply the identification logic to a pandas DataFrame.
    
    Args:
        df: A pandas DataFrame with the expected columns.
    
    Returns:
        A list of dimension strings corresponding to each row.
    """
    results = []
    for idx, row in df.iterrows():
        dim = identify_primary_dimension(row.to_dict())
        results.append(dim)
    return results
