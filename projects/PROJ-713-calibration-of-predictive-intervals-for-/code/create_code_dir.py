"""
Utility script to create the `code/` directory idempotently and verify
write access. Used by task T001a.
"""

import os
from pathlib import Path
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def create_and_verify_code_dir() -> None:
    """
    Create the `code/` directory (parents=True, exist_ok=True) and assert
    that it is writable. Raises an AssertionError if the directory cannot be
    written to.
    """
    code_dir = Path(__file__).resolve().parent
    # Ensure we are operating on the top‑level `code` folder
    # (the script lives inside that folder, so its parent is the project root)
    # and the target directory is the sibling `code` directory.
    target_dir = code_dir.parent / "code"
    target_dir.mkdir(parents=True, exist_ok=True)

    if not os.access(target_dir, os.W_OK):
        raise PermissionError(f"Directory not writable: {target_dir}")

    log.info(f"Verified writable code directory at {target_dir}")

if __name__ == "__main__":
    create_and_verify_code_dir()
