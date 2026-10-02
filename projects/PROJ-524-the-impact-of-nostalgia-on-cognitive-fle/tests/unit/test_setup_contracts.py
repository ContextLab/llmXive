import os
import pytest
from pathlib import Path
from code.setup_contracts import create_contracts_directory
from code.config import get_config

def test_create_contracts_directory_exists():
    """Verify that create_contracts_directory creates the contracts folder."""
    config = get_config()
    contracts_dir = Path(config.get("contracts_dir", "contracts"))
    
    # Ensure it doesn't exist before (optional, but good for idempotency check)
    if contracts_dir.exists():
        # If it exists, the function should still return True
        result = create_contracts_directory()
        assert result is True
        assert contracts_dir.is_dir()
    else:
        result = create_contracts_directory()
        assert result is True
        assert contracts_dir.is_dir()
        # Cleanup for test isolation if needed, though usually we leave it
        # os.rmdir(contracts_dir)

def test_contracts_dir_is_writable():
    """Verify the contracts directory is writable."""
    config = get_config()
    contracts_dir = Path(config.get("contracts_dir", "contracts"))
    
    assert contracts_dir.is_dir()
    
    # Try to create a temp file to verify write permissions
    test_file = contracts_dir / ".write_test"
    try:
        test_file.touch()
        assert test_file.exists()
        test_file.unlink()
    except Exception as e:
        pytest.fail(f"Contracts directory is not writable: {e}")