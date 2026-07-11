"""
Serialization module for embedding outputs.
Handles writing embeddings and metadata to Parquet format.
"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from utils.logging import get_logger, log_info, log_warning, log_error
from config import get_output_path

logger = get_logger(__name__)


def serialize_embeddings_to_parquet(
    embeddings: List[Dict[str, Any]],
    output_path: Union[str, Path],
    run_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Serialize a list of embedding records to a Parquet file.

    Args:
        embeddings: List of dicts containing 'dataset_id', 'record_id',
                    'embedding_vector', 'modality', and other metadata.
        output_path: Path to the output Parquet file.
        run_id: Unique identifier for this run (included in metadata).
        metadata: Optional additional metadata to store alongside embeddings.
    """
    if not embeddings:
        log_warning("No embeddings provided for serialization. Creating empty file.")
        # Create an empty Parquet file with the expected schema
        schema = pa.schema([
            ('run_id', pa.string()),
            ('dataset_id', pa.string()),
            ('record_id', pa.string()),
            ('modality', pa.string()),
            ('embedding_vector', pa.list_(pa.float32())),
            ('timestamp', pa.string()),
            ('checksum', pa.string())
        ])
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table(schema=schema), str(output_path))
        log_info(f"Created empty Parquet file at {output_path}")
        return

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data for DataFrame
    data = []
    for record in embeddings:
        # Convert numpy arrays to lists for JSON/Parquet compatibility
        embedding_vec = record.get('embedding_vector')
        if isinstance(embedding_vec, np.ndarray):
            embedding_vec = embedding_vec.tolist()
        elif embedding_vec is None:
            embedding_vec = []

        # Compute checksum for data integrity
        checksum_data = json.dumps({
            'dataset_id': record.get('dataset_id', ''),
            'record_id': record.get('record_id', ''),
            'embedding_vector': embedding_vec
        }, sort_keys=True)
        checksum = hashlib.sha256(checksum_data.encode('utf-8')).hexdigest()[:16]

        data.append({
            'run_id': run_id,
            'dataset_id': record.get('dataset_id', ''),
            'record_id': record.get('record_id', ''),
            'modality': record.get('modality', 'unknown'),
            'embedding_vector': embedding_vec,
            'timestamp': datetime.utcnow().isoformat(),
            'checksum': checksum
        })

    # Create DataFrame
    df = pd.DataFrame(data)

    # Ensure embedding_vector column is list type for PyArrow
    # PyArrow handles list columns well, but we ensure consistency
    if 'embedding_vector' in df.columns:
        df['embedding_vector'] = df['embedding_vector'].apply(lambda x: x if isinstance(x, list) else [])

    try:
        # Write to Parquet using PyArrow for better compatibility
        table = pa.Table.from_pandas(df)
        pq.write_table(table, str(output_path))
        log_info(f"Successfully serialized {len(embeddings)} embeddings to {output_path}")
    except Exception as e:
        log_error(f"Failed to serialize embeddings to Parquet: {e}")
        raise


def load_embeddings_from_parquet(
    input_path: Union[str, Path]
) -> pd.DataFrame:
    """
    Load embeddings from a Parquet file into a Pandas DataFrame.

    Args:
        input_path: Path to the input Parquet file.

    Returns:
        DataFrame containing the embeddings.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {input_path}")

    try:
        df = pd.read_parquet(str(input_path))
        log_info(f"Loaded {len(df)} embeddings from {input_path}")
        return df
    except Exception as e:
        log_error(f"Failed to load embeddings from Parquet: {e}")
        raise


def generate_run_id() -> str:
    """
    Generate a unique run ID based on timestamp and a random component.

    Returns:
        A unique run ID string.
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    random_part = hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]
    return f"{timestamp}_{random_part}"
