"""
I/O utilities for llmXive PROJ-011.
Robust file loading and saving with error handling.
"""
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class IOLoadError(Exception):
    """Exception raised when loading data fails."""
    pass


class IOSaveError(Exception):
    """Exception raised when saving data fails."""
    pass


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        The Path object for the directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_exists(file_path: Union[str, Path]) -> bool:
    """
    Check if a file exists.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        True if the file exists, False otherwise.
    """
    return Path(file_path).exists()


def load_csv(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    
    Args:
        file_path: Path to the CSV file.
        **kwargs: Additional arguments passed to pd.read_csv.
        
    Returns:
        DataFrame containing the CSV data.
        
    Raises:
        IOLoadError: If the file cannot be loaded.
    """
    try:
        return pd.read_csv(file_path, **kwargs)
    except Exception as e:
        raise IOLoadError(f"Failed to load CSV {file_path}: {e}")


def save_csv(df: pd.DataFrame, file_path: Union[str, Path], **kwargs) -> None:
    """
    Save a pandas DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save.
        file_path: Path to save the CSV file.
        **kwargs: Additional arguments passed to df.to_csv.
        
    Raises:
        IOSaveError: If the file cannot be saved.
    """
    try:
        ensure_dir(Path(file_path).parent)
        df.to_csv(file_path, **kwargs)
    except Exception as e:
        raise IOSaveError(f"Failed to save CSV {file_path}: {e}")


def load_json(file_path: Union[str, Path], **kwargs) -> Union[Dict, List]:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        **kwargs: Additional arguments passed to json.load.
        
    Returns:
        Parsed JSON data (dict or list).
        
    Raises:
        IOLoadError: If the file cannot be loaded.
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise IOLoadError(f"Failed to load JSON {file_path}: {e}")


def save_json(data: Union[Dict, List], file_path: Union[str, Path], **kwargs) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save (dict or list).
        file_path: Path to save the JSON file.
        **kwargs: Additional arguments passed to json.dump.
        
    Raises:
        IOSaveError: If the file cannot be saved.
    """
    try:
        ensure_dir(Path(file_path).parent)
        with open(file_path, "w") as f:
            json.dump(data, f, **kwargs)
    except Exception as e:
        raise IOSaveError(f"Failed to save JSON {file_path}: {e}")


def load_jsonl(file_path: Union[str, Path]) -> List[Dict]:
    """
    Load a JSON Lines file (one JSON object per line).
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of dictionaries, one per line.
        
    Raises:
        IOLoadError: If the file cannot be loaded.
    """
    try:
        data = []
        with open(file_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise IOLoadError(f"Invalid JSON on line {line_num} in {file_path}: {e}")
        return data
    except FileNotFoundError:
        raise IOLoadError(f"JSONL file not found: {file_path}")
    except Exception as e:
        raise IOLoadError(f"Failed to load JSONL {file_path}: {e}")


def save_jsonl(data: List[Dict], file_path: Union[str, Path], **kwargs) -> None:
    """
    Save a list of dictionaries to a JSON Lines file.
    
    Args:
        data: List of dictionaries to save.
        file_path: Path to save the JSONL file.
        **kwargs: Additional arguments passed to json.dump.
        
    Raises:
        IOSaveError: If the file cannot be saved.
    """
    try:
        ensure_dir(Path(file_path).parent)
        with open(file_path, "w") as f:
            for item in data:
                f.write(json.dumps(item, **kwargs) + "\n")
    except Exception as e:
        raise IOSaveError(f"Failed to save JSONL {file_path}: {e}")