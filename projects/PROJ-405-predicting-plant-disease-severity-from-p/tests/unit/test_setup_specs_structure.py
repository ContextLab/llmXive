import pytest
from pathlib import Path
import tempfile
import shutil
import os

from setup_specs_structure import create_specs_directories

class TestCreateSpecsDirectories:
    """
    Unit tests for the specs directory creation logic.
    """

    def test_creates_feature_root(self, tmp_path):
        """Verify the main feature directory is created."""
        feature_root = tmp_path / "specs" / "001-predict-plant-disease-severity"
        result = create_specs_directories(tmp_path)
        
        assert feature_root.exists()
        assert feature_root.is_dir()
        assert str(feature_root) in result

    def test_creates_contracts_subdirectory(self, tmp_path):
        """Verify the contracts subdirectory is created."""
        contracts_dir = tmp_path / "specs" / "001-predict-plant-disease-severity" / "contracts"
        result = create_specs_directories(tmp_path)
        
        assert contracts_dir.exists()
        assert contracts_dir.is_dir()
        assert str(contracts_dir) in result

    def test_creates_designs_subdirectory(self, tmp_path):
        """Verify the designs subdirectory is created."""
        designs_dir = tmp_path / "specs" / "001-predict-plant-disease-severity" / "designs"
        result = create_specs_directories(tmp_path)
        
        assert designs_dir.exists()
        assert designs_dir.is_dir()
        assert str(designs_dir) in result

    def test_creates_notes_subdirectory(self, tmp_path):
        """Verify the notes subdirectory is created."""
        notes_dir = tmp_path / "specs" / "001-predict-plant-disease-severity" / "notes"
        result = create_specs_directories(tmp_path)
        
        assert notes_dir.exists()
        assert notes_dir.is_dir()
        assert str(notes_dir) in result

    def test_idempotent_creation(self, tmp_path):
        """Verify running the function twice does not raise errors."""
        create_specs_directories(tmp_path)
        # Should not raise
        create_specs_directories(tmp_path)
        
        feature_root = tmp_path / "specs" / "001-predict-plant-disease-severity"
        assert feature_root.exists()