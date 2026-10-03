"""
Configuration module: random seeds and file paths.
"""
import os
from pathlib import Path
from typing import Final, Dict, Any
from datetime import datetime

def get_config() -> Dict[str, Any]:
    """Return project configuration."""
    return {
        "seed": 42,
        "start_date": "2000-01-01",
        "end_date": "2023-12-31",
        "data_dir": Path("data"),
        "code_dir": Path("code"),
        "output_dir": Path("data/artifacts")
    }