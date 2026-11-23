"""
Project directory setup utility for the Meta-Analysis of Trust Perception in Deepfake Facial Stimuli.

This module ensures the existence of all required data and results directories
as defined in the project structure plan.
"""
import os
from pathlib import Path


def setup_directories():
    """
    Create the required directory structure for the project.
    
    Creates the following directories relative to the project root:
    - data/search_results/
    - data/screening/
    - data/harmonized/
    - results/
    
    Returns:
        Path: The project root path.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "data/search_results",
        "data/screening",
        "data/harmonized",
        "results"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {full_path}")
    
    return project_root


if __name__ == "__main__":
    root = setup_directories()
    print(f"Project structure initialized at: {root}")
