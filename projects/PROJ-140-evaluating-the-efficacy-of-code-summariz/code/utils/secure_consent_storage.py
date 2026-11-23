import os
import stat
import logging
from pathlib import Path
from typing import Optional

from utils.logging_utils import get_logger

# Constants
CONSENT_DIR = Path("data/consent")
GITIGNORE_PATH = Path(".gitignore")
PERMISSION_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0o600 (rw-------)
DIRECTORY_PERMISSION_MODE = stat.S_IRWXU  # 0o700 (rwx------)

logger = get_logger(__name__)

def ensure_consent_directory(directory: Optional[Path] = None) -> Path:
    """
    Ensure the consent directory exists. Creates it with restricted permissions if missing.
    
    Args:
        directory: Optional custom path. Defaults to data/consent.
        
    Returns:
        Path to the consent directory.
    """
    target_dir = directory if directory else CONSENT_DIR
    
    if not target_dir.exists():
        target_dir.mkdir(parents=True, mode=DIRECTORY_PERMISSION_MODE)
        logger.info(f"Created consent directory: {target_dir} with permissions 0o700")
    else:
        logger.debug(f"Consent directory already exists: {target_dir}")
        
    return target_dir

def enforce_file_permissions(file_path: Path) -> None:
    """
    Set file permissions to 0o600 (read/write for owner only).
    
    Args:
        file_path: Path to the file.
    """
    if not file_path.exists():
        logger.warning(f"Cannot enforce permissions on non-existent file: {file_path}")
        return

    try:
        # Remove all permissions first, then set owner read/write
        os.chmod(file_path, PERMISSION_MODE)
        logger.debug(f"Enforced permissions 0o600 on: {file_path}")
    except PermissionError as e:
        logger.error(f"Permission denied while setting file permissions: {file_path} - {e}")
        raise
    except OSError as e:
        logger.error(f"OS error while setting file permissions: {file_path} - {e}")
        raise

def enforce_directory_permissions(directory: Path) -> None:
    """
    Set directory permissions to 0o700 (read/write/execute for owner only).
    
    Args:
        directory: Path to the directory.
    """
    if not directory.exists():
        logger.warning(f"Cannot enforce permissions on non-existent directory: {directory}")
        return

    try:
        os.chmod(directory, DIRECTORY_PERMISSION_MODE)
        logger.debug(f"Enforced permissions 0o700 on: {directory}")
    except PermissionError as e:
        logger.error(f"Permission denied while setting directory permissions: {directory} - {e}")
        raise
    except OSError as e:
        logger.error(f"OS error while setting directory permissions: {directory} - {e}")
        raise

def ensure_gitignore_exclusion() -> None:
    """
    Ensure that 'data/consent/' is excluded in .gitignore.
    Adds the rule if it does not exist.
    """
    if not GITIGNORE_PATH.exists():
        GITIGNORE_PATH.touch()
        logger.info("Created .gitignore file.")

    current_content = GITIGNORE_PATH.read_text()
    consent_rule = "data/consent/"

    if consent_rule not in current_content:
        # Ensure there's a newline before appending if file isn't empty
        if current_content and not current_content.endswith('\n'):
            current_content += '\n'
        
        with open(GITIGNORE_PATH, 'a') as f:
            f.write(f"{consent_rule}\n")
        
        logger.info(f"Added '{consent_rule}' to .gitignore")
    else:
        logger.debug(f"'{consent_rule}' already present in .gitignore")

def secure_consent_storage(base_dir: Optional[Path] = None) -> Path:
    """
    Main entry point to secure the consent storage.
    
    1. Ensures the directory exists with restricted permissions.
    2. Ensures all existing files inside have restricted permissions.
    3. Ensures .gitignore excludes the directory.
    
    Args:
        base_dir: Optional base directory override.
        
    Returns:
        Path to the secured consent directory.
    """
    target_dir = base_dir if base_dir else CONSENT_DIR
    
    # 1. Ensure directory exists and has correct permissions
    ensure_consent_directory(target_dir)
    enforce_directory_permissions(target_dir)
    
    # 2. Enforce permissions on all existing files in the directory
    if target_dir.exists():
        for item in target_dir.iterdir():
            if item.is_file():
                enforce_file_permissions(item)
            elif item.is_dir():
                # Recursively secure subdirectories if any
                for sub_item in item.rglob('*'):
                    if sub_item.is_file():
                        enforce_file_permissions(sub_item)
    
    # 3. Ensure gitignore exclusion
    ensure_gitignore_exclusion()
    
    logger.info(f"Secure consent storage initialized at {target_dir}")
    return target_dir

def main() -> None:
    """
    CLI entry point to run the secure consent storage setup.
    """
    logger.info("Starting secure consent storage setup...")
    try:
        secure_consent_storage()
        logger.info("Secure consent storage setup completed successfully.")
    except Exception as e:
        logger.error(f"Failed to setup secure consent storage: {e}")
        raise

if __name__ == "__main__":
    main()
