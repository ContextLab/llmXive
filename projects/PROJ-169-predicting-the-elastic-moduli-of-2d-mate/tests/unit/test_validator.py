"""Unit tests for the runtime source enforcement in validator.py."""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest.validator import (
    enforce_single_source,
    reset_source_lock,
    get_active_source,
    _STATE_FILE_PATH,
    get_project_root
)


class TestSourceEnforcement:
    """Tests for the single source enforcement logic."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset the global state before and after each test."""
        reset_source_lock()
        yield
        reset_source_lock()

    def test_first_source_activation(self):
        """Test that the first source activation succeeds and persists state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the project root and state file path for this test
            # We need to patch get_project_root and the state file path
            # Since these are module-level globals, we'll test the logic directly
            # by creating a temporary state file and checking behavior.

            # For this test, we assume the state file doesn't exist yet.
            # We just check that the function doesn't raise and sets the lock.
            # Note: In a real scenario, the state file would be written to the project root.
            # Here we just verify the logic flow.
            
            # Since we can't easily mock the file path in the module without complex patching,
            # we test the in-process locking behavior which is independent of the file system.
            enforce_single_source("materials_project")
            assert get_active_source() == "materials_project"

    def test_same_source_reactivation(self):
        """Test that reactivating the same source is idempotent."""
        enforce_single_source("aflow")
        assert get_active_source() == "aflow"
        
        # Should not raise
        enforce_single_source("aflow")
        assert get_active_source() == "aflow"

    def test_different_source_in_process_raises(self):
        """Test that activating a different source in the same process raises SystemExit."""
        enforce_single_source("materials_project")
        
        with pytest.raises(SystemExit) as exc_info:
            enforce_single_source("aflow")
        
        assert exc_info.value.code == 1

    def test_invalid_source_raises_value_error(self):
        """Test that an invalid source name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            enforce_single_source("invalid_source")
        
        assert "Invalid source name" in str(exc_info.value)

    def test_state_file_persistence_logic(self, tmp_path):
        """Test the cross-run state file logic by simulating file presence."""
        # This test simulates the scenario where a state file exists with a different source.
        # We need to mock the file operations or create a controlled environment.
        
        # Since the function uses hardcoded paths relative to the module,
        # we will test the logic by temporarily modifying the global state
        # and simulating the file check behavior.
        
        # We'll create a temporary directory and simulate the state file
        original_get_root = get_project_root
        
        def mock_get_root():
            return tmp_path
        
        # Patch the function temporarily
        import ingest.validator as validator_module
        validator_module.get_project_root = mock_get_root
        
        try:
            # Create a state file with a different source
            state_file = tmp_path / "data" / ".source_state"
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                json.dump({"source": "aflow"}, f)
            
            # Now try to activate a different source - should fail
            with pytest.raises(SystemExit) as exc_info:
                enforce_single_source("materials_project")
            
            assert exc_info.value.code == 1
        finally:
            # Restore original function
            validator_module.get_project_root = original_get_root

    def test_state_file_with_same_source(self, tmp_path):
        """Test that activating the same source as in state file succeeds."""
        original_get_root = get_project_root
        
        def mock_get_root():
            return tmp_path
        
        import ingest.validator as validator_module
        validator_module.get_project_root = mock_get_root
        
        try:
            # Create a state file with the same source
            state_file = tmp_path / "data" / ".source_state"
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                json.dump({"source": "materials_project"}, f)
            
            # Should succeed
            enforce_single_source("materials_project")
            assert get_active_source() == "materials_project"
        finally:
            validator_module.get_project_root = original_get_root