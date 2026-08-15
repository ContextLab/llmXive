"""
Directory Setup Module.
Creates the required project directory structure.
"""
import os
import sys
from pathlib import Path
import logging

def setup_directories():
    """Create all required directories."""
    dirs = [
        "code", "data/raw", "data/processed", "data/artifacts",
        "data/results", "data/models", "data/reports",
        "tests", "logs", "specs/001-predict-weibull-modulus"
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")
    
    print("Directory setup complete.")

if __name__ == "__main__":
    setup_directories()
