"""
Directory setup script for the Residue Distribution of Euler's Totient Function project.
Creates the essential directory structure required for the pipeline.
"""
import os
from pathlib import Path


def setup_directories():
    """
    Creates the root directory structure: code/, data/, results/, tests/.
    This function ensures the foundational folders exist for the project.
    """
    root = Path(".")
    
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "results",
        "results/plots",
        "results/reports",
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {full_path}")

    return True