"""
Utility functions for the llmXive project.
Contains shared constants and helper functions.
"""
import os
from pathlib import Path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Default random seed for reproducibility (Constitution-I)
DEFAULT_SEED = 42

def get_seed() -> int:
    """Get the default random seed."""
    return DEFAULT_SEED

def ensure_dir(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def get_config_path() -> Path:
    """Get the path to the config file."""
    return PROJECT_ROOT / "code" / "config.yaml"

def get_state_path() -> Path:
    """Get the path to the state file."""
    return PROJECT_ROOT / "state" / "projects" / "PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml"