"""
Configuration utilities for the Quantifying Dataset Sparsity Impact project.

This module provides a single public function ``load_env`` which loads
environment variables from a ``.env`` file (if present) and ensures that
the required ``MP_API_KEY`` variable is defined. If the variable is missing,
a ``RuntimeError`` is raised to abort any pipeline execution that depends on
the Materials Project API key.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

__all__ = ["load_env"]

def load_env() -> str:
    """
    Load environment variables from a ``.env`` file located at the project root
    and verify that ``MP_API_KEY`` is defined.

    Returns
    -------
    str
        The Materials Project API key.

    Raises
    ------
    RuntimeError
        If ``MP_API_KEY`` is not set after attempting to load the ``.env`` file.
    """
    # Resolve the path to the project root (the directory containing this file's parent)
    project_root = Path(__file__).resolve().parents[1]

    # Load a .env file if it exists at the project root
    env_path = project_root / ".env"
    if env_path.is_file():
        # ``load_dotenv`` returns True if the file was found and parsed
        load_dotenv(dotenv_path=env_path, override=True)

    # Retrieve the API key from the environment
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MP_API_KEY environment variable is required but not set. "
            "Create a .env file (see .env.example) or export the variable "
            "in your shell before running any pipeline script."
        )
    return api_key
