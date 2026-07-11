"""
Utility functions for the llmXive project.
"""
import hashlib
import json
import logging
import os
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance with deterministic formatting.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_deterministic_info(seed: int, details: Dict[str, Any]) -> None:
    """
    Log deterministic configuration info.
    """
    logger = get_logger()
    logger.info(f"Deterministic Run - Seed: {seed}")
    for key, value in details.items():
        logger.info(f"  {key}: {value}")


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_sha256_string(data: str) -> str:
    """
    Compute SHA-256 hash of a string.
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def tokenize_char_level_no_punct(text: str) -> List[str]:
    """
    Tokenize text into characters, removing punctuation.
    """
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator)
    # Convert to lowercase
    cleaned_text = cleaned_text.lower()
    # Return list of characters
    return list(cleaned_text)


def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save data to a JSON file.
    """
    path = Path(file_path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
