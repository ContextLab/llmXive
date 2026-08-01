"""
Environment configuration and management for the llmXive project.

Handles loading of environment variables (OPENNERO_API_KEY) and
resolution of local paths relative to the project root.
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Looks for a marker file (e.g., .project_root) or traverses up to find
    the directory containing 'code/', 'data/', 'tests/'.
    """
    current = Path(__file__).resolve()
    # Traverse up from code/ directory
    for parent in current.parents:
        if (parent / "code").exists() and (parent / "data").exists() and (parent / "tests").exists():
            return parent
    
    # Fallback: assume current directory structure if standard layout found
    if current.name == "env_config.py" and current.parent.name == "code":
        return current.parent.parent
    
    # Last resort: current working directory
    logger.warning("Could not auto-detect project root, using CWD.")
    return Path.cwd()

def get_openneuro_api_key(required: bool = False) -> Optional[str]:
    """
    Retrieve the OpenNeuro API key from environment variables.
    
    Args:
        required: If True, raise an error if the key is missing.
    
    Returns:
        The API key string or None.
    
    Raises:
        EnvironmentError: If required is True and the key is not set.
    """
    key = os.getenv("OPENNEURO_API_KEY")
    if required and not key:
        error_msg = (
            "OPENNEURO_API_KEY environment variable is not set. "
            "Please set it to access OpenNeuro datasets. "
            "Example: export OPENNEURO_API_KEY='your_key_here'"
        )
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    if key:
        logger.info("OpenNeuro API key found in environment.")
    return key

def get_path(relative_path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Resolve a relative path to an absolute path within the project structure.
    
    Args:
        relative_path: Path relative to the project root or specified base_dir.
        base_dir: Optional base directory. If None, uses project root.
    
    Returns:
        Absolute Path object.
    """
    if base_dir is None:
        base_dir = get_project_root()
    
    full_path = base_dir / relative_path
    return full_path.resolve()

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory to ensure.
    """
    if not path.exists():
        logger.info(f"Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)

def validate_environment() -> bool:
    """
    Validate that the necessary environment variables and directory structures exist.
    
    Returns:
        True if validation passes, False otherwise.
    """
    is_valid = True
    
    # Check API key (not strictly required for all tasks, but good to warn)
    if not get_openneuro_api_key(required=False):
        logger.warning("OPENNEURO_API_KEY not set. Some data downloads may fail.")
    
    # Check critical directories
    root = get_project_root()
    critical_dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "code",
        root / "tests",
        root / "results"
    ]
    
    for dir_path in critical_dirs:
        if not dir_path.exists():
            logger.error(f"Critical directory missing: {dir_path}")
            is_valid = False
    
    return is_valid

def main():
    """CLI entry point to validate environment and print paths."""
    print("=== llmXive Environment Configuration ===")
    root = get_project_root()
    print(f"Project Root: {root}")
    
    api_key = get_openneuro_api_key(required=False)
    if api_key:
        print("OpenNeuro API Key: [REDACTED] (Found)")
    else:
        print("OpenNeuro API Key: [MISSING]")
    
    if validate_environment():
        print("Environment validation: PASSED")
    else:
        print("Environment validation: FAILED")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
