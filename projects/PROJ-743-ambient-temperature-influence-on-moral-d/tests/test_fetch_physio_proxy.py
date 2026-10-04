import pytest
import os
import sys
from pathlib import Path
import json
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetch_physio_proxy import ensure_directories, fetch_physio_proxy

class TestFetchPhysioProxy:
    def test_ensure_directories(self, tmp_path):
        """Test that ensure_directories creates the required folders."""
        # Temporarily override the default paths for testing
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            # This function creates directories relative to cwd
            # We need to patch the function or test the side effect
            # Since the function uses hardcoded paths, we test that it creates them
            ensure_directories()
            
            assert Path("data/processed").exists()
            assert Path("results/logs").exists()
        finally:
            os.chdir(original_cwd)

    def test_fetch_physio_proxy_failure(self, tmp_path, monkeypatch):
        """Test that the fetch function fails loudly if no data is available."""
        # Mock the load_dataset to raise an error
        def mock_load_dataset(*args, **kwargs):
            raise ImportError("Simulated dataset not found")
        
        monkeypatch.setattr("fetch_physio_proxy.load_dataset", mock_load_dataset)
        
        output_path = tmp_path / "data" / "processed" / "test_proxy.parquet"
        log_path = tmp_path / "results" / "logs" / "test_status.json"
        
        # Ensure parent directories exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # We need to pass a logger, but for this test we'll just check the exception
        # Since fetch_physio_proxy calls load_dataset which we mocked
        with pytest.raises(Exception) as exc_info:
            # We can't easily pass a logger without importing logging setup
            # So we rely on the fact that the function raises
            # We'll create a dummy logger
            import logging
            logger = logging.getLogger("test")
            fetch_physio_proxy(logger, output_path)
        
        assert "Physiological proxy dataset fetch failed" in str(exc_info.value)

    def test_fetch_physio_proxy_success_mock(self, tmp_path, monkeypatch):
        """Test that the fetch function succeeds if a mock dataset is provided."""
        # Create a mock dataset
        mock_data = {
            'participant_id': ['p1', 'p2', 'p3'],
            'signal_value': [1.2, 3.4, 5.6],
            'timestamp': [100, 200, 300]
        }
        mock_df = pd.DataFrame(mock_data)
        
        def mock_load_dataset(*args, **kwargs):
            from datasets import Dataset
            return Dataset.from_pandas(mock_df)
        
        monkeypatch.setattr("fetch_physio_proxy.load_dataset", mock_load_dataset)
        
        output_path = tmp_path / "data" / "processed" / "test_proxy.parquet"
        log_path = tmp_path / "results" / "logs" / "test_status.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        import logging
        logger = logging.getLogger("test")
        
        # This should not raise
        result = fetch_physio_proxy(logger, output_path)
        
        assert result is True
        assert output_path.exists()
        
        # Verify content
        loaded_df = pd.read_parquet(output_path)
        assert 'participant_id' in loaded_df.columns
        assert len(loaded_df) == 3