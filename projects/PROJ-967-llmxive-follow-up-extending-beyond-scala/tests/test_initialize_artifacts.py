"""
Tests for Task T001e: Initialize output artifacts.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We assume the module is in code/initialize_artifacts.py
# For testing, we might need to adjust the import path or copy the logic
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala" / "code"))

from initialize_artifacts import initialize_empty_artifacts

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        # Create expected subdirectories
        (root / "data" / "processed").mkdir(parents=True)
        (root / "results").mkdir(parents=True)
        yield root

def test_initializes_features_json(temp_project_root):
    """Test that features.json is created with an empty list."""
    logger = type('Logger', (), {'info': lambda s, m: None, 'error': lambda s, m: None})()
    initialize_empty_artifacts(temp_project_root, logger)

    features_path = temp_project_root / "data" / "processed" / "features.json"
    assert features_path.exists(), "features.json should be created."
    
    with open(features_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    assert content == [], "features.json should contain an empty list."

def test_initializes_results_json(temp_project_root):
    """Test that results.json is created with an empty dict."""
    logger = type('Logger', (), {'info': lambda s, m: None, 'error': lambda s, m: None})()
    initialize_empty_artifacts(temp_project_root, logger)

    results_path = temp_project_root / "results" / "results.json"
    assert results_path.exists(), "results.json should be created."
    
    with open(results_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    assert content == {}, "results.json should contain an empty dict."

def test_creates_directories_if_missing(temp_project_root):
    """Test that the function creates directories if they don't exist."""
    # Remove the processed directory
    processed_dir = temp_project_root / "data" / "processed"
    results_dir = temp_project_root / "results"
    # Note: The fixture creates them, but we can test the logic by removing them
    # However, the fixture creates them. Let's test a scenario where we pass a root
    # that doesn't have them, but the fixture ensures structure. 
    # The function itself calls mkdir(parents=True, exist_ok=True), so it handles it.
    # We verify the files exist after call.
    
    logger = type('Logger', (), {'info': lambda s, m: None, 'error': lambda s, m: None})()
    # Re-create a temp dir without the specific subdirs to test mkdir logic
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        # Do NOT create data/processed or results
        initialize_empty_artifacts(root, logger)
        
        assert (root / "data" / "processed" / "features.json").exists()
        assert (root / "results" / "results.json").exists()