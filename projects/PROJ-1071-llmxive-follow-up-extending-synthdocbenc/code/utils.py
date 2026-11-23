"""
Utility functions for the llmXive SynthDocBench pipeline.

Implements:
- State update logic (atomic JSON updates)
- Random seed pinning (reproducibility)
- Checksum generation (Constitution Principle V)
"""
import hashlib
import json
import os
import random
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import torch


def pin_random_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across Python, NumPy, and PyTorch.
    
    Args:
        seed: The random seed to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior in CUDA operations
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def compute_file_checksum(
    file_path: Union[str, Path], algorithm: str = "sha256"
) -> str:
    """
    Compute the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        Hexadecimal digest of the file checksum.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def compute_directory_checksum(
    dir_path: Union[str, Path], algorithm: str = "sha256"
) -> str:
    """
    Compute a combined checksum for all files in a directory.
    
    Files are sorted by path to ensure deterministic ordering.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
    
    Returns:
        Hexadecimal digest of the directory checksum.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    hash_func = hashlib.new(algorithm)
    # Sort files for deterministic ordering
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            # Include relative path in hash for context
            rel_path = file_path.relative_to(dir_path)
            hash_func.update(str(rel_path).encode("utf-8"))
            # Include file content hash
            file_hash = compute_file_checksum(file_path, algorithm)
            hash_func.update(file_hash.encode("utf-8"))
    
    return hash_func.hexdigest()


def update_state_json(
    state_path: Union[str, Path],
    updates: Dict[str, Any],
    backup: bool = True,
) -> None:
    """
    Atomically update a JSON state file with new values.
    
    This function:
    1. Loads the existing state (or creates empty dict if file doesn't exist)
    2. Merges in the provided updates (deep merge for nested dicts)
    3. Writes to a temporary file
    4. Atomically renames to the target path
    
    Args:
        state_path: Path to the JSON state file.
        updates: Dictionary of values to update/merge into state.
        backup: If True, create a .bak backup before updating.
    
    Raises:
        json.JSONDecodeError: If the existing file is not valid JSON.
        IOError: If the file cannot be written.
    """
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON in state file: {state_path}", e.doc, e.pos
                )
    else:
        state = {}
    
    # Deep merge updates
    def deep_merge(base: Dict, updates: Dict) -> Dict:
        result = base.copy()
        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    state = deep_merge(state, updates)
    
    # Create backup if requested
    if backup and state_path.exists():
        backup_path = state_path.with_suffix(state_path.suffix + ".bak")
        shutil.copy2(state_path, backup_path)
    
    # Write to temporary file first (atomic on most filesystems)
    fd, temp_path = tempfile.mkstemp(
        suffix=state_path.suffix, dir=state_path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)
            f.write("\n")  # Ensure file ends with newline
        # Atomic rename
        shutil.move(temp_path, state_path)
    except Exception:
        # Clean up temp file if write fails
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def load_state_json(state_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON state file.
    
    Args:
        state_path: Path to the JSON state file.
    
    Returns:
        Dictionary containing the state.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    state_path = Path(state_path)
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_checksum(
    file_path: Union[str, Path], expected_checksum: str, algorithm: str = "sha256"
) -> bool:
    """
    Validate a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file to validate.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm to use.
    
    Returns:
        True if the checksum matches, False otherwise.
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum
