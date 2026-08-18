import os
from pathlib import Path

# Environment variable name for the IRB consent file path
ENV_VAR_NAME = "IRB_CONSENT_FILE_PATH"
DEFAULT_CONSENT_PATH = "data/consent/irb_approved.txt"

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the project structure is:
    PROJ-205-.../
      code/
      data/
      ...
    This function walks up from the current file to find the root.
    """
    current_path = Path(__file__).resolve()
    # Walk up until we find a directory that looks like the project root
    # We assume the project root contains a 'code' directory at the same level as 'data'
    for parent in current_path.parents:
        if (parent / "code").exists() and (parent / "data").exists():
            return parent
    # Fallback to current working directory if structure not found
    return Path.cwd()

def get_consent_file_path() -> Path:
    """
    Returns the path to the IRB-approved consent file.
    Priority:
    1. Environment variable IRB_CONSENT_FILE_PATH (absolute or relative to project root)
    2. Default path: data/consent/irb_approved.txt (relative to project root)

    Raises:
        FileNotFoundError: If the file does not exist at the resolved path.
    """
    project_root = get_project_root()
    env_path = os.getenv(ENV_VAR_NAME)

    if env_path:
        # Check if env path is absolute or relative
        if Path(env_path).is_absolute():
            consent_path = Path(env_path)
        else:
            # Treat relative paths as relative to project root
            consent_path = project_root / env_path
    else:
        consent_path = project_root / DEFAULT_CONSENT_PATH

    if not consent_path.exists():
        raise FileNotFoundError(
            f"IRB consent file not found at: {consent_path}. "
            f"Please set the {ENV_VAR_NAME} environment variable or ensure the default file exists."
        )

    return consent_path

def load_consent_text() -> str:
    """
    Loads and returns the full text of the IRB-approved consent form.

    Returns:
        str: The content of the consent file.

    Raises:
        FileNotFoundError: If the consent file path is invalid.
        PermissionError: If the file cannot be read.
    """
    consent_path = get_consent_file_path()
    with open(consent_path, "r", encoding="utf-8") as f:
        return f.read()

def get_irb_protocol_id() -> str:
    """
    Extracts the IRB Protocol ID from the consent text.
    Looks for a line starting with "IRB Protocol ID:" or "IRB Protocol ID for Verification:".

    Returns:
        str: The extracted protocol ID.

    Raises:
        ValueError: If the protocol ID cannot be found in the consent text.
    """
    consent_text = load_consent_text()
    lines = consent_text.splitlines()
    for line in lines:
        if "IRB Protocol ID" in line and ":" in line:
            # Extract the part after the colon
            parts = line.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
    
    raise ValueError("IRB Protocol ID not found in consent text.")
