"""
T034: Refactored Utility Functions.

Consolidates common utility functions used across `code/graph_builder.py`,
`code/topology_extractor.py`, and `code/evaluator.py` to reduce duplication
and improve type safety.

Exports:
- `normalize_feature_vector`: Standardizes numerical features.
- `safe_divide`: Prevents division by zero errors in metric calculations.
- `calculate_hash`: Unified hashing utility.
"""

import hashlib
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
import json
from pathlib import Path

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divides two numbers, returning a default value if the denominator is zero.
    Replaces repetitive `if denominator == 0` checks in topology and retrieval modules.
    """
    if denominator == 0:
        return default
    return numerator / denominator

def normalize_feature_vector(
    features: List[float],
    method: str = "zscore"
) -> List[float]:
    """
    Normalizes a list of numerical features.
    Supports 'zscore' (standardization) and 'minmax' scaling.
    """
    if not features:
        return []

    arr = np.array(features)
    if method == "zscore":
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return [0.0] * len(features)
        return ((arr - mean) / std).tolist()
    elif method == "minmax":
        min_val, max_val = np.min(arr), np.max(arr)
        if max_val == min_val:
            return [0.0] * len(features)
        return ((arr - min_val) / (max_val - min_val)).tolist()
    else:
        raise ValueError(f"Unknown normalization method: {method}")

def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.
    Used for artifact versioning and integrity checks.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_metric_value(
    logger: logging.Logger,
    metric_name: str,
    value: Union[float, int, str],
    level: int = logging.INFO
) -> None:
    """
    Logs a metric value with a consistent format.
    """
    logger.log(level, f"{metric_name}: {value}")

def validate_json_schema(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validates that a dictionary contains all required keys.
    Simple schema validation without external dependencies.
    """
    missing = [key for key in required_keys if key not in data]
    if missing:
        return False
    return True

def read_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Reads a JSON file safely, returning None on failure.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return None

def write_json_safe(file_path: Path, data: Dict[str, Any]) -> bool:
    """
    Writes data to a JSON file safely.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except IOError as e:
        return False
