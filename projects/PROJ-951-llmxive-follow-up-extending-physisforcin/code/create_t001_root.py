"""
create_t001_root.py
--------------------
Script to create the top‑level project code directory for the
PROJ‑951‑llmxive‑follow‑up‑extending‑physisforcin project.

The required directory is:
    projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/

The script is idempotent: if the directory already exists it will be left
untouched, and any pre‑existing contents will be removed so that the
directory is empty, satisfying the “empty directory” requirement.
"""

import os
import sys
from pathlib import Path
import shutil
import logging

# Set up a minimal logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    """
    Create the required empty project code directory.

    If the directory already exists, it is cleared of all contents to
    guarantee emptiness.
    """
    target_dir = Path(
        "projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code"
    ).resolve()

    logger.info("Ensuring directory exists: %s", target_dir)

    # Create parent directories if they do not exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Remove any existing contents to guarantee emptiness
    for item in target_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
            logger.debug("Removed directory: %s", item)
        else:
            item.unlink()
            logger.debug("Removed file: %s", item)

    logger.info("Directory %s is now empty.", target_dir)

if __name__ == "__main__":
    main()
