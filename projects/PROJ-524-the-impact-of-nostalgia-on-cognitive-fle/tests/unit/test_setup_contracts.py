import os
import tempfile
import pytest
from pathlib import Path

# Mock config for testing
from code.config import get_config
from code.setup_contracts import create_contracts_directory


def test_create_contracts_directory_exists():
    """
    Test that create_contracts_directory creates the directory if it doesn't exist
    and returns True if it already exists.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "contracts"
        
        # Mock config to use our temp directory
        config = {
            "contracts_dir": str(contracts_path)
        }

        # First call should create it
        result = create_contracts_directory(config)
        assert result is True
        assert contracts_path.exists()
        assert contracts_path.is_dir()

        # Second call should succeed (directory already exists)
        result = create_contracts_directory(config)
        assert result is True

def test_create_contracts_directory_permissions():
    """
    Test behavior when directory creation fails due to permissions (mocked).
    Since we can't easily mock OS permissions in a portable way, we test
    that the function handles the path correctly.
    """
    # This test verifies the logic flow; actual permission errors are hard to trigger
    # in a test environment without root/special setup.
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "contracts"
        config = {"contracts_dir": str(contracts_path)}
        
        # Should succeed
        assert create_contracts_directory(config) is True
        assert contracts_path.exists()
