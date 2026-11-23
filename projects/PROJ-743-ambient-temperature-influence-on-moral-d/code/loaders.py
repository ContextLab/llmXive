"""
Data loading utilities including chunked parquet support.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Generator

log = logging.getLogger(__name__)

def load_parquet_as_df(path: str | Path) -> pd.DataFrame:
    """
    Load a parquet file into a pandas DataFrame.
    
    Args:
        path: Path to the parquet file.
    Returns:
        The loaded DataFrame.
    """
    try:
        return pd.read_parquet(path)
    except Exception as e:
        log.error(f"Failed to load parquet file {path}: {e}")
        raise

def load_parquet_chunked(path: str | Path, chunk_size: int = 100000) -> Generator[pd.DataFrame, None, None]:
    """
    Stream a parquet file in chunks using pyarrow.
    
    Args:
        path: Path to the parquet file.
        chunk_size: Target number of rows per chunk.
    Yields:
        Pandas DataFrames containing chunks of the dataset.
    """
    import pyarrow.parquet as pq
    try:
        parquet_file = pq.ParquetFile(path)
        # Parquet files are organized by row groups. 
        # We yield row groups as the natural chunking mechanism.
        for i in range(parquet_file.num_row_groups):
            yield parquet_file.read_row_group(i).to_pandas()
    except Exception as e:
        log.error(f"Failed to load parquet file chunked {path}: {e}")
        raise
