import os
import sys
from pathlib import Path
from typing import List
from utils.logging import get_logger, info, error

def setup_data_directories() -> bool:
    """
    Create required project directories: code/, data/, tests/, state/.
    Verifies existence after creation.
    
    Returns:
        bool: True if all directories created/verified successfully, False otherwise.
    """
    # Determine project root (assuming script runs from code/ or project root)
    # We need to navigate to the project root relative to this file
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    # Define required directories relative to project root
    required_dirs = [
        "code",
        "data",
        "tests",
        "state"
    ]
    
    logger = get_logger("setup_data_dirs")
    info(logger, "Starting directory initialization...")
    
    created_count = 0
    failed_dirs = []
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        try:
            if not dir_path.exists():
              dir_path.mkdir(parents=True, exist_ok=True)
              info(logger, f"Created directory: {dir_path}")
              created_count += 1
            else:
              info(logger, f"Directory already exists: {dir_path}")
            
            # Verify existence
            if not dir_path.is_dir():
                error(logger, f"Failed to verify directory: {dir_path}")
                failed_dirs.append(dir_name)
        except Exception as e:
            error(logger, f"Error creating directory {dir_name}: {str(e)}")
            failed_dirs.append(dir_name)
    
    if failed_dirs:
        error(logger, f"Failed to create/verify directories: {', '.join(failed_dirs)}")
        return False
    
    info(logger, f"Successfully initialized {created_count} directories.")
    return True
