"""Path management utilities for the project."""
import os
from pathlib import Path
from typing import Union

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_raw_path(*parts: str) -> Path:
    """Get path to data/raw directory."""
    root = get_project_root()
    path = root / "data" / "raw"
    if parts:
        path = path / "/".join(parts)
    ensure_dir(path)
    return path

def get_processed_path(*parts: str) -> Path:
    """Get path to data/processed directory."""
    root = get_project_root()
    path = root / "data" / "processed"
    if parts:
        path = path / "/".join(parts)
    ensure_dir(path)
    return path

def get_results_path(*parts: str) -> Path:
    """Get path to data/results directory."""
    root = get_project_root()
    path = root / "data" / "results"
    if parts:
        path = path / "/".join(parts)
    ensure_dir(path)
    return path

def get_code_path(*parts: str) -> Path:
    """Get path to code directory."""
    root = get_project_root()
    path = root / "code"
    if parts:
        path = path / "/".join(parts)
    return path

def get_docs_path(*parts: str) -> Path:
    """Get path to docs directory."""
    root = get_project_root()
    path = root / "docs"
    if parts:
        path = path / "/".join(parts)
    ensure_dir(path)
    return path

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    if isinstance(path, str):
        path = Path(path)
    
    # If path looks like a file (has a suffix), create parent directory
    if path.suffix:
        path = path.parent
    
    path.mkdir(parents=True, exist_ok=True)
    return path
