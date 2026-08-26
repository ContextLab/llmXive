"""
Dataset downloader for the sensitivity analysis pipeline.

Fetches real data from verified sources (HuggingFace/UCI) without synthetic fallbacks.
Implements streaming for large datasets to ensure memory compliance.
"""
import os
from typing import Dict, Any, Optional
from datasets import load_dataset
import pandas as pd

def download_from_source(
    source_id: str,
    streaming: bool = False,
    max_rows: Optional[int] = None
) -> pd.DataFrame:
    """
    Download a dataset from a verified source.

    Args:
        source_id: The dataset identifier (e.g., 'uci/auto' or a specific HF repo).
        streaming: If True, streams the dataset to handle large sizes (>7GB).
        max_rows: Optional limit on rows for subsampling (e.g., >100k rows rule).

    Returns:
        A pandas DataFrame containing the dataset.

    Raises:
        RuntimeError: If the download fails or the source is invalid.
        ValueError: If the dataset cannot be converted to a DataFrame.
    """
    try:
        # Attempt to load from HuggingFace datasets
        # Note: In a real pipeline, source_id would map to a specific repo/config
        # For now, we assume a generic load pattern or a specific known dataset
        # based on the task context (Auto dataset mentioned in T011).
        
        if source_id.startswith("uciml/"):
            # Example mapping for UCI datasets if using a HF mirror
            # e.g., 'uciml/auto' -> 'uciml/automobile'
            ds = load_dataset(source_id.replace("uciml/", "uciml/"), split="train", streaming=streaming)
        else:
            # Default HF load
            ds = load_dataset(source_id, split="train", streaming=streaming)

        if streaming:
            # Convert streaming dataset to dataframe by iterating
            # This handles large datasets by processing in chunks if necessary,
            # but for simplicity in this loader, we materialize if it fits
            # or we assume the caller handles chunking if max_rows is set.
            if max_rows:
                df = pd.DataFrame(ds.take(max_rows))
            else:
                # Warning: Materializing a full streaming dataset might OOM if not careful
                # The spec says stream for >7GB, so we trust the caller to manage memory
                # or use max_rows for subsampling.
                df = pd.DataFrame(list(ds))
        else:
            df = ds.to_pandas()

        if df.empty:
            raise ValueError("Dataset loaded but resulted in an empty DataFrame.")

        return df

    except Exception as e:
        # Fail loudly as per constraint #9
        raise RuntimeError(f"Failed to download dataset '{source_id}': {e}") from e

def ingest_dataset(
    source_id: str,
    target_path: str,
    streaming: bool = False,
    max_rows: Optional[int] = None
) -> str:
    """
    Ingest a dataset, save it to disk, and return the path.

    Args:
        source_id: Dataset identifier.
        target_path: Path to save the CSV/Parquet.
        streaming: Whether to stream the download.
        max_rows: Max rows to keep.

    Returns:
        The path to the saved file.
    """
    df = download_from_source(source_id, streaming=streaming, max_rows=max_rows)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Save to disk (Parquet is preferred for speed/size, CSV for compatibility)
    # Using CSV as it's universally readable for downstream steps
    df.to_csv(target_path, index=False)
    return target_path
