import os
import stat
import tempfile
import shutil
from pathlib import Path
import sys
import pytest

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_permissions import set_restricted_permissions

class TestPermissions:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing permissions."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_set_restricted_permissions_data_insufficient(self, temp_dir):
        """Test that 'Data Insufficient' mode sets 555 permissions."""
        # Simulate the mode logic by passing the mode directly
        # We can't easily mock the global get_mode_flag without refactoring,
        # so we test the core logic of the function if we can expose it,
        # or we test the behavior by passing a specific mode argument if we modify the function.
        # For this test, we will assume the function `set_restricted_permissions` 
        # takes a mode argument for testing purposes (as defined in the implementation above).
        
        # Force the mode to 'Data Insufficient'
        set_restricted_permissions(temp_dir, mode="Data Insufficient")
        
        current_mode = os.stat(str(temp_dir)).st_mode & 0o777
        expected_mode = 0o555
        
        assert current_mode == expected_mode, f"Expected {oct(expected_mode)}, got {oct(current_mode)}"
        
    def test_set_restricted_permissions_primary(self, temp_dir):
        """Test that 'Primary' mode sets 755 permissions."""
        set_restricted_permissions(temp_dir, mode="Primary")
        
        current_mode = os.stat(str(temp_dir)).st_mode & 0o777
        expected_mode = 0o755
        
        assert current_mode == expected_mode, f"Expected {oct(expected_mode)}, got {oct(current_mode)}"
        
    def test_set_restricted_permissions_underpowered(self, temp_dir):
        """Test that 'Underpowered' mode sets 555 permissions."""
        set_restricted_permissions(temp_dir, mode="Underpowered")
        
        current_mode = os.stat(str(temp_dir)).st_mode & 0o777
        expected_mode = 0o555
        
        assert current_mode == expected_mode, f"Expected {oct(expected_mode)}, got {oct(current_mode)}"
