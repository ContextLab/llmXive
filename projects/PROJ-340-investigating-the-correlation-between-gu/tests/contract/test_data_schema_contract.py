"""
Contract test for the data directory structure.
Ensures the project adheres to the defined directory layout contract.
"""
import os
import pytest
from pathlib import Path


def test_data_directory_contract():
    """
    Contract test: The project MUST have a data/ directory with specific subdirectories.
    
    Contract Requirements:
    - data/raw/
    - data/processed/
    - data/results/
    - data/config/
    """
    required_structure = {
        "data": ["raw", "processed", "results", "config"]
    }

    for base, children in required_structure.items():
        base_path = Path(base)
        assert base_path.exists(), f"Contract violation: {base} directory missing"
        assert base_path.is_dir(), f"Contract violation: {base} is not a directory"

        for child in children:
            child_path = base_path / child
            assert child_path.exists(), f"Contract violation: {child_path} directory missing"
            assert child_path.is_dir(), f"Contract violation: {child_path} is not a directory"
