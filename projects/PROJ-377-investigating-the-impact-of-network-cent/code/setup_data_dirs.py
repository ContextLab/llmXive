"""
Utility script to set up data directories.

Creates the necessary directory structure for the project.
"""

import os
from pathlib import Path

def setup_data_directories():
    """
    Create the project's data directory structure.
    
    Creates:
        - data/raw: Raw downloaded data
        - data/processed: Processed data ready for analysis
        - data/artifacts: Final analysis outputs
        - data/processed/connectivity: Connectivity matrices
        - data/processed/centrality: Centrality metrics
        - data/processed/behavioral: Behavioral metrics
        - data/processed/regression: Regression results
        - data/processed/validation: Validation results
    """
    base_dir = Path("data")
    
    directories = [
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "artifacts",
        base_dir / "processed" / "connectivity",
        base_dir / "processed" / "centrality",
        base_dir / "processed" / "behavioral",
        base_dir / "processed" / "regression",
        base_dir / "processed" / "validation",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")
    
    return directories

if __name__ == "__main__":
    setup_data_directories()