import os
import tempfile
import pytest
from code.setup_directories import create_directories

def test_create_directories_creates_expected_structure():
    """Test that create_directories creates all required directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create directories
        created = create_directories(tmp_dir)
        
        # Check that all expected directories exist
        expected_dirs = [
            "data",
            "results",
            "models",
            "contracts",
            "data/raw",
            "data/processed",
            "results/plots",
            "results/logs",
            "models/checkpoints",
            "contracts/schemas"
        ]
        
        for rel_path in expected_dirs:
            full_path = os.path.join(tmp_dir, rel_path)
            assert os.path.exists(full_path), f"Directory {full_path} was not created"
            assert os.path.isdir(full_path), f"{full_path} is not a directory"

def test_create_directories_idempotent():
    """Test that running create_directories twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # First run
        created_first = create_directories(tmp_dir)
        
        # Second run
        created_second = create_directories(tmp_dir)
        
        # Should not raise any errors
        assert len(created_first) > 0
        assert len(created_second) == 0  # No new dirs created on second run

def test_create_directories_custom_root():
    """Test that create_directories works with a custom root directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        custom_root = os.path.join(tmp_dir, "custom_project")
        os.makedirs(custom_root)
        
        created = create_directories(custom_root)
        
        # Verify directories are created under custom_root
        assert any(custom_root in path for path in created)
        
        # Check one specific directory
        data_dir = os.path.join(custom_root, "data")
        assert os.path.exists(data_dir)

def test_create_directories_returns_list():
    """Test that create_directories returns a list of paths."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        result = create_directories(tmp_dir)
        
        assert isinstance(result, list)
        assert all(isinstance(path, str) for path in result)