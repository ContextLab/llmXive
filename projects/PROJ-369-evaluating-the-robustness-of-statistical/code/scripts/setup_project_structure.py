import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Add code directory to path if running as script
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.config import get_path, ensure_dirs
from src.utils.directory_manager import setup_project_directories, initialize_checksums
from src.utils.logging import setup_logger, log_info, log_error

def main():
    """
    Script entry point to create project structure and manifest.
    """
    # Setup logging
    logger = setup_logger("structure_setup")
    log_info("Starting project structure initialization...")

    try:
        # Create directories
        created_paths = setup_project_directories()
        
        # Generate manifest
        manifest = initialize_checksums(created_paths)
        
        log_info(f"Successfully created {len(created_paths)} directories.")
        log_info(f"Manifest saved to: {get_path('state/structure_manifest.json')}")
        
        return 0
    except Exception as e:
        log_error(f"Failed to initialize project structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())