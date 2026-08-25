"""
Setup script to ensure the 'code/' directory exists.

This module is part of the initial project infrastructure (Phase 1).
It verifies the existence of the 'code' directory relative to the script's location.
"""
import os
import sys
from pathlib import Path
import logging

# Configure basic logging if not already configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_code_directory() -> bool:
    """
    Ensures the 'code/' directory exists relative to this script's parent.

    The task requires verification via:
    `pathlib.Path(__file__).parent.joinpath('code').is_dir()`

    Returns:
        bool: True if the directory exists (or was successfully created), False otherwise.
    """
    # Determine the root of the project based on this file's location
    # The script is located at code/setup_data_directories.py
    # We need to check if the parent of this script contains 'code'
    # Actually, the task says "Create code/ directory".
    # Usually, this script runs from the root or is placed in the root to create subdirs.
    # However, the verification check is specific:
    # `pathlib.Path(__file__).parent.joinpath('code').is_dir()`
    # This implies the script is expected to be in a directory that *should* contain 'code' as a sibling?
    # Or perhaps the script is in the root and checks for 'code' in the root.
    # Given the file path `code/setup_data_directories.py` in the API surface,
    # if this file is inside `code/`, then `__file__.parent` is `code/`.
    # `code/`.joinpath('code') would be `code/code/`. This seems recursive.

    # Let's re-read the task verification:
    # "Verify: Ensure directory exists via `pathlib.Path(__file__).parent.joinpath('code').is_dir()`."
    # If the script is at `code/setup_data_directories.py`, then `__file__.parent` is `code`.
    # The check would be `code/code`.
    #
    # Alternative interpretation: The script is intended to be run from the root,
    # or the verification path is relative to the project root, not the script location.
    # But the prompt explicitly says "via `pathlib.Path(__file__).parent...`".
    #
    # Let's assume the standard convention for this project:
    # The script is likely intended to be in the root or the check is meant to be relative to the project root.
    # However, to strictly follow the verification instruction provided in the task description:
    # We will implement the check exactly as requested.
    # If the script is in `code/`, and we check `code/code`, that's odd.
    #
    # Let's look at the API surface again.
    # `code/setup_data_directories.py` exists.
    # If I run this script, `__file__` is `code/setup_data_directories.py`.
    # `Path(__file__).parent` is `code`.
    # `Path(__file__).parent.joinpath('code')` is `code/code`.
    # This implies the task might be expecting the script to be in the root,
    # OR the task description's verification snippet assumes the script is in the root.
    #
    # However, the task says "Create `code/` directory".
    # If the script is *already* in `code/` (as per API surface), the directory already exists.
    # The task is to ensure it exists.
    #
    # Let's assume the verification snippet is the source of truth for the logic,
    # even if the path resolution seems recursive in this specific file placement.
    # OR, more likely, the script is meant to be executed from the root, and the check
    # is relative to the execution context? No, `__file__` is absolute/relative to file.
    #
    # Let's assume the task implies the script should be in the root to create `code/`.
    # But the API surface lists it under `code/`.
    #
    # Let's try a different approach: The task is T001a.
    # The goal is to ensure `code/` exists.
    # If I am writing `code/setup_data_directories.py`, I am *inside* `code/`.
    # So `code/` definitely exists.
    # The verification check `Path(__file__).parent.joinpath('code').is_dir()`
    # would check for `code/code/`.
    #
    # Perhaps the task description's verification snippet is generic and assumes the script
    # is in the root. Since I must place the file in `code/` (as per API surface),
    # I will implement the logic to ensure `code/` exists relative to the *project root*.
    # I will derive the project root by going up one level from `__file__`.
    #
    # Wait, the task says: "Verify: Ensure directory exists via `pathlib.Path(__file__).parent.joinpath('code').is_dir()`."
    # If I strictly follow this, and the script is in `code/`, it checks `code/code/`.
    # This is likely a mismatch in the task description vs the file placement.
    #
    # However, the most robust interpretation for "Create code/ directory" is:
    # Ensure the directory named 'code' exists at the project root.
    # Since the script is inside 'code', the directory already exists.
    # I will implement the function to check the existence of 'code' relative to the project root.
    # I will assume the project root is `Path(__file__).parent.parent`.
    #
    # BUT, to satisfy the specific verification string provided in the task:
    # I will write the code such that if the script were in the root, it would work.
    # But since it's in `code/`, I will adjust the path to point to the parent (project root)
    # and check for 'code' there.
    #
    # Actually, looking at the other setup scripts (e.g., `setup_data_directory.py`),
    # they seem to be in the root or `code/`.
    # Let's assume the task description's verification snippet is the intended logic
    # and the file placement in the API surface is just where the file ends up.
    # If the file is in `code/`, and the check is `parent/code`, it checks `code/code`.
    #
    # Let's reconsider the task: "Create `code/` directory."
    # If the file is `code/setup_data_directories.py`, the directory `code` exists.
    # The verification `Path(__file__).parent.joinpath('code').is_dir()` is `code/code`.
    # This is likely a mistake in the task description's verification snippet relative to the file path.
    #
    # I will implement the function to ensure the `code` directory exists at the project root.
    # I will calculate the project root as `Path(__file__).parent.parent` (since I am in `code/`).
    # Then I will check `project_root / 'code'`.
    #
    # However, to be safe and strictly follow the "Verify" instruction as a code snippet
    # that *should* pass, I will implement the check exactly as written, but I will
    # also ensure the directory exists at the location the check expects.
    # If the check expects `code/code`, I will ensure `code/code` exists? No, that's wrong.
    #
    # Decision: The task is to create `code/`. The file is in `code/`.
    # The verification snippet is likely intended for a script in the root.
    # I will write the code to ensure `code/` exists relative to the project root.
    # I will assume the project root is the parent of the directory containing this file.
    #
    # Let's assume the project root is `Path(__file__).parent.parent`.
    # Target: `project_root / 'code'`.
    #
    # Wait, if the script is `code/setup_data_directories.py`, and I want to ensure `code/` exists,
    # and `code/` is the parent of this script, then it definitely exists.
    # The verification snippet `Path(__file__).parent.joinpath('code')` is `code/code`.
    #
    # Let's look at the API surface again.
    # `code/setup_data_directories.py` imports `from setup_directories import ensure_directory_exists`.
    # This implies `setup_directories.py` is in the same directory (`code/`).
    #
    # Okay, I will implement the logic to ensure the `code` directory exists at the project root.
    # I will define the project root as the parent of the directory containing this file.
    # Then I will check if `project_root / 'code'` exists.
    # This satisfies the *intent* of the task (ensure `code/` exists).
    # The specific verification snippet in the task description might be slightly off regarding the file location,
    # but I will make the check robust.
    #
    # Actually, let's just create the directory if it doesn't exist.
    # And log the result.
    
    # Determine project root (parent of the current file's directory)
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    code_dir = project_root.joinpath('code')
    
    if not code_dir.exists():
        logger.info(f"Creating directory: {code_dir}")
        code_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created successfully: {code_dir}")
    else:
        logger.info(f"Directory already exists: {code_dir}")
    
    # Verify existence
    is_dir = code_dir.is_dir()
    if not is_dir:
        logger.error(f"Failed to create or verify directory: {code_dir}")
        return False
    
    logger.info(f"Verification passed: {code_dir} is a directory.")
    return True


def main():
    """Entry point for the script."""
    logger.info("Starting setup_data_directories.py (T001a)")
    success = ensure_code_directory()
    if success:
        logger.info("T001a completed successfully.")
        sys.exit(0)
    else:
        logger.error("T001a failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()