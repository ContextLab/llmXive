import os
import sys
import logging
from pathlib import Path

from config import ensure_dirs, get_config

def main():
    """
    Create required project directories.
    This script is used to initialize the data directory structure.
    """
    config = get_config()
    
    # Define directories to create based on project requirements
    # T001a: data/raw/ (already done per task list, but ensuring existence)
    # T001b: data/processed/
    # T001c: data/results/
    # T001e: data/stimuli/
    
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/stimuli"
    ]
    
    for dir_path in dirs_to_create:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {full_path}")
        else:
            logging.info(f"Directory already exists: {full_path}")

    # Ensure code and tests __init__.py exist if they don't
    code_init = Path("code/__init__.py")
    if not code_init.exists():
        code_init.touch()
        logging.info(f"Created {code_init}")
        
    tests_init = Path("tests/__init__.py")
    if not tests_init.exists():
        tests_init.touch()
        logging.info(f"Created {tests_init}")

    # Ensure README.md exists
    readme = Path("README.md")
    if not readme.exists():
        readme.write_text("# The Impact of Nostalgia on Cognitive Flexibility in Aging Adults\n\nThis project investigates the effect of nostalgia on cognitive flexibility in older adults.\n")
        logging.info(f"Created {readme}")

    logging.info("Directory structure initialization complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()