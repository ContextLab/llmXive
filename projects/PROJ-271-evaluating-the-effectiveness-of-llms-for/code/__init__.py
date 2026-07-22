"""
llmXive - Automated Science Pipeline for LLM Code Smell Detection

This package provides the core functionality for evaluating LLM effectiveness
in detecting code smells through static analysis and semantic inference.
"""

import os
import logging
from pathlib import Path

# Ensure required directory structure exists
def _ensure_directory_structure():
    """
    Create required project directories if they don't exist.
    
    Creates:
        - data/raw: For raw input data
        - data/processed: For processed datasets
        - results: For analysis outputs and reports
    """
    # Determine project root (parent of the 'code' directory)
    project_root = Path(__file__).parent.parent
    
    # Define required directories
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results"
    ]
    
    # Create directories
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Ensured directory exists: {dir_path}")
    
    return required_dirs

# Initialize directory structure on import
_ensure_directories = _ensure_directory_structure()

__version__ = "0.1.0"
__all__ = [
    "ensure_directory_structure",
    "_ensure_directories"
]