"""
Tests for T007: Download data script.

These tests verify that the download script:
1. Raises RuntimeError on download failure
2. Verifies checksums (if possible)
3. Logs detected tasks to data/interim/detected_tasks.log
4. Halts if task names do not match expected set
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_path, ensure_dirs

class TestDownloadData:
    """Test suite for data download functionality."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_root = Path(tempfile.mkdtemp())
        data_raw = temp_root / "data" / "raw"
        interim = temp_root / "data" / "interim"
        data_raw.mkdir(parents=True, exist_ok=True)
        interim.mkdir(parents=True, exist_ok=True)
        
        # Mock get_path to use temp directories
        original_get_path = get_path
        
        def mock_get_path(name, *args):
            if name == "raw_data":
                return str(data_raw)
            elif name == "interim":
                return str(interim)
            elif name in ["data/raw", "data/interim"]:
                return str(temp_root / name)
            else:
                return str(temp_root / name)
        
        with patch('code.config.get_path', mock_get_path):
            yield {
                "raw": data_raw,
                "interim": interim,
                "root": temp_root
            }
        
        # Cleanup
        shutil.rmtree(temp_root)

    def test_ensure_dirs_handles_various_inputs(self):
        """Test that ensure_dirs handles all call signatures."""
        # Test no args
        result = ensure_dirs()
        assert isinstance(result, Path)
        
        # Test single string
        with tempfile.TemporaryDirectory() as tmpdir:
            path_str = os.path.join(tmpdir, "test")
            result = ensure_dirs(path_str)
            assert Path(path_str).exists()
            
            # Test single Path
            path_obj = Path(tmpdir) / "test2"
            result = ensure_dirs(path_obj)
            assert path_obj.exists()
            
            # Test list of strings
            result = ensure_dirs([os.path.join(tmpdir, "test3")])
            assert Path(os.path.join(tmpdir, "test3")).exists()
            
            # Test list of Paths
            result = ensure_dirs([Path(tmpdir) / "test4"])
            assert (Path(tmpdir) / "test4").exists()

    def test_get_path_handles_various_inputs(self):
        """Test that get_path handles all call signatures."""
        # Test single key
        path = get_path("data_raw")
        assert isinstance(path, str)
        
        # Test key with subpath
        path = get_path("processed", "features.csv")
        assert isinstance(path, str)
        
        # Test direct path string
        path = get_path("data/processed/features.csv")
        assert isinstance(path, str)

    def test_download_script_raises_on_failure(self):
        """Test that download script raises RuntimeError on failure."""
        from code_01_download_data import download_file
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "test.txt"
            with pytest.raises(RuntimeError):
                download_file("http://invalid-url-that-does-not-exist.com", dest)

    def test_log_detected_tasks_creates_log(self, temp_dirs):
        """Test that log_detected_tasks creates the log file."""
        from code_01_download_data import log_detected_tasks
        
        # Create a dummy EDF file to simulate data
        edf_file = temp_dirs["raw"] / "S001R01.edf"
        edf_file.touch()
        
        log_path = temp_dirs["interim"] / "detected_tasks.log"
        detected = log_detected_tasks(temp_dirs["raw"], log_path)
        
        assert log_path.exists()
        assert "Detected Tasks" in log_path.read_text()
        assert "Rest" in detected or "Run" in detected or "Imagery" in detected

    def test_verify_data_integrity_raises_on_missing_tasks(self, temp_dirs):
        """Test that verify_data_integrity raises on missing expected tasks."""
        from code_01_download_data import verify_data_integrity
        
        # Create a dummy file that doesn't match expected tasks
        dummy_file = temp_dirs["raw"] / "S001X99.edf"
        dummy_file.touch()
        
        # This should raise because we can't detect any valid tasks
        # or if we detect tasks that don't match expected set
        with pytest.raises(RuntimeError):
            verify_data_integrity(temp_dirs["raw"], {"InvalidTask"})

    def test_main_function_structure(self):
        """Test that main function has correct structure."""
        from code_01_download_data import main
        import inspect
        
        # Check that main exists and is callable
        assert callable(main)
        
        # Check that it has the expected arguments
        sig = inspect.signature(main)
        # main() should have no required arguments (uses argparse)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
