"""
Configuration management for the Visual Aesthetics Credibility Study.

This module handles environment variable loading and validation for critical
project paths, specifically the IRB consent form source.
"""
import os
from pathlib import Path

# Default relative path from project root for the IRB consent file
DEFAULT_CONSENT_PATH = "data/consent/irb_approved.txt"
ENV_VAR_NAME = "IRB_CONSENT_FILE_PATH"

def get_consent_file_path() -> str:
    """
    Retrieves the path to the IRB approved consent file.

    Checks for the environment variable `IRB_CONSENT_FILE_PATH`.
    If not set, defaults to `data/consent/irb_approved.txt` relative to the
    project root.

    Returns:
        str: Absolute path to the consent file.

    Raises:
        FileNotFoundError: If the resolved file path does not exist on disk.
    """
    # Determine the project root (assuming code/utils/config.py is 2 levels deep)
    # We use the location of this module to find the root relative to the standard structure
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent

    # Check environment variable
    env_path = os.getenv(ENV_VAR_NAME)

    if env_path:
        # If env var is set, treat it as relative to project root or absolute
        if os.path.isabs(env_path):
            consent_path = Path(env_path)
        else:
            consent_path = project_root / env_path
    else:
        # Default fallback
        consent_path = project_root / DEFAULT_CONSENT_PATH

    # Validate existence
    if not consent_path.exists():
        raise FileNotFoundError(
            f"IRB Consent file not found at: {consent_path}. "
            f"Please ensure the file exists or set the {ENV_VAR_NAME} environment variable."
        )

    return str(consent_path)

def load_consent_text() -> str:
    """
    Loads the full text content of the IRB approved consent form.

    Returns:
        str: The raw text content of the consent file.

    Raises:
        FileNotFoundError: If the consent file is missing.
    """
    path = get_consent_file_path()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
