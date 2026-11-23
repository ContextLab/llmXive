"""
Tests for T001c: Verify .gitkeep files exist in data directories.
"""
import os
from pathlib import Path
import pytest

def test_gitkeep_in_data_raw():
    """Verify .gitkeep exists in data/raw/"""
    project_root = Path(__file__).resolve().parent.parent
    gitkeep_path = project_root / "data" / "raw" / ".gitkeep"
    
    assert gitkeep_path.exists(), f".gitkeep not found in {gitkeep_path.parent}"
    assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

def test_gitkeep_in_data_processed():
    """Verify .gitkeep exists in data/processed/"""
    project_root = Path(__file__).resolve().parent.parent
    gitkeep_path = project_root / "data" / "processed" / ".gitkeep"
    
    assert gitkeep_path.exists(), f".gitkeep not found in {gitkeep_path.parent}"
    assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"
