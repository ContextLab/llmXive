import pytest
import os
from pathlib import Path
import tempfile
import shutil

from code.utils.directories import create_all_directories, create_results_directories
from code.utils.config import get_project_root

class TestDirectoryCreation:
    """Unit tests for directory creation utilities."""

    def test_create_results_directories_structure(self, tmp_path):
        """Test that create_results_directories creates the required T001d structure."""
        # Create a temporary project root
        test_root = tmp_path / "test_project"
        test_root.mkdir()
        
        # Call the function with the temp root
        create_results_directories(test_root)
        
        # Verify the required directories exist
        required_dirs = [
            "results",
            "results/reports",
            "results/plots",
            "results/baseline",
            "results/predictions"
        ]
        
        for rel_path in required_dirs:
            full_path = test_root / rel_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_create_all_directories_comprehensive(self, tmp_path):
        """Test that create_all_directories creates the full project structure."""
        test_root = tmp_path / "full_project"
        test_root.mkdir()
        
        create_all_directories(test_root)
        
        # Check code structure
        code_dirs = ["code", "code/data", "code/models", "code/eval", "code/utils"]
        for d in code_dirs:
            assert (test_root / d).exists(), f"Missing code dir: {d}"
        
        # Check data structure
        data_dirs = ["data/raw", "data/processed", "data/splits", "data/schemas"]
        for d in data_dirs:
            assert (test_root / d).exists(), f"Missing data dir: {d}"
        
        # Check tests structure
        test_dirs = ["tests/contract", "tests/unit", "tests/integration"]
        for d in test_dirs:
            assert (test_root / d).exists(), f"Missing tests dir: {d}"
        
        # Check results structure (T001d)
        results_dirs = ["results/reports", "results/plots", "results/baseline", "results/predictions"]
        for d in results_dirs:
            assert (test_root / d).exists(), f"Missing results dir: {d}"
        
        # Check logs
        assert (test_root / "logs").exists(), "Missing logs dir"

    def test_create_all_directories_idempotent(self, tmp_path):
        """Test that calling create_all_directories multiple times does not fail."""
        test_root = tmp_path / "idempotent_test"
        test_root.mkdir()
        
        # Create once
        create_all_directories(test_root)
        
        # Create again - should not raise
        create_all_directories(test_root)
        
        # Verify structure still intact
        assert (test_root / "results/reports").exists()
        assert (test_root / "results/predictions").exists()

    def test_create_results_directories_idempotent(self, tmp_path):
        """Test that create_results_directories is idempotent."""
        test_root = tmp_path / "idempotent_results"
        test_root.mkdir()
        
        create_results_directories(test_root)
        create_results_directories(test_root)
        
        assert (test_root / "results/reports").exists()
        assert (test_root / "results/plots").exists()
        assert (test_root / "results/baseline").exists()
        assert (test_root / "results/predictions").exists()