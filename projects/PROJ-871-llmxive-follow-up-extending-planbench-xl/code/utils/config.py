import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root is determined by the presence of a marker or by traversing up
# Assuming the project root is the directory containing this file's parent structure
# In the deployed structure: projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/
# This script runs from code/, so we look for the project root.
_PROJECT_ROOT = None

def get_project_root() -> Path:
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Try to find the project root by looking for the specific project directory name
        # or by traversing up from the current file location
        current = Path(__file__).resolve()
        # Traverse up until we find the specific project folder or a marker
        # Assuming the structure: projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/utils/config.py
        # We look for 'code' then the project folder
        parts = current.parts
        try:
            # Find the index of 'code'
            code_idx = parts.index('code')
            # The project root is the parent of 'code'
            _PROJECT_ROOT = Path(*parts[:code_idx])
        except ValueError:
            # Fallback: assume current working directory is project root or parent
            _PROJECT_ROOT = Path.cwd()
    return _PROJECT_ROOT

def get_path(key: str) -> str:
    """
    Retrieve a path from the configuration based on a key.
    Defaults to standard relative paths if not explicitly configured.
    """
    root = get_project_root()
    paths_map = {
        "raw_data": "data/raw",
        "derived_data": "data/derived",
        "logs": "data/logs",
        "results": "data/results",
        "failure_signatures": "data/derived/failure_signatures.json",
        "implicit_failure_subset": "data/derived/implicit_failure_subset.jsonl",
        "baseline_log": "data/logs/baseline_execution.jsonl",
        "augmented_log": "data/logs/augmented_execution.jsonl",
        "final_report": "data/results/final_report.json",
    }
    relative = paths_map.get(key, key)
    return str(root / relative)

def get_hyperparameter(key: str, default: Any = None) -> Any:
    """
    Retrieve a hyperparameter from the configuration.
    In a real system, this might read from a config.yaml or env vars.
    For now, it returns defaults or environment variables.
    """
    env_val = os.getenv(f"LLMXIVE_{key.upper()}")
    if env_val is not None:
        return env_val
    defaults = {
        "max_tokens": 512,
        "temperature": 0.7,
        "model": "llama-3-8b-quantized",
        "seed": 42,
    }
    return defaults.get(key, default)

def ensure_dirs_exist() -> None:
    """
    Ensure all required data directories exist.
    """
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "derived",
        root / "data" / "logs",
        root / "data" / "results",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
