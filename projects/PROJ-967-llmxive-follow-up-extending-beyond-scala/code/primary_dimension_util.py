import hashlib
import json
import logging
import inspect
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

def derive_primary_dimension_from_metadata(row: pd.Series, logger: logging.Logger) -> Optional[str]:
    """
    Derive primary_dimension from prompt metadata.
    Rule: If 'prompt_metadata' exists and has 'primary_dimension', use it.
    Else, use a deterministic hash of the prompt text.
    """
    # Check for explicit metadata
    if 'prompt_metadata' in row.index and isinstance(row['prompt_metadata'], dict):
        if 'primary_dimension' in row['prompt_metadata']:
            return row['prompt_metadata']['primary_dimension']

    # Fallback: Deterministic hash of prompt
    prompt = str(row.get('prompt', ''))
    if not prompt:
        return None

    # Hash to one of 4 dimensions
    h = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    idx = int(h, 16) % 4
    dims = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    return dims[idx]

def get_derivation_rule_hash() -> str:
    """
    Return the SHA-256 hash of the source code of derive_primary_dimension_from_metadata.
    """
    source = inspect.getsource(derive_primary_dimension_from_metadata)
    return hashlib.sha256(source.encode('utf-8')).hexdigest()

def process_dataframe_primary_dimensions(df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Process the dataframe to ensure 'primary_dimension' is derived from metadata.
    Exclude samples where derivation fails (returns None).
    Returns (processed_df, exclusions_list).
    """
    exclusions = []
    derivation_hash = get_derivation_rule_hash()

    logger.info(f"Derivation rule hash: {derivation_hash}")

    derived_dims = []
    for idx, row in df.iterrows():
        dim = derive_primary_dimension_from_metadata(row, logger)
        if dim is None:
            exclusions.append({
                'sample_id': idx,
                'reason': 'missing_metadata',
                'timestamp': pd.Timestamp.now().isoformat()
            })
        derived_dims.append(dim)

    df['primary_dimension'] = derived_dims

    # Drop rows where primary_dimension is None
    valid_mask = df['primary_dimension'].notna()
    excluded_df = df[~valid_mask]
    df = df[valid_mask].copy()

    logger.info(f"Derived primary_dimension for {len(df)} samples. Excluded {len(excluded_df)}.")

    return df, exclusions