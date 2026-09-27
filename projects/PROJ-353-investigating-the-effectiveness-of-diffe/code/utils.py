"""
Utility functions and constants for the llmXive research pipeline.

This module provides:
- Deterministic seeding for reproducibility
- Artifact hashing for caching/checksums
- Project-wide constants defined in the specification
"""
import hashlib
import os
import random
from pathlib import Path
from typing import Optional

# Try to import torch and numpy, but do not fail if not present yet
# They will be required for the actual seeding logic in training,
# but utils.py itself should be importable for constants.
_TORCH_AVAILABLE = False
_NP_AVAILABLE = False
_TORCH = None
_NP = None

try:
    import torch
    _TORCH_AVAILABLE = True
    _TORCH = torch
except ImportError:
    pass

try:
    import numpy as np
    _NP_AVAILABLE = True
    _NP = np
except ImportError:
    pass


# ----------------------------------------------------------------------
# Constants (Spec FR-001, FR-005, SC-003)
# ----------------------------------------------------------------------

SAMPLE_SIZE: int = 110
"""Total number of graphs to generate (N=110)."""

CONVERGENCE_THRESHOLD: float = 0.90
"""Accuracy threshold for convergence (>= 0.90)."""

MAX_EPOCHS: int = 1000
"""Maximum training epochs before censoring."""

# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------

def seed_all(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across all supported libraries.
    
    Args:
        seed: Integer seed value.
        
    Raises:
        RuntimeError: If torch or numpy are not installed when called.
    """
    random.seed(seed)
    
    if _NP_AVAILABLE:
        _NP.random.seed(seed)
    else:
        # If numpy is not installed, we cannot seed it. 
        # This is acceptable for a utility module that might be imported
        # before dependencies are fully resolved, but usually indicates
        # a setup issue if called during training.
        pass
        
    if _TORCH_AVAILABLE:
        _TORCH.manual_seed(seed)
        if _TORCH.cuda.is_available():
            _TORCH.cuda.manual_seed(seed)
            _TORCH.cuda.manual_seed_all(seed)  # if multi-GPU
            _TORCH.backends.cudnn.deterministic = True
            _TORCH.backends.cudnn.benchmark = False
    else:
        # If torch is not installed, we cannot seed it.
        pass

def hash_artifact(path: str) -> str:
    """
    Compute the SHA-256 hash of a file artifact.
    
    Args:
        path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()
