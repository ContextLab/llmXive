"""
Secure Consent Storage Module

Implements secure storage logic for raw consent forms as per Constitution Principle VI.
- Ensures the consent directory exists at data/consent/
- Enforces file permissions (chmod 600) for all files in the directory
- Ensures the directory is excluded from version control via .gitignore
"""
import os
import stat
import logging
from pathlib import Path
from typing import Optional

# Ensure we can import from the project root if run as a script
# But primarily designed to be imported as a module
try:
    from utils.logging_utils import setup_logging, get_logger
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def setup_logging(): pass
    def get_logger(name): return logging.getLogger(name)

def ensure_consent_directory(base_path: Optional[Path] = None) -> Path:
    """
    Ensures the consent directory exists at the specified base path.
    Defaults to project root / data / consent.
    
    Args:
        base_path: Optional base path. If None, uses current working directory.
    
    Returns:
        Path to the consent directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    consent_dir = base_path / "data" / "consent"
    consent_dir.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger("secure_consent_storage")
    logger.info(f"Ensured consent directory exists: {consent_dir}")
    return consent_dir

def enforce_file_permissions(file_path: Path) -> None:
    """
    Sets file permissions to 600 (owner read/write only) for a specific file.
    
    Args:
        file_path: Path to the file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot set permissions on non-existent file: {file_path}")
    
    # chmod 600: Owner read/write only
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
    
    logger = get_logger("secure_consent_storage")
    logger.info(f"Set permissions 600 on file: {file_path}")

def enforce_directory_permissions(dir_path: Path) -> None:
    """
    Enforces 600 permissions on all files within a directory.
    
    Args:
        dir_path: Path to the directory.
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    logger = get_logger("secure_consent_storage")
    count = 0
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            enforce_file_permissions(file_path)
            count += 1
    
    logger.info(f"Enforced permissions on {count} files in {dir_path}")

def ensure_gitignore_exclusion(base_path: Optional[Path] = None) -> None:
    """
    Ensures the .gitignore file contains the rule to exclude data/consent/.
    
    Args:
        base_path: Optional base path. If None, uses current working directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    gitignore_path = base_path / ".gitignore"
    consent_rule = "data/consent/"
    
    if not gitignore_path.exists():
        # Create .gitignore if it doesn't exist
        gitignore_path.touch()
        logger = get_logger("secure_consent_storage")
        logger.info(f"Created .gitignore at {gitignore_path}")
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if consent_rule not in content:
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{consent_rule}\n")
        logger = get_logger("secure_consent_storage")
        logger.info(f"Added '{consent_rule}' to .gitignore")
    else:
        logger = get_logger("secure_consent_storage")
        logger.debug(f"'{consent_rule}' already present in .gitignore")

def secure_consent_storage(base_path: Optional[Path] = None) -> Path:
    """
    Main entry point to secure the consent storage area.
    1. Ensures the directory exists.
    2. Enforces 600 permissions on all existing files in the directory.
    3. Ensures .gitignore excludes the directory.
    
    Args:
        base_path: Optional base path. If None, uses current working directory.
    
    Returns:
        Path to the secured consent directory.
    """
    consent_dir = ensure_consent_directory(base_path)
    enforce_directory_permissions(consent_dir)
    ensure_gitignore_exclusion(base_path)
    
    logger = get_logger("secure_consent_storage")
    logger.info("Secure consent storage setup complete.")
    return consent_dir

def main():
    """
    CLI entry point for T019 task execution.
    Runs the secure storage logic against the project root.
    """
    setup_logging()
    logger = get_logger("secure_consent_storage")
    logger.info("Starting secure consent storage implementation (T019)...")
    
    try:
        # Run against the project root (where the script is likely called from)
        # We assume the project root is the parent of 'code'
        project_root = Path(__file__).resolve().parent.parent
        secure_consent_storage(project_root)
        logger.info("Task T019 completed successfully.")
    except Exception as e:
        logger.error(f"Task T019 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
