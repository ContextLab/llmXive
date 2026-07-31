"""
Configuration and path management for the project.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the code is located in a 'code' subdirectory of the root.
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def ensure_directories() -> None:
    """
    Creates the necessary directory structure for the project.
    """
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "final",
        root / "data" / "final" / "plots",
        root / "code",
        root / "tests",
        root / "contracts",
        root / "specs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """
    Returns a dictionary of configuration values.
    """
    root = get_project_root()
    return {
        "project_root": str(root),
        "data_raw": str(root / "data" / "raw"),
        "data_processed": str(root / "data" / "processed"),
        "data_final": str(root / "data" / "final"),
        "plots_dir": str(root / "data" / "final" / "plots"),
        "levenshtein_threshold": 4,
        "match_rate_threshold": 0.80,
        "seed": 42,
        "use_mock_data": False,
        "msd_url": "hf://brian/MSD",
        "amt_url": "hf://brian/AMT"
    }