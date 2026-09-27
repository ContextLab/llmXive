import json
import os
import tempfile
from pathlib import Path
import pytest

from code.initialize_artifacts import initialize_empty_artifacts, parse_args

def test_initialize_artifacts_creates_files():
    """Test that initialize_empty_artifacts creates the JSON files with correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Define paths within temp directory
        data_dir = tmpdir_path / "data" / "processed"
        results_dir = tmpdir_path / "results"
        
        features_path = data_dir / "features.json"
        results_path = results_dir / "results.json"
        
        # Mock logger
        class MockLogger:
            def info(self, msg):
                pass
            def error(self, msg):
                pass
        
        logger = MockLogger()
        
        # Initialize artifacts
        initialize_empty_artifacts(features_path, results_path, logger)
        
        # Verify files exist
        assert features_path.exists(), "features.json was not created"
        assert results_path.exists(), "results.json was not created"
        
        # Verify content
        with open(features_path, 'r') as f:
            features_data = json.load(f)
        assert features_data == [], "features.json should contain an empty list"
        
        with open(results_path, 'r') as f:
            results_data = json.load(f)
        assert results_data == {}, "results.json should contain an empty dict"

def test_initialize_artifacts_creates_directories():
    """Test that initialize_empty_artifacts creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Define paths where directories don't exist
        features_path = tmpdir_path / "deep" / "nested" / "path" / "features.json"
        results_path = tmpdir_path / "other" / "path" / "results.json"
        
        class MockLogger:
            def info(self, msg):
                pass
            def error(self, msg):
                pass
        
        logger = MockLogger()
        
        # Initialize artifacts
        initialize_empty_artifacts(features_path, results_path, logger)
        
        # Verify directories were created
        assert features_path.parent.exists(), "Parent directory for features.json was not created"
        assert results_path.parent.exists(), "Parent directory for results.json was not created"
        
        # Verify files exist
        assert features_path.exists(), "features.json was not created"
        assert results_path.exists(), "results.json was not created"