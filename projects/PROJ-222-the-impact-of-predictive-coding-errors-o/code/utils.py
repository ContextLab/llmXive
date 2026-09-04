import pandas as pd
import logging
from pathlib import Path
from typing import Iterator, Optional, Callable, Any, List, Dict
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_dataset_chunked(file_path: str, chunksize: int = 10000) -> Iterator[pd.DataFrame]:
    """Load a dataset in chunks."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    logger.info(f"Loading dataset in chunks from {file_path}...")
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        yield chunk

def compute_chunked_statistics(chunks: Iterator[pd.DataFrame], func: Callable[[pd.DataFrame], Any]) -> Any:
    """Compute statistics over chunks of a dataset."""
    results = []
    for chunk in chunks:
        result = func(chunk)
        results.append(result)
    return results
