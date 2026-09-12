import os
import sys
from pathlib import Path
from typing import List

from utils.logging import get_logger, info, error

def setup_data_directories() -> bool:
    """
    Create the required project directories: code/, data/, tests/, state/.
    Verifies their existence after creation.
    
    Returns:
        True if all directories were created/verified successfully.
        Raises RuntimeError if verification fails.
    """
    # Determine project root based on this file's location
    # Assuming this file is at: projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/utils/setup_data_dirs.py
    # The project root is 4 levels up from this file.
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent.parent.parent
    
    directories_to_create: List[Path] = [
        project_root / "code",
        project_root / "data",
        project_root / "tests",
        project_root / "state"
    ]
    
    logger = get_logger("setup_data_dirs")
    info(f"Project root identified at: {project_root}")
    
    created_count = 0
    verified_count = 0
    
    for dir_path in directories_to_create:
        try:
            # Create parents if they don't exist (though usually they do)
            dir_path.mkdir(parents=True, exist_ok=True)
            info(f"Ensured existence of directory: {dir_path}")
            created_count += 1
            
            # Verify existence
            if dir_path.exists() and dir_path.is_dir():
                verified_count += 1
            else:
                error(f"Failed to verify directory creation: {dir_path}")
                
        except OSError as e:
            error(f"OS error while creating directory {dir_path}: {e}")
            raise RuntimeError(f"Failed to create directory {dir_path}: {e}")
        except Exception as e:
            error(f"Unexpected error while creating directory {dir_path}: {e}")
            raise RuntimeError(f"Unexpected error creating directory {dir_path}: {e}")
    
    if verified_count == len(directories_to_create):
        info(f"Successfully created and verified {verified_count} directories.")
        return True
    else:
        error(f"Verification failed. Created {created_count}, Verified {verified_count} out of {len(directories_to_create)}.")
        raise RuntimeError(f"Directory verification failed. Expected {len(directories_to_create)}, verified {verified_count}.")
