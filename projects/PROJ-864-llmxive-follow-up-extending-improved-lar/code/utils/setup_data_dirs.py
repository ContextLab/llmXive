import os
import sys
from pathlib import Path
from typing import List
from utils.logging import get_logger, info, error

def setup_data_directories() -> bool:
    """
    Create the required project directories: code/, data/, tests/, and state/.
    
    This function ensures that the directory structure required by the project
    exists under the project root. It creates the directories if they don't exist
    and verifies their existence afterwards.
    
    Returns:
        bool: True if all directories were successfully created or already exist,
              False if any directory creation failed.
    """
    logger = get_logger(__name__)
    
    # Define the directories to create relative to the project root
    # The project root is assumed to be the parent of the 'code' directory
    project_root = Path(__file__).resolve().parent.parent.parent
    
    directories_to_create: List[Path] = [
        project_root / "code",
        project_root / "data",
        project_root / "tests",
        project_root / "state"
    ]
    
    success = True
    
    for directory in directories_to_create:
        try:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                info(f"Created directory: {directory}")
            else:
                info(f"Directory already exists: {directory}")
            
            # Verify the directory exists and is actually a directory
            if not directory.is_dir():
                error(f"Path exists but is not a directory: {directory}")
                success = False
                
        except PermissionError as e:
            error(f"Permission denied when creating directory {directory}: {e}")
            success = False
        except OSError as e:
            error(f"OS error when creating directory {directory}: {e}")
            success = False
        except Exception as e:
            error(f"Unexpected error when creating directory {directory}: {e}")
            success = False
    
    if success:
        info("All required directories verified successfully.")
    else:
        error("Failed to create or verify one or more required directories.")
    
    return success
