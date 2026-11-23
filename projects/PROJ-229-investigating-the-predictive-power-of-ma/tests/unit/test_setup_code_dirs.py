"""
Unit tests for the code directory creation script (T001b).
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the function to test
from code.setup_code_dirs import create_code_directories

def test_create_code_directories():
    """Test that create_code_directories creates the expected folders."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Ensure the 'code' parent exists if we are creating relative paths
        # The function expects to create 'code/data', etc. relative to base_path
        # But our function logic creates 'code/data' inside base_path.
        # So we need to make sure 'code' is not required to exist beforehand if 
        # the function handles parent creation, or we create it.
        # The function uses mkdir(parents=True), so it should work.
        
        created = create_code_directories(base_path)
        
        expected_dirs = [
            "code/data",
            "code/models",
            "code/utils"
        ]
        
        assert len(created) == 3
        
        for dir_str in expected_dirs:
            full_path = base_path / dir_str
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

def test_create_code_directories_idempotent():
    """Test that running the function twice does not raise errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # First run
        create_code_directories(base_path)
        
        # Second run
        try:
            create_code_directories(base_path)
        except Exception as e:
            pytest.fail(f"Idempotent run failed: {e}")