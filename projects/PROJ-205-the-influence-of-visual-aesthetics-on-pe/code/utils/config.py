import os
from pathlib import Path

# Environment variable name for the IRB consent file path
ENV_VAR_NAME = "IRB_CONSENT_FILE_PATH"

# Default relative path from project root
DEFAULT_CONSENT_PATH = "data/consent/irb_approved.txt"

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the code structure is:
    project_root/
        code/
            utils/
                config.py
    """
    return Path(__file__).resolve().parent.parent.parent

def get_consent_file_path() -> Path:
    """
    Returns the path to the IRB-approved consent text file.
    Priority:
    1. Environment variable defined by ENV_VAR_NAME
    2. Default path relative to project root
    
    Raises:
        FileNotFoundError: If the file does not exist at the resolved path.
    """
    project_root = get_project_root()
    
    # Check for environment variable override
    env_path = os.getenv(ENV_VAR_NAME)
    if env_path:
        path_obj = Path(env_path)
        # If it's an absolute path, use it directly; otherwise, resolve relative to CWD or project root
        if not path_obj.is_absolute():
            # Prefer relative to project root if not absolute
            path_obj = project_root / path_obj
    else:
        # Default path relative to project root
        path_obj = project_root / DEFAULT_CONSENT_PATH
    
    if not path_obj.exists():
        raise FileNotFoundError(
            f"Consent file not found at {path_obj}. "
            f"Please ensure the file exists or set the {ENV_VAR_NAME} environment variable."
        )
    
    return path_obj

def load_consent_text() -> str:
    """
    Loads the full text of the IRB-approved consent form.
    
    Returns:
        str: The complete text content of the consent file.
        
    Raises:
        FileNotFoundError: If the consent file is missing.
        PermissionError: If the file cannot be read.
    """
    file_path = get_consent_file_path()
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
