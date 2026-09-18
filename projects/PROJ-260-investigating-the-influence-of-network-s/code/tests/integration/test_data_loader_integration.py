"""
Integration tests for the data loader service.

These tests verify that the data loader correctly interacts with the 
research.md file and handles missing/invalid scenarios as per T056 requirements.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.data_loader import load_verified_dataset_ids, write_missing_log, DATA_RAW_DIR, MISSING_LOG_FILE
from src.lib.config import get_project_root

class TestDataLoaderIntegration:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        
        # Create minimal project structure
        Path("research.md").touch()
        Path("data").mkdir()
        Path("data/raw").mkdir()
        
        yield
        
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_load_verified_ids_success(self):
        """Test that load_verified_dataset_ids correctly parses research.md."""
        research_content = """
        # Research Data
        
        ### Verified Datasets
        - N=1000: zenodo/12345
        - N=2000: zenodo/67890
        - N=4000: zenodo/11111
        """
        with open("research.md", "w") as f:
            f.write(research_content)
        
        result = load_verified_dataset_ids()
        
        assert 1000 in result
        assert result[1000] == "zenodo/12345"
        assert 2000 in result
        assert result[2000] == "zenodo/67890"
        assert 4000 in result
        assert result[4000] == "zenodo/11111"

    def test_load_verified_ids_missing_file(self):
        """Test that load_verified_dataset_ids raises error if research.md is missing."""
        os.remove("research.md")
        
        with pytest.raises(FileNotFoundError):
            load_verified_dataset_ids()

    def test_load_verified_ids_empty(self):
        """Test that load_verified_dataset_ids raises error if no datasets found."""
        with open("research.md", "w") as f:
            f.write("# No datasets here")
        
        with pytest.raises(ValueError, match="No verified dataset IDs found"):
            load_verified_dataset_ids()

    def test_write_missing_log(self):
        """Test that missing datasets are logged correctly."""
        missing = ["N=1000 (ID: zenodo/123)", "N=2000 (ID: zenodo/456)"]
        
        write_missing_log(missing)
        
        assert MISSING_LOG_FILE.exists()
        content = MISSING_LOG_FILE.read_text()
        assert "Missing Datasets Report" in content
        assert "N=1000" in content
        assert "N=2000" in content

    def test_no_synthetic_fallback(self):
        """
        This is a conceptual test to ensure the code structure does not allow
        synthetic fallbacks. We verify that the main logic exits on failure.
        """
        # The actual logic is in main(), which calls sys.exit(1) on failure.
        # This test verifies the existence of the write_missing_log call
        # which is the first step of the "fail loudly" protocol.
        import inspect
        from src.services.data_loader import main
        
        source = inspect.getsource(main)
        # Ensure the code checks for missing datasets and logs them
        assert "missing_datasets" in source
        assert "write_missing_log" in source
        assert "sys.exit(1)" in source
        # Ensure no synthetic generation functions are called
        assert "generate_synthetic" not in source
        assert "mock_data" not in source
        assert "np.random" not in source
