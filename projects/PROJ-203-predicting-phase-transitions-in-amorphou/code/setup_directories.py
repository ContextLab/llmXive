"""
T008: Setup directory structure for the project.

This script ensures the existence of required directories for data storage,
model artifacts, and documentation reports as defined in the project plan.

Directories created:
- data/raw/
- data/processed/
- models/
- docs/reports/

Usage:
    python code/setup_directories.py
"""

import os
from pathlib import Path

# Define the project root relative to this script's location
# Assuming this script is in code/, project root is one level up
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define relative paths to be created
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/logs",
    "models",
    "docs/reports",
    "docs/reports/shap_plots",
    "artifacts"
]

def setup_directories():
    """Create the required directory structure."""
    created_count = 0
    existing_count = 0
    
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        
        if full_path.exists():
            existing_count += 1
            continue
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            return False
    
    print(f"Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return True

if __name__ == "__main__":
    success = setup_directories()
    exit(0 if success else 1)
