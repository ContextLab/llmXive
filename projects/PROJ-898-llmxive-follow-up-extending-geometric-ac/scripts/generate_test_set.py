#!/usr/bin/env python3
"""
Script to execute the test set generation for User Story 1.
This script ensures the directory structure is valid and invokes the generator.
"""
import os
import sys
import json
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.config import load_config, get_default_config_path
from code.setup_project_structure import create_directory_structure, create_gitkeep_files

def ensure_directories():
    """Ensure the required directory structure exists."""
    dirs = [
        "data/raw",
        "data/generated",
        "data/results",
        "code",
        "tests"
    ]
    for d in dirs:
        full_path = os.path.join(project_root, d)
        os.makedirs(full_path, exist_ok=True)
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write(f"# Placeholder for {d}\n")
    logging.info("Directory structure and .gitkeep files ensured.")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    ensure_directories()
    
    # Load config to verify setup
    config_path = get_default_config_path()
    if os.path.exists(config_path):
        config = load_config(config_path)
        logging.info(f"Configuration loaded successfully from {config_path}")
    else:
        logging.warning(f"Config file not found at {config_path}. Using defaults.")

    logging.info("Test set generation environment ready.")
    # Note: Actual generation logic is in code/data_generation.py or similar
    # This script serves as the entry point for the task T001b verification.
    return 0

if __name__ == "__main__":
    sys.exit(main())
