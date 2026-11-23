import os
import json
import pytest
from pathlib import Path
import sys

# Add code to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import init_preprocess_stats
from config import get_path

class TestInitPreprocessStats:
    def test_init_creates_file(self, tmp_path, monkeypatch):
        """Test that init_preprocess_stats creates the JSON file."""
        # Mock get_path to use tmp_path
        original_get_path = None
        # We can't easily mock get_path globally without affecting other tests,
        # so we test the logic by ensuring the file structure is correct.
        
        # Instead, we test the function's behavior by checking the file content
        # after calling it, assuming the path resolution works in the test env.
        
        # For this unit test, we will verify the logic by mocking the file write
        # or by using a temporary directory structure that mimics the project.
        
        # Let's assume the project structure exists for the sake of the test
        # or we patch the output path.
        
        # A better approach for this specific task:
        # The task requires writing to data/processed/preprocess_stats.json.
        # We will verify that the function writes valid JSON with the correct keys.
        
        # Since we cannot easily change the global get_path without side effects,
        # we will test the content generation logic by inspecting the file
        # after the function runs (if it runs) or by mocking.
        
        # Let's mock the file writing to verify the content.
        import preprocess
        from unittest.mock import patch, mock_open
        
        mock_data = {}
        
        def mock_open_func(file, *args, **kwargs):
            if 'w' in args or 'w' in kwargs.get('mode', ''):
                # Capture the content written
                class MockFile:
                    def __init__(self):
                        self.content = ""
                    def write(self, data):
                        self.content = data
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                m = MockFile()
                mock_data['content'] = m.content
                return m
            return open(file, *args, **kwargs)

        with patch('builtins.open', mock_open_func):
            with patch('os.path.exists', return_value=True): # Pretend file check passes
                with patch('config.ensure_dirs'): # Skip dir creation
                    init_preprocess_stats("https://osf.io/xyz")
        
        assert 'content' in mock_data
        data = json.loads(mock_data['content'])
        
        assert data['data_source_url'] == "https://osf.io/xyz"
        assert data['excluded_days_count'] == 0
        assert data['reason'] == "initial"

    def test_init_verifies_write(self, tmp_path, monkeypatch):
        """Test that the function raises if write fails (simulated)."""
        import preprocess
        from unittest.mock import patch
        
        # Simulate a write that results in empty file or missing file
        with patch('builtins.open', side_effect=Exception("IO Error")):
            with pytest.raises(Exception):
                init_preprocess_stats("test_url")