"""
Configuration management for the llmXive project.

Provides functions to load environment variables and resolve
project-specific file system paths relative to the project root.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Determine the project root based on the standard layout:
# code/config.py -> parent is code/ -> parent is project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env() -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists,
    and returns a dictionary of relevant configuration variables.

    This function checks for a .env file in the project root.
    It does not strictly require 'python-dotenv' to be installed
    to function, but attempts to use it if available for robustness.
    If 'python-dotenv' is not installed, it falls back to manual parsing.

    Returns:
        Dict[str, str]: A dictionary of environment variables found.
    """
    env_vars = {}
    env_file = _PROJECT_ROOT / ".env"

    if env_file.exists():
        try:
            # Attempt to use python-dotenv if installed
            import dotenv
            # dotenv.load_dotenv() modifies os.environ in-place
            # We return a snapshot of what we care about or the whole env
            # For this task, we return the dict representation of os.environ
            # filtered or just the raw dict if we want simplicity.
            # Let's return the raw dict of os.environ for completeness.
            return dict(os.environ)
        except ImportError:
            # Fallback: manual parsing if python-dotenv is missing
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
    
    return dict(os.environ)


def load_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of resolved absolute paths for project directories
    and key files based on the project root.

    Returns:
        Dict[str, Path]: A mapping of logical names to Path objects.
    """
    paths = {
        "root": _PROJECT_ROOT,
        "data": _PROJECT_ROOT / "data",
        "data_raw": _PROJECT_ROOT / "data" / "raw",
        "data_elemental_properties": _PROJECT_ROOT / "data" / "elemental_properties",
        "data_processed": _PROJECT_ROOT / "data" / "processed",
        "data_evaluation": _PROJECT_ROOT / "data" / "evaluation",
        "data_logs": _PROJECT_ROOT / "data" / "logs",
        "code": _PROJECT_ROOT / "code",
        "code_utils": _PROJECT_ROOT / "code" / "utils",
        "tests": _PROJECT_ROOT / "tests",
        "tests_contract": _PROJECT_ROOT / "tests" / "contract",
        "tests_unit": _PROJECT_ROOT / "tests" / "unit",
        "contracts": _PROJECT_ROOT / "contracts",
        "specs": _PROJECT_ROOT / "specs",
        "figures": _PROJECT_ROOT / "data" / "evaluation" / "pdp_plots", # Default figure output location
    }

    # Ensure all directories exist (side effect for robustness)
    # This is safe to do as it matches T001/T004 intent
    for path_key, path_val in paths.items():
        if path_key != "root": # Root is assumed to exist
            path_val.mkdir(parents=True, exist_ok=True)

    return paths