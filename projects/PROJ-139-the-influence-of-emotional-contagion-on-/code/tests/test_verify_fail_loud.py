"""
Unit tests for T041: Fail-loud mechanism verification.

These tests ensure that the fail-loud mechanisms are correctly implemented
and trigger on expected failure conditions.
"""
import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root / "code"))

from data.download import download_data
from config.settings import DatasetPaths

class TestFailLoudDownload:
    """Tests for download.py fail-loud behavior."""

    def test_download_raises_runtime_error_on_all_failures(self):
        """Test that download_data raises RuntimeError when all sources fail."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_paths = DatasetPaths(
                raw_data=Path(tmp_dir) / "raw",
                processed_data=Path(tmp_dir) / "processed",
                state=Path(tmp_dir) / "state"
            )
            test_paths.raw_data.mkdir(parents=True, exist_ok=True)
            test_paths.processed_data.mkdir(parents=True, exist_ok=True)
            test_paths.state.mkdir(parents=True, exist_ok=True)

            # Mock all fetch functions to raise exceptions
            with patch('data.download.fetch_from_pushshift', side_effect=Exception("Pushshift API Unreachable")), \
                 patch('data.download.fetch_from_reddit_api', side_effect=Exception("Reddit API Auth Failed")), \
                 patch('data.download.fetch_from_huggingface', side_effect=Exception("HF Archive Not Found")), \
                 patch('data.download.fetch_from_internet_archive', side_effect=Exception("Internet Archive Unavailable")):
                
                    with pytest.raises(RuntimeError) as exc_info:
                        download_data(output_dir=test_paths.raw_data, config=None)
                    
                    assert "All data sources failed" in str(exc_info.value)

    def test_download_does_not_generate_synthetic_data(self):
        """Test that download_data does not generate synthetic data on failure."""
        # This test is more of a code review check, but we can verify
        # that no synthetic data files are created in the output directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_paths = DatasetPaths(
                raw_data=Path(tmp_dir) / "raw",
                processed_data=Path(tmp_dir) / "processed",
                state=Path(tmp_dir) / "state"
            )
            test_paths.raw_data.mkdir(parents=True, exist_ok=True)
            test_paths.processed_data.mkdir(parents=True, exist_ok=True)
            test_paths.state.mkdir(parents=True, exist_ok=True)

            # Mock all fetch functions to raise exceptions
            with patch('data.download.fetch_from_pushshift', side_effect=Exception("Pushshift API Unreachable")), \
                 patch('data.download.fetch_from_reddit_api', side_effect=Exception("Reddit API Auth Failed")), \
                 patch('data.download.fetch_from_huggingface', side_effect=Exception("HF Archive Not Found")), \
                 patch('data.download.fetch_from_internet_archive', side_effect=Exception("Internet Archive Unavailable")):
                
                    try:
                        download_data(output_dir=test_paths.raw_data, config=None)
                    except RuntimeError:
                        pass  # Expected
                    
                    # Check that no files were created in raw_data
                    files = list(test_paths.raw_data.glob("*"))
                    assert len(files) == 0, "No files should be created if all sources fail"

class TestNoSyntheticFallback:
    """Tests to ensure no synthetic fallback is used."""

    def test_no_synthetic_patterns_in_download(self):
        """Verify that download.py does not contain synthetic data generation patterns."""
        download_py_path = Path(__file__).resolve().parent.parent / "data" / "download.py"
        
        if not download_py_path.exists():
            pytest.skip("download.py not found")
        
        with open(download_py_path, 'r') as f:
            content = f.read()
        
        synthetic_patterns = [
            "generate_synthetic",
            "mock_data",
            "np.random",
            "faker",
            "fake_data"
        ]
        
        for pattern in synthetic_patterns:
            assert pattern not in content, f"Found synthetic pattern '{pattern}' in download.py"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
