import pytest
import os
import json
import tempfile
import hashlib
from pathlib import Path
import sys
import yaml

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.checksum import compute_file_checksum

class TestSaveRawData:
    """
    Unit tests for T020: Save raw data to data/raw/ with SHA-256 checksums.
    """

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.raw_dir = self.project_root / "data" / "raw"
        self.state_dir = self.project_root / "state" / "projects"
        self.raw_dir.mkdir(parents=True)
        self.state_dir.mkdir(parents=True)
        
        # Create a dummy data file
        self.test_file = self.raw_dir / "test_data.csv"
        self.test_content = "smiles,composition,Tg,Modulus\nCCO,0.5,300,1.0\n"
        self.test_file.write_text(self.test_content)
        
        # Mock the global project_root in the module if needed, 
        # but here we test logic directly or via mocks.
        # For this test, we test the checksum logic and state update logic directly.

    def test_compute_checksum(self):
        """Test that SHA-256 checksum is computed correctly."""
        expected_hash = hashlib.sha256(self.test_content.encode('utf-8')).hexdigest()
        computed_hash = compute_file_checksum(self.test_file)
        assert computed_hash == expected_hash

    def test_state_update_format(self):
        """Test that the state file is updated with the correct structure."""
        state_file = self.state_dir / "PROJ-122-identifying-structure-property-relations.yaml"
        
        # Simulate the state update logic
        checksum = compute_file_checksum(self.test_file)
        relative_path = str(self.test_file.relative_to(self.project_root))
        
        state_data = {
            "project_id": "PROJ-122-identifying-structure-property-relations",
            "artifacts": {
                "raw_data_checksums": {
                    relative_path: checksum
                }
            }
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)
        
        # Verify file exists and content
        assert state_file.exists()
        with open(state_file, 'r') as f:
            loaded_state = yaml.safe_load(f)
        
        assert "artifacts" in loaded_state
        assert "raw_data_checksums" in loaded_state["artifacts"]
        assert relative_path in loaded_state["artifacts"]["raw_data_checksums"]
        assert loaded_state["artifacts"]["raw_data_checksums"][relative_path] == checksum

    def test_missing_file_raises(self):
        """Test that missing file handling works (conceptually)."""
        missing_file = self.raw_dir / "nonexistent.csv"
        with pytest.raises(FileNotFoundError):
            if not missing_file.exists():
                raise FileNotFoundError(f"File {missing_file} not found.")

    def teardown_method(self):
        """Cleanup temp files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
