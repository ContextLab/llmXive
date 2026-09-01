import os
from pathlib import Path
import pytest

from code.config import DATA_DIR, ERRORS_DIR, MODELS_DIR, REPORTS_DIR, LOG_DIR
from code.setup_data_dirs import create_directories
from code.data.checksum import generate_checksums


def test_data_directory_structure(tmp_path, monkeypatch):
    """Integration test: Verify complete data directory structure."""
    # Setup tmp paths
    monkeypatch.setattr("code.config.DATA_DIR", tmp_path / "data")
    monkeypatch.setattr("code.config.ERRORS_DIR", tmp_path / "errors")
    monkeypatch.setattr("code.config.MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr("code.config.REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr("code.config.LOG_DIR", tmp_path / "logs")
    
    # Re-import
    import importlib
    import code.setup_data_dirs
    importlib.reload(code.setup_data_dirs)
    
    # Create directories
    code.setup_data_dirs.create_directories()
    
    # Verify structure
    required_dirs = [
        tmp_path / "data" / "raw",
        tmp_path / "data" / "curated",
        tmp_path / "data" / "artifacts",
        tmp_path / "data" / "logs",
        tmp_path / "errors",
        tmp_path / "models",
        tmp_path / "reports",
        tmp_path / "logs",
    ]
    
    for directory in required_dirs:
        assert directory.exists(), f"Directory missing: {directory}"
        assert directory.is_dir(), f"Not a directory: {directory}"


def test_checksum_integration(tmp_path, monkeypatch):
    """Integration test: Verify checksum generation works with data structure."""
    # Setup tmp paths
    data_dir = tmp_path / "data"
    monkeypatch.setattr("code.config.DATA_DIR", data_dir)
    monkeypatch.setattr("code.config.ERRORS_DIR", tmp_path / "errors")
    monkeypatch.setattr("code.config.MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr("code.config.REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr("code.config.LOG_DIR", tmp_path / "logs")
    
    # Re-import
    import importlib
    import code.setup_data_dirs
    import code.data.checksum
    importlib.reload(code.setup_data_dirs)
    importlib.reload(code.data.checksum)
    
    # Create directories
    code.setup_data_dirs.create_directories()
    
    # Create a test file
    test_file = data_dir / "raw" / "test.csv"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("col1,col2\n1,2\n3,4")
    
    # Generate checksums
    checksums = code.data.checksum.generate_checksums(data_dir)
    
    # Verify checksum was generated
    assert len(checksums) > 0
    assert "raw/test.csv" in checksums
    
    # Verify checksum is valid hex
    checksum_value = checksums["raw/test.csv"]
    assert all(c in '0123456789abcdef' for c in checksum_value)
    assert len(checksum_value) == 64  # SHA256 produces 64 hex chars
