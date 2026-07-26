import logging
import sys
from pathlib import Path
from typing import List

# Import existing utility to ensure project root logic is consistent
# The API surface indicates setup_project_structure exists, but we use pathlib directly here
# to avoid circular imports or re-defining logic not in scope for this specific task.

def get_project_root() -> Path:
    """Determine the project root directory (parent of 'code')."""
    current = Path(__file__).resolve()
    # Traverse up to find 'code' directory, then go up one more level
    if current.name == 'setup_directories.py':
        code_dir = current.parent
        if code_dir.name == 'code':
            return code_dir.parent
    # Fallback: assume current working directory is project root if structure is flat
    return Path.cwd()

def create_directories() -> List[str]:
    """
    Create the required directory structure for data storage.
    
    Returns:
        List of paths that were created or verified.
    """
    project_root = get_project_root()
    data_root = project_root / "data"
    dirs_to_create = [
        data_root / "raw",
        data_root / "processed",
    ]
    
    created_paths = []
    
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {dir_path}")
        else:
            logging.info(f"Directory already exists: {dir_path}")
        created_paths.append(str(dir_path))
        
    return created_paths

def main() -> int:
    """Entry point for the directory setup script."""
    configure_root_logger()
    logging.info("Starting directory structure creation for data storage.")
    
    try:
        created = create_directories()
        logging.info(f"Successfully ensured directories exist: {created}")
        return 0
    except Exception as e:
        logging.error(f"Failed to create directories: {e}", exc_info=True)
        return 1

def configure_root_logger():
    """Configure basic logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

if __name__ == "__main__":
    sys.exit(main())
