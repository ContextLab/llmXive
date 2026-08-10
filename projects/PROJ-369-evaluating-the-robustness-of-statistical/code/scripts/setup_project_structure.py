import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.config import get_path, ensure_dirs
from src.utils.logging import setup_logger, log_info, log_error
from src.utils.directory_manager import setup_project_directories, initialize_checksums

def main() -> int:
    """
    Script entry point to execute T001: Create project structure.
    """
    logger = setup_logger("setup_project_structure")
    try:
        log_info(logger, "Executing T001: Creating project structure...")
        
        # Ensure base directories exist before calling the manager
        ensure_dirs()
        
        # Create specific directories and get the list
        created_paths = setup_project_directories()
        
        # Generate the manifest
        manifest = initialize_checksums(created_paths)
        
        log_info(logger, "T001 Completed successfully.")
        log_info(logger, f"Manifest saved to: {get_path('state')}/structure_manifest.json")
        
        return 0
    except Exception as e:
        log_error(logger, f"T001 Failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
