import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Generator
import logging

logger = logging.getLogger(__name__)

def load_csv_chunked(path: str, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Load a CSV file in chunks to optimize memory usage.
    """
    logger.info(f"Loading CSV in chunks: {path}")
    chunks = []
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def optimize_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a DataFrame by downcasting numeric types.
    """
    logger.info("Optimizing memory usage")
    for col in df.columns:
        col_type = df[col].dtype
        if col_type != object:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type).startswith('float'):
                if c_min >= np.finfo(np.float32).min and c_max <= np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
            else:
                if c_min >= np.iinfo(np.int8).min and c_max <= np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min >= np.iinfo(np.int16).min and c_max <= np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                else:
                    df[col] = df[col].astype(np.int64)
        else:
            df[col] = df[col].astype('category')
    logger.info("Memory optimization complete")
    return df
