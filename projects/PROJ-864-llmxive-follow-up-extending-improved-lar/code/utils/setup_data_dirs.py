import os
from pathlib import Path
import sys
from utils.logging import get_logger, info, error

def setup_data_directories() -> bool:
    """
    Creates the required data directory structure for the project:
    - data/raw/
    - data/processed/
    - data/artifacts/

    Returns True if all directories were created or already exist, False on failure.
    """
    logger = get_logger(__name__)
    try:
        # Determine the project root. We assume this script is run from 'code/'
        # or that the caller has set the working directory appropriately.
        # We look for 'projects/PROJ-864-llmxive-follow-up-extending-improved-lar'
        # relative to the current working directory if 'code' is a subdirectory,
        # or we assume the current directory is the project root if 'code' is present.
        
        current_path = Path.cwd()
        
        # Strategy: Look for the 'code' directory. If we are inside it, go up.
        # If we are at the project root, 'code' should exist here.
        if (current_path / "code").is_dir():
            project_root = current_path
        elif (current_path / "projects").is_dir():
            # Search for the specific project folder
            proj_folder = current_path / "projects" / "PROJ-864-llmxive-follow-up-extending-improved-lar"
            if proj_folder.is_dir() and (proj_folder / "code").is_dir():
                project_root = proj_folder
            else:
                # Fallback: assume current path is project root if it contains 'code' directly or is the target
                # Given the task description, we assume the runner is in the project root or 'code'
                project_root = current_path
                if not (project_root / "code").is_dir():
                    # If we are in 'code', go up
                    if (current_path.parent / "code").is_dir():
                        project_root = current_path.parent
        else:
            project_root = current_path
            # If 'code' doesn't exist here, we might be in 'code'
            if not (project_root / "code").is_dir():
                 # Check if we are already in code
                 if current_path.name == "code":
                     project_root = current_path.parent
        
        data_dir = project_root / "data"
        
        sub_dirs = [
            data_dir / "raw",
            data_dir / "processed",
            data_dir / "artifacts"
        ]
        
        created_count = 0
        for dir_path in sub_dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                info(f"Created directory: {dir_path}")
                created_count += 1
            else:
                info(f"Directory already exists: {dir_path}")
        
        if created_count > 0:
            info(f"Successfully created {created_count} data directories under {data_dir}")
        else:
            info("All required data directories already exist.")
        
        return True

    except PermissionError as e:
        error(f"Permission denied while creating data directories: {e}")
        return False
    except OSError as e:
        error(f"OS error while creating data directories: {e}")
        return False
    except Exception as e:
        error(f"Unexpected error during data directory setup: {e}")
        return False
