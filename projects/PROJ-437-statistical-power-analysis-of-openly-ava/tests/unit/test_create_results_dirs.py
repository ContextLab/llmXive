"""
Unit tests for the create_results_dirs module (T001d).
"""
import os
import tempfile
from pathlib import Path
import pytest
from code.data_setup.create_results_dirs import create_results_directories


def test_create_results_directories_creates_folders():
    """
    Test that create_results_directories creates the expected folder structure.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Run the function
        create_results_directories(tmp_dir)
        
        root_path = Path(tmp_dir).resolve()
        results_dir = root_path / "results"
        paper_dir = results_dir / "paper"
        
        # Assert directories exist
        assert results_dir.exists(), "results/ directory was not created"
        assert results_dir.is_dir(), "results/ is not a directory"
        assert paper_dir.exists(), "results/paper/ directory was not created"
        assert paper_dir.is_dir(), "results/paper/ is not a directory"
        
        # Assert .gitkeep exists
        gitkeep = paper_dir / ".gitkeep"
        assert gitkeep.exists(), ".gitkeep file was not created in results/paper/"


def test_create_results_directories_idempotent():
    """
    Test that running the function twice does not raise an error.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Run twice
        create_results_directories(tmp_dir)
        create_results_directories(tmp_dir)
        
        root_path = Path(tmp_dir).resolve()
        assert (root_path / "results").exists()
        assert (root_path / "results" / "paper").exists()