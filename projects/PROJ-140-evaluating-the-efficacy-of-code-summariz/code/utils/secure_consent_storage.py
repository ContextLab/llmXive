"""
Secure storage logic for raw consent forms.
Implements Constitution Principle VI: Non-public storage with access control.

This module ensures:
1. Consent forms are stored in a non-public directory (`data/consent/`).
2. File permissions are set to `chmod 600` (owner read/write only).
3. The directory is explicitly excluded from version control via `.gitignore`.
"""
import os
import stat
import logging
from pathlib import Path
from typing import Optional

# Import logging setup from existing utils
from utils.logging_utils import setup_logging, get_logger

# Configure logger
logger = get_logger(__name__)

CONSENT_DIR = Path("data/consent")
GITIGNORE_PATH = Path(".gitignore")
GITIGNORE_RULE = "data/consent/"

def ensure_consent_directory() -> Path:
    """
    Creates the consent directory if it does not exist.
    Returns the path to the directory.
    """
    if not CONSENT_DIR.exists():
        CONSENT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created consent directory: {CONSENT_DIR}")
    else:
        logger.debug(f"Consent directory already exists: {CONSENT_DIR}")
    return CONSENT_DIR

def enforce_file_permissions(file_path: Path) -> bool:
    """
    Sets file permissions to 600 (owner read/write only) for a specific file.
    
    Args:
        file_path: Path to the file to secure.
        
    Returns:
        True if permissions were successfully set, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for permission enforcement: {file_path}")
        return False

    try:
        # Calculate the desired mode: read/write for owner, nothing for others
        desired_mode = stat.S_IRUSR | stat.S_IWUSR
        
        # Get current mode
        current_mode = file_path.stat().st_mode
        
        if current_mode != desired_mode:
            file_path.chmod(desired_mode)
            logger.info(f"Enforced permissions 600 on: {file_path}")
            return True
        else:
            logger.debug(f"Permissions already correct for: {file_path}")
            return True
    except PermissionError as e:
        logger.error(f"Permission denied while setting permissions on {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error setting permissions on {file_path}: {e}")
        return False

def enforce_directory_permissions(dir_path: Path) -> bool:
    """
    Sets directory permissions to 700 (owner read/write/execute only) 
    and recursively secures all files within to 600.
    
    Args:
        dir_path: Path to the directory to secure.
        
    Returns:
        True if all operations succeeded, False otherwise.
    """
    if not dir_path.exists():
        logger.error(f"Directory not found: {dir_path}")
        return False

    success = True
    try:
        # Set directory permissions to 700 (rwx for owner)
        dir_path.chmod(stat.S_IRWXU)
        logger.info(f"Enforced permissions 700 on directory: {dir_path}")
    except Exception as e:
        logger.error(f"Failed to set directory permissions on {dir_path}: {e}")
        success = False

    # Secure all files inside
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            if not enforce_file_permissions(file_path):
                success = False
        
    return success

def ensure_gitignore_exclusion() -> bool:
    """
    Ensures the `.gitignore` file exists and contains the exclusion rule for `data/consent/`.
    
    Returns:
        True if the rule is present or added successfully, False otherwise.
    """
    try:
        if not GITIGNORE_PATH.exists():
            GITIGNORE_PATH.touch()
            logger.info("Created new .gitignore file.")
        
        current_content = GITIGNORE_PATH.read_text()
        
        if GITIGNORE_RULE not in current_content:
            with open(GITIGNORE_PATH, "a") as f:
                f.write(f"\n# Secure consent forms (Principle VI)\n{GITIGNORE_RULE}\n")
            logger.info(f"Added exclusion rule '{GITIGNORE_RULE}' to .gitignore")
            return True
        else:
            logger.debug(f"Exclusion rule '{GITIGNORE_RULE}' already present in .gitignore")
            return True
    except Exception as e:
        logger.error(f"Failed to update .gitignore: {e}")
        return False

def secure_consent_storage() -> bool:
    """
    Main entry point to secure the consent storage infrastructure.
    
    1. Ensures the directory exists.
    2. Ensures .gitignore excludes the directory.
    3. Enforces permissions on the directory and all existing files.
    
    Returns:
        True if all steps completed successfully, False otherwise.
    """
    logger.info("Starting secure consent storage setup...")
    
    # 1. Ensure directory exists
    ensure_consent_directory()
    
    # 2. Ensure gitignore exclusion
    if not ensure_gitignore_exclusion():
        logger.warning("Could not ensure .gitignore exclusion, but continuing with permissions.")
    
    # 3. Enforce permissions
    if not enforce_directory_permissions(CONSENT_DIR):
        logger.error("Failed to enforce directory permissions.")
        return False
    
    logger.info("Secure consent storage setup completed successfully.")
    return True

def main():
    """
    CLI entry point for securing consent storage.
    """
    setup_logging()
    success = secure_consent_storage()
    if success:
        print("Secure consent storage logic applied successfully.")
        exit(0)
    else:
        print("Failed to apply secure consent storage logic. Check logs.")
        exit(1)

if __name__ == "__main__":
    main()
