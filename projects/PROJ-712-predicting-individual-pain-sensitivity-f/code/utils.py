"""
Utility functions for the llmXive pain sensitivity project.

Provides:
- Seed pinning for reproducibility
- Logging setup
- Artifact hashing for Constitution Principle V
"""
import hashlib
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent


def set_global_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across numpy, python, and torch (if available).
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Attempt to seed torch if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_file: Optional path to log file. If None, logs only to console.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        project_root: Base directory for log file resolution. Defaults to PROJECT_ROOT.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("llmXive_pain")
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute() and project_root:
            log_path = project_root / log_path
        elif not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path
        
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file's contents.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hex digest string.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def record_artifact_hash(
    artifact_path: Union[str, Path],
    output_dir: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Record the hash of an artifact and its metadata for Constitution Principle V.
    
    This function computes the hash of the specified artifact file, stores it
    in a manifest file within the output directory, and returns the record.
    
    Args:
        artifact_path: Path to the artifact file to hash.
        output_dir: Directory where the manifest will be saved.
        metadata: Optional dictionary of additional metadata (e.g., source, timestamp).
        project_root: Base directory for path resolution. Defaults to PROJECT_ROOT.
        
    Returns:
        Dictionary containing the artifact record (path, hash, metadata).
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
        ValueError: If the artifact is a directory.
    """
    artifact_path = Path(artifact_path)
    output_dir = Path(output_dir)
    
    if not project_root:
        project_root = PROJECT_ROOT
        
    # Resolve relative paths against project root
    if not artifact_path.is_absolute():
        artifact_path = project_root / artifact_path
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
        
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    if artifact_path.is_dir():
        raise ValueError(f"Artifact must be a file, not a directory: {artifact_path}")
        
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Compute hash
    file_hash = compute_file_hash(artifact_path)
    
    # Prepare record
    record = {
        "path": str(artifact_path.relative_to(project_root)),
        "hash": file_hash,
        "algorithm": "sha256",
        "metadata": metadata or {}
    }
    
    # Load or create manifest
    manifest_path = output_dir / "artifact_manifest.json"
    manifest = {}
    
    if manifest_path.exists():
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    
    # Update manifest
    manifest[str(artifact_path)] = record
    
    # Save manifest
    import json
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return record