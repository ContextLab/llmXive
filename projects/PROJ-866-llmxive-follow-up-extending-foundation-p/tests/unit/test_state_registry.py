import os
import sys
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to test the update_state_registry logic
# Since we can't easily import the function if it's in a new file not in sys.path
# we will import it directly from the module we created
from utils.update_state_registry import update_state_registry, compute_sha256, STATE_FILE, DATA_RAW_DIR

class TestStateRegistry:
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        
        # Create a mock project structure
        (self.test_dir / "state" / "projects").mkdir(parents=True, exist_ok=True)
        (self.test_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Create a mock state file
        self.mock_state_file = self.test_dir / "state" / "projects" / "PROJ-866-test.yaml"
        state_data = {
            "project_id": "PROJ-866-test",
            "created_at": "2023-01-01T00:00:00Z",
            "artifact_hashes": {}
        }
        with open(self.mock_state_file, "w") as f:
            yaml.dump(state_data, f)
        
        # Create some mock data files
        (self.test_dir / "data" / "raw" / "workflow_1.json").write_text('{"id": 1}')
        (self.test_dir / "data" / "raw" / "workflow_2.json").write_text('{"id": 2}')

    def teardown_method(self):
        """Tear down test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_compute_sha256(self):
        """Test SHA256 computation."""
        file_path = self.test_dir / "data" / "raw" / "workflow_1.json"
        hash_val = compute_sha256(file_path)
        assert len(hash_val) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in hash_val)

    def test_update_state_registry(self, monkeypatch):
        """Test that update_state_registry updates the state file correctly."""
        # Monkeypatch the constants to point to our test files
        monkeypatch.setattr("utils.update_state_registry.STATE_FILE", self.mock_state_file)
        monkeypatch.setattr("utils.update_state_registry.DATA_RAW_DIR", self.test_dir / "data" / "raw")
        monkeypatch.setattr("utils.update_state_registry.PROJECT_ID", "PROJ-866-test")

        # Run the update
        update_state_registry()

        # Verify the state file was updated
        with open(self.mock_state_file, "r") as f:
            state_data = yaml.safe_load(f)

        assert "artifact_hashes" in state_data
        assert len(state_data["artifact_hashes"]) == 2
        assert "data/raw/workflow_1.json" in state_data["artifact_hashes"]
        assert "data/raw/workflow_2.json" in state_data["artifact_hashes"]
        assert "updated_at" in state_data
        assert "last_operation" in state_data
        assert state_data["last_operation"] == "update_state_registry"

    def test_update_state_registry_empty_dir(self, monkeypatch):
        """Test update when data/raw is empty."""
        # Remove files
        (self.test_dir / "data" / "raw").unlink()
        (self.test_dir / "data" / "raw").mkdir()
        
        monkeypatch.setattr("utils.update_state_registry.STATE_FILE", self.mock_state_file)
        monkeypatch.setattr("utils.update_state_registry.DATA_RAW_DIR", self.test_dir / "data" / "raw")
        monkeypatch.setattr("utils.update_state_registry.PROJECT_ID", "PROJ-866-test")

        update_state_registry()

        with open(self.mock_state_file, "r") as f:
            state_data = yaml.safe_load(f)

        assert state_data["artifact_hashes"] == {}

    def test_update_state_registry_missing_file(self, monkeypatch):
        """Test update when state file is missing."""
        # Remove state file
        self.mock_state_file.unlink()
        
        monkeypatch.setattr("utils.update_state_registry.STATE_FILE", self.mock_state_file)
        monkeypatch.setattr("utils.update_state_registry.DATA_RAW_DIR", self.test_dir / "data" / "raw")
        monkeypatch.setattr("utils.update_state_registry.PROJECT_ID", "PROJ-866-test")

        with pytest.raises(SystemExit):
            update_state_registry()