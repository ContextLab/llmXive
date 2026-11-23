import os
import yaml
import pytest
from pathlib import Path
import tempfile
import shutil

from downloaders import main, generate_checksum_file, update_state_file

class TestChecksumPipeline:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        tmpdir = tempfile.mkdtemp()
        data_raw = os.path.join(tmpdir, "data", "raw")
        state_dir = os.path.join(tmpdir, "state", "projects")
        
        os.makedirs(data_raw, exist_ok=True)
        os.makedirs(state_dir, exist_ok=True)
        
        yield {
            "base": tmpdir,
            "data_raw": data_raw,
            "state_dir": state_dir
        }
        
        shutil.rmtree(tmpdir)

    def test_checksum_generation(self, temp_dirs):
        """Test that checksum files are generated correctly."""
        # Create a test file
        test_file = os.path.join(temp_dirs["data_raw"], "test.parquet")
        with open(test_file, 'wb') as f:
            f.write(b"test data for checksum")
        
        checksum_path = test_file + ".sha256"
        generate_checksum_file(test_file, checksum_path)
        
        assert os.path.exists(checksum_path)
        
        # Verify checksum format
        with open(checksum_path, 'r') as f:
            content = f.read().strip()
        
        parts = content.split()
        assert len(parts) == 2
        assert len(parts[0]) == 64  # SHA-256 hex length

    def test_state_file_update(self, temp_dirs):
        """Test that state file is updated with checksums."""
        state_file = os.path.join(temp_dirs["state_dir"], "test-project.yaml")
        
        checksums = {
            "oqmd": "abc123",
            "aflow": "def456"
        }
        
        update_state_file(checksums, state_file)
        
        assert os.path.exists(state_file)
        
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "artifact_hashes" in data
        assert data["artifact_hashes"]["oqmd"] == "abc123"
        assert data["artifact_hashes"]["aflow"] == "def456"

    def test_full_pipeline_integration(self, temp_dirs):
        """Test the full checksum pipeline with mocked downloads."""
        # Create mock data files
        oqmd_path = os.path.join(temp_dirs["data_raw"], "oqmd.parquet")
        aflow_path = os.path.join(temp_dirs["data_raw"], "aflow.parquet")
        
        with open(oqmd_path, 'wb') as f:
            f.write(b"mock oqmd data")
        with open(aflow_path, 'wb') as f:
            f.write(b"mock aflow data")
        
        # Mock the download functions
        with patch('downloaders.download_oqmd_constitution', return_value=oqmd_path), \
             patch('downloaders.download_aflow_constitution', return_value=aflow_path), \
             patch('downloaders.download_materials_project', return_value=None):
            
            # Change to temp directory to run main
            old_cwd = os.getcwd()
            os.chdir(temp_dirs["base"])
            
            try:
                main()
                
                # Check that checksum files were created
                assert os.path.exists(oqmd_path + ".sha256")
                assert os.path.exists(aflow_path + ".sha256")
                
                # Check state file
                state_file = os.path.join(temp_dirs["state_dir"], "PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml")
                assert os.path.exists(state_file)
                
                with open(state_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                assert "artifact_hashes" in data
            finally:
                os.chdir(old_cwd)