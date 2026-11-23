import os
import stat
import logging
import subprocess
from pathlib import Path
from typing import Optional

from utils.logging_utils import get_logger

# Ensure the logger is configured
logger = get_logger(__name__)

# Constants
CONSENT_DIR = Path("data/consent")
GITIGNORE_PATH = Path(".gitignore")
PERMISSIONS_600 = stat.S_IRUSR | stat.S_IWUSR  # Owner read/write only

def ensure_consent_directory() -> None:
    """
    Ensure the data/consent/ directory exists.
    Creates it with restricted permissions (700) if it doesn't exist.
    """
    if not CONSENT_DIR.exists():
        logger.info(f"Creating consent directory: {CONSENT_DIR}")
        CONSENT_DIR.mkdir(parents=True, exist_ok=True)
        # Set directory permissions to 700 (rwx------)
        os.chmod(CONSENT_DIR, stat.S_IRWXU)
        logger.info(f"Set permissions 700 on {CONSENT_DIR}")
    else:
        logger.info(f"Consent directory already exists: {CONSENT_DIR}")

def enforce_file_permissions(file_path: Path) -> None:
    """
    Enforce 600 permissions on a specific file.
    Raises an error if the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot enforce permissions: file not found {file_path}")
    
    os.chmod(file_path, PERMISSIONS_600)
    logger.debug(f"Enforced 600 permissions on {file_path}")

def enforce_directory_permissions(dir_path: Path) -> None:
    """
    Enforce 700 permissions on a directory and 600 on all files within it.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Cannot enforce permissions: directory not found {dir_path}")
    
    # Set directory permissions
    os.chmod(dir_path, stat.S_IRWXU)
    logger.debug(f"Enforced 700 permissions on {dir_path}")

    # Iterate through files and set 600
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            os.chmod(file_path, PERMISSIONS_600)
            logger.debug(f"Enforced 600 permissions on {file_path}")

def ensure_gitignore_exclusion() -> None:
    """
    Ensure 'data/consent/' is excluded in .gitignore.
    Adds the line if it is missing.
    """
    if not GITIGNORE_PATH.exists():
        logger.warning(f".gitignore not found at {GITIGNORE_PATH}. Creating one.")
        GITIGNORE_PATH.touch()

    with open(GITIGNORE_PATH, "r") as f:
        lines = f.readlines()

    exclusion_line = "data/consent/\n"
    found = False
    for line in lines:
        if line.strip() == exclusion_line.strip():
            found = True
            break

    if not found:
        with open(GITIGNORE_PATH, "a") as f:
            f.write("\n" + exclusion_line)
        logger.info(f"Added '{exclusion_line.strip()}' to .gitignore")
    else:
        logger.debug(f"'{exclusion_line.strip()}' already present in .gitignore")

def secure_consent_storage() -> bool:
    """
    Main entry point for securing the consent storage.
    Returns True if successful, False otherwise.
    """
    try:
        ensure_consent_directory()
        enforce_directory_permissions(CONSENT_DIR)
        ensure_gitignore_exclusion()
        logger.info("Consent storage security verification complete.")
        return True
    except Exception as e:
        logger.error(f"Failed to secure consent storage: {e}")
        return False

def main() -> None:
    """
    CLI entry point for secure storage verification.
    """
    setup_logger = get_logger(__name__)
    logger.info("Starting secure storage verification for T019...")
    
    success = secure_consent_storage()
    
    if success:
        print("T019 Verification: SUCCESS")
        print(f"  - Directory '{CONSENT_DIR}' exists and is secured.")
        print(f"  - Permissions set to 700 (dir) and 600 (files).")
        print(f"  - '{CONSENT_DIR}/' is excluded from VCS in .gitignore.")
    else:
        print("T019 Verification: FAILED")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
