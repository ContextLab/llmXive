"""
Configuration and environment handling.
"""
import os
from pathlib import Path

ENV_VAR_NAME = "IRB_CONSENT_FILE_PATH"
DEFAULT_CONSENT_PATH = "data/consent/irb_approved.txt"

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_consent_file_path():
    """Return the path to the consent file."""
    path = os.getenv(ENV_VAR_NAME)
    if path:
        return Path(path)
    return get_project_root() / DEFAULT_CONSENT_PATH

def load_consent_text():
    """Load the IRB approved consent text."""
    consent_path = get_consent_file_path()
    if not consent_path.exists():
        raise FileNotFoundError(f"Consent file not found at {consent_path}")
    
    with open(consent_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_irb_protocol_id():
    """Get the IRB Protocol ID from the consent file or environment."""
    # For now, we assume it's embedded in the consent text or a separate config
    # This is a placeholder implementation
    return "PROJ-205-IRB-001"
