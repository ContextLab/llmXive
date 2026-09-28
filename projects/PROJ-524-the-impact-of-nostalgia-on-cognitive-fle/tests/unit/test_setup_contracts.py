import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_contracts import create_contracts_directory, main
from config import get_config

def test_create_contracts_directory_creates_dir():
    """
    Test that create_contracts_directory creates the directory if it doesn't exist.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_contracts_path = Path(tmpdir) / "contracts"
        
        # Mock config to point to temp dir
        config = {"contracts_dir": str(test_contracts_path)}
        
        # Ensure it doesn't exist first
        assert not test_contracts_path.exists()
        
        # Run the function
        result = create_contracts_directory(config)
        
        # Verify
        assert result is True
        assert test_contracts_path.exists()
        assert test_contracts_path.is_dir()

def test_create_contracts_directory_existing_dir():
    """
    Test that create_contracts_directory handles existing directory gracefully.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_contracts_path = Path(tmpdir) / "contracts"
        
        # Create it first
        test_contracts_path.mkdir()
        assert test_contracts_path.exists()
        
        # Mock config
        config = {"contracts_dir": str(test_contracts_path)}
        
        # Run the function
        result = create_contracts_directory(config)
        
        # Verify it returns True and directory still exists
        assert result is True
        assert test_contracts_path.exists()

def test_main_returns_success():
    """
    Test that main() returns 0 on success.
    """
    # We assume standard config works in the test environment
    # This is a basic smoke test
    result = main()
    assert result == 0
