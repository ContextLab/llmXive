"""
Project Configuration
Handles directory creation and configuration retrieval.
"""

import os
from pathlib import Path
from typing import Optional

# Base project root (assumed to be the directory containing this file's parent 'code')
# In a standard setup, we assume the script runs from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Structure
DIRECTORIES = [
    "code",
    "code/data",
    "code/model",
    "code/analysis",
    "code/utils",
    "data",
    "data/raw",
    "data/processed",
    "data/logs",
    "tests",
    "tests/unit",
    "tests/contract"
]

# Configuration Defaults
CONFIG = {
    "model_path": "meta-llama/Llama-2-7b-chat-hf", # Placeholder, overridden by env
    "timeout": 30,
    "seed": 42,
    "semantic_threshold": 0.95,
    "max_variants": 3,
    "budget_cap": 100
}

def ensure_directories() -> None:
    """Creates all required project directories if they do not exist."""
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> dict:
    """Returns a summary of current configuration."""
    return {
        "project_root": str(PROJECT_ROOT),
        "config": CONFIG,
        "directories": DIRECTORIES
    }
