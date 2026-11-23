import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import pandas as pd
import numpy as np
import torch

from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def generate_run_id() -> str:
    """
    Generate a deterministic run_id based on current timestamp and a random salt.
    This ensures unique identifiers for each run while allowing reproducibility
    if the seed is fixed in the calling context.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    salt = hashlib.sha256(os.urandom(16)).hexdigest()[:8]
    return f"run_{timestamp}_{salt}"

def serialize_embeddings_to_parquet(
    embeddings: List[Dict[str, Any]],
    output_path: str,
    run_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Serialize a list of embedding dictionaries to a Parquet file.

    Each embedding dictionary must contain:
    - dataset_id: str
    - sample_id: str (or index)
    - embedding: np.ndarray or list
    - modality: str ('image' or 'text')
    - Optional: model_name, seed, timestamp, etc.

    The output Parquet file will include:
    - run_id: str (added to every row)
    - dataset_id: str
    - sample_id: str
    - embedding: list[float] (flattened)
    - modality: str
    - Any additional metadata fields provided

    Args:
        embeddings: List of embedding dictionaries.
        output_path: Path to the output Parquet file.
        run_id: Unique identifier for this run.
        metadata: Optional dictionary of global metadata to include.
    """
    if not embeddings:
        log_warning("No embeddings to serialize. Creating empty Parquet file with schema.")
        # Create an empty DataFrame with the expected schema
        df = pd.DataFrame({
            'run_id': pd.Series([], dtype=str),
            'dataset_id': pd.Series([], dtype=str),
            'sample_id': pd.Series([], dtype=str),
            'embedding': pd.Series([], dtype='object'),
            'modality': pd.Series([], dtype=str)
        })
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_file, index=False)
        log_info(f"Created empty Parquet file at {output_path}")
        return

    # Prepare data rows
    rows = []
    for emb_dict in embeddings:
        row = {
            'run_id': run_id,
            'dataset_id': emb_dict.get('dataset_id', 'unknown'),
            'sample_id': emb_dict.get('sample_id', 'unknown'),
            'embedding': emb_dict['embedding'].tolist() if isinstance(emb_dict['embedding'], np.ndarray) else emb_dict['embedding'],
            'modality': emb_dict.get('modality', 'unknown'),
        }
        
        # Add optional fields
        if 'model_name' in emb_dict:
            row['model_name'] = emb_dict['model_name']
        if 'seed' in emb_dict:
            row['seed'] = emb_dict['seed']
        if 'timestamp' in emb_dict:
            row['timestamp'] = emb_dict['timestamp']
        
        rows.append(row)

    df = pd.DataFrame(rows)

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to Parquet
    try:
        df.to_parquet(output_file, index=False)
        log_info(f"Successfully serialized {len(rows)} embeddings to {output_path}")
        
        # Log schema summary
        log_info(f"Output schema: {df.dtypes.to_dict()}")
        log_info(f"Sample row: {df.iloc[0].to_dict()}")
        
    except Exception as e:
        log_error(f"Failed to serialize embeddings to {output_path}: {str(e)}")
        raise

def load_embeddings_from_parquet(
    input_path: str,
    filter_by_run_id: Optional[str] = None,
    filter_by_dataset_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load embeddings from a Parquet file.

    Args:
        input_path: Path to the input Parquet file.
        filter_by_run_id: Optional filter to only include rows with this run_id.
        filter_by_dataset_id: Optional filter to only include rows with this dataset_id.

    Returns:
        List of embedding dictionaries with the same structure as serialize_embeddings_to_parquet.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Embeddings file not found: {input_path}")

    df = pd.read_parquet(input_path)

    # Apply filters
    if filter_by_run_id:
        df = df[df['run_id'] == filter_by_run_id]
    if filter_by_dataset_id:
        df = df[df['dataset_id'] == filter_by_dataset_id]

    embeddings = []
    for _, row in df.iterrows():
        emb_dict = {
            'dataset_id': row['dataset_id'],
            'sample_id': row['sample_id'],
            'embedding': np.array(row['embedding']),
            'modality': row['modality'],
            'run_id': row['run_id'],
        }
        
        # Add optional fields if present
        if 'model_name' in row:
            emb_dict['model_name'] = row['model_name']
        if 'seed' in row:
            emb_dict['seed'] = row['seed']
        if 'timestamp' in row:
            emb_dict['timestamp'] = row['timestamp']
        
        embeddings.append(emb_dict)

    log_info(f"Loaded {len(embeddings)} embeddings from {input_path}")
    return embeddings
