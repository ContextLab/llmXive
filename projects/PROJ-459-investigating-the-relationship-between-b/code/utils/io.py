"""
I/O utilities for checksums, JSON/Parquet handling, and directory creation.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Union

import pandas as pd


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure the directory for the given path exists.
    Creates parent directories if necessary.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def compute_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def save_parquet(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    compression: str = "snappy",
) -> None:
    """
    Save a pandas DataFrame to a Parquet file.

    Args:
        df: DataFrame to save.
        file_path: Destination path.
        compression: Compression codec ('snappy', 'gzip', 'brotli', None).
    """
    path = ensure_dir(file_path)
    df.to_parquet(path, compression=compression, index=False)


def load_parquet(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Args:
        file_path: Path to the Parquet file.

    Returns:
        Loaded DataFrame.
    """
    return pd.read_parquet(file_path)


def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save data to a JSON file.

    Args:
        data: Python object to serialize (dict, list, etc.).
        file_path: Destination path.
        indent: Indentation level for pretty-printing.
    """
    path = ensure_dir(file_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(file_path: Union[str, Path]) -> Any:
    """
    Load data from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed Python object.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_text(file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    """
    Write a string to a text file.

    Args:
        file_path: Destination path.
        content: String content to write.
        encoding: Text encoding.
    """
    path = ensure_dir(file_path)
    with open(path, "w", encoding=encoding) as f:
        f.write(content)


def read_text(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    Read a text file and return its content.

    Args:
        file_path: Path to the file.
        encoding: Text encoding.

    Returns:
        File content as string.
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()
