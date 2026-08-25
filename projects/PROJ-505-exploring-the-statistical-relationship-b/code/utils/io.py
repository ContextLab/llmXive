import hashlib
import os
from pathlib import Path
from typing import Optional
import pandas as pd
import pyarrow.parquet as pq

def compute_md5(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_md5(file_path: Path, expected_md5: str) -> bool:
    """Verify file MD5 against expected value."""
    return compute_md5(file_path) == expected_md5

def load_parquet(file_path: Path) -> pd.DataFrame:
    """Load a Parquet file into a DataFrame."""
    return pq.read_table(file_path).to_pandas()

def save_parquet(df: pd.DataFrame, file_path: Path) -> None:
    """Save a DataFrame to a Parquet file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, index=False)
