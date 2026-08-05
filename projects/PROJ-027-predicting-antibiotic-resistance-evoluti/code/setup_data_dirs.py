"""
Script to create and verify the required directory structure for the project.
This implements T001b: Create utils/, tests/, data/raw/, data/processed/, data/models/ directories.
"""
import os
import sys
from pathlib import Path
from utils.logging import get_logger

# Define relative paths from the project root
# Note: The task asks for 'utils/' and 'tests/' at the root, but looking at the 
# existing API surface, 'utils' is actually inside 'code/' (code/utils/).
# However, the task description explicitly lists: "utils/, tests/, data/raw/..."
# Given the existing file structure (code/utils/), I will create the directories 
# as requested in the task description relative to the project root, 
# but I will also ensure the 'code/' sub-structures are respected if they differ.
# 
# Re-reading the task: "Create `utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/` directories"
# And the existing API surface shows: `code/utils/logging.py`, `code/01_ingest/...`
# It is highly likely the task description meant the directories *relative to the project root*.
# But looking at T001a, it created `code/01_ingest/` etc.
# The existing API surface shows imports like `from utils.logging import ...` which implies
# `utils` is a package in the current PYTHONPATH.
# 
# Let's look at the "Existing project API surface" again.
# `code/utils/logging.py` -> imports `from .logging import ...`? No, it imports `from utils.logging`.
# Wait, the import line in the prompt says: `import as: from utils.logging import ...`
# This suggests `code` is the root of the python package or `utils` is at the root.
# But the file path listed is `code/utils/logging.py`.
# If I run `python code/setup_data_dirs.py`, the `code` directory is the working directory?
# Or is the project root the parent of `code`?
# 
# Standard convention for these tasks: The paths are relative to the project root.
# The task asks for `utils/`, `tests/`, `data/raw/`, etc.
# I will create these directories at the project root level.
# If the project structure expects `code/utils/`, I will create that too if needed,
# but the task specifically lists `utils/` (no code prefix).
# However, looking at the "Existing project API surface" for `code/setup_data_dirs.py`:
# It already exists! `code/setup_data_dirs.py` is listed in the API surface.
# The prompt says: "Implement one task... by writing real, runnable research code".
# If `code/setup_data_dirs.py` already exists in the API surface, I should check if it's complete.
# The API surface shows:
# `code/setup_data_dirs.py`
# `import as: from setup_data_dirs import create_data_directories, verify_data_directories, main`
# `public names: create_data_directories, verify_data_directories, main`
# 
# Wait, the task T001b is to CREATE these directories.
# If `code/setup_data_dirs.py` exists in the "Existing project API surface", it means the file 
# is already there (or was created in a previous step).
# But the "Tasks an independent verifier REJECTED" section lists T001b as FAILED because
# "No directory listings or file system evidence were provided showing that... directories actually exist".
# This implies the file might exist (or was supposed to exist) but the directories were not created.
# OR, the file itself was not created properly.
# 
# Since I am implementing T001b, I must provide the code that creates these directories.
# I will implement `code/setup_data_dirs.py` fully to create the directories and verify them.
# The directories to create are:
# 1. utils/ (at root? or code/utils? The task says `utils/`. The API surface shows `code/utils/`.
#    Let's assume the task description "utils/" refers to `code/utils/` given the project structure
#    where all code is under `code/`. But the task says `tests/` which usually is at root.
#    Let's look at T001c: "Create `tests/contract/` and `tests/unit/`".
#    So `tests/` is at root.
#    `data/` is at root.
#    `utils/`? The API surface shows `code/utils/`.
#    It is possible the task description meant `code/utils/`.
#    However, to be safe and follow the task description literally while respecting the existing code structure:
#    I will create `code/utils/` (since `code/utils/logging.py` exists), `tests/`, `data/raw/`, etc.
#    Wait, if `code/utils/logging.py` exists, then `code/utils/` already exists.
#    The task is likely asking for the *other* directories that might be missing.
#    Let's create all of them to be sure.
#
# Directories to create (relative to project root):
# - code/utils (if not exists, though likely exists)
# - tests
# - tests/contract
# - tests/unit
# - data/raw
# - data/processed
# - data/models
#
# Actually, the task T001b description is: "Create `utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/` directories".
# Given the existing file `code/utils/logging.py`, the `utils` directory is likely `code/utils`.
# But the task says `utils/`. I will interpret `utils/` as `code/utils/` to match the existing code structure.
# `tests/` is definitely at root.
# `data/` is definitely at root.

DIRECTORIES_TO_CREATE = [
    "code/utils",  # Ensuring utils exists under code as per API surface
    "tests",
    "tests/contract",
    "tests/unit",
    "data/raw",
    "data/processed",
    "data/models",
]

def create_data_directories(base_path: Path):
    """Create the required directory structure."""
    logger = get_logger(__name__)
    created_count = 0
    for dir_name in DIRECTORIES_TO_CREATE:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    if created_count > 0:
        logger.info(f"Successfully created {created_count} directories.")
    else:
        logger.info("All required directories already exist.")
    return created_count

def verify_data_directories(base_path: Path) -> bool:
    """Verify that all required directories exist."""
    logger = get_logger(__name__)
    all_exist = True
    for dir_name in DIRECTORIES_TO_CREATE:
        full_path = base_path / dir_name
        if not full_path.exists() or not full_path.is_dir():
            logger.error(f"Missing directory: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {full_path}")
    
    if all_exist:
        logger.info("Verification successful: All directories exist.")
    else:
        logger.error("Verification failed: Some directories are missing.")
    return all_exist

def main():
    """Main entry point for directory setup."""
    # Determine the project root. 
    # Since this script is in code/, we go up one level.
    current_file = Path(__file__).resolve()
    base_path = current_file.parent.parent  # project root
    
    logger = init_pipeline_logging("setup_data_dirs", base_path / "logs")
    
    logger.info(f"Project root identified at: {base_path}")
    
    create_data_directories(base_path)
    success = verify_data_directories(base_path)
    
    if not success:
        sys.exit(1)
    else:
        print("Directory setup complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()