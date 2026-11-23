"""
Helper utilities for the training module.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logging import get_logger, info, error
from utils.config import get_project_root, get_artifacts_dir

logger = get_logger(__name__)

def ensure_training_dirs() -> Dict[str, Path]:
    """
    Ensure all necessary directories for training exist.
    
    Returns:
        Dict mapping directory names to Path objects.
    """
    project_root = get_project_root()
    code_root = project_root / "code"
    
    # Define required directories
    dirs = {
        "training": code_root / "training",
        "logs": project_root / "data" / "artifacts" / "logs",
        "checkpoints": project_root / "data" / "artifacts" / "checkpoints",
        "metrics": project_root / "data" / "artifacts" / "metrics",
    }
    
    # Create directories if they don't exist
    for dir_name, dir_path in dirs.items():
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            info(f"Created directory: {dir_path}")
        else:
            debug(f"Directory already exists: {dir_path}")
    
    return dirs
