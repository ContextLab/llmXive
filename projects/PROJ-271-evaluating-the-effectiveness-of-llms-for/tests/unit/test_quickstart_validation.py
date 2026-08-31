"""
Unit tests for the Quickstart Validation script (T034).
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Mock the config module for testing if necessary, but here we assume standard paths
# For unit testing, we will test the logic functions directly by patching or mocking paths
# However, since the script uses config.get_path(), we need to ensure the environment
# is set up or we test the logic in isolation.

# We will test the logic by creating temporary files and verifying the validation functions
# We need to import the functions from run_quickstart_validation
# Note: Since run_quickstart_validation imports from config, we need to ensure config is available.
# We assume the test environment has the project structure set up as per T001.

import sys
import importlib.util

# Load the module dynamically to avoid import errors if paths are not set up perfectly in test env
spec = importlib.util.spec_from_file_location("run_quickstart_validation", "code/run_quickstart_validation.py")
validator_module = importlib.util.module_from_spec(spec)

# We will mock the config functions that are used
class MockConfig:
    @staticmethod
    def get_data_path(filename):
        return os.path.join("data", filename)
    @staticmethod
    def get_processed_path(filename):
        return os.path.join("data", "processed", filename)
    @staticmethod
    def get_results_path(filename):
        return os.path.join("results", filename)
    @staticmethod
    def setup_logging(name, level=None):
        import logging
        return logging.getLogger(name)

# Patching the module's config reference if it was imported
# Since the script does: from config import ..., we can't easily patch inside the module
# unless we reload it. Instead, we will test the logic by mocking the file system existence
# and content reading logic where possible, or by creating a temporary directory structure.

# Alternative approach: Test the logic by creating a temporary directory and mocking the paths
# But the functions in run_quickstart_validation are tightly coupled to config paths.
# Let's assume the test runs in an environment where the project root is set up.
# For the purpose of this task, we will write tests that verify the logic by creating
# temporary files in a temp directory and monkey-patching the path functions.

# Actually, a cleaner way for unit tests is to refactor the validation functions to accept paths,
# but since we are implementing T034 and not refactoring, we will create a test that
# mocks the config module or the file system.

# Let's create a test that creates a temporary directory structure and mocks the config functions
# by re-importing the module with mocked config.

# However, to keep it simple and robust, we will test the logic by creating a temporary
# directory and using monkeypatch to override the config functions.

# We will use pytest's monkeypatch fixture

@pytest.fixture
def mock_config(monkeypatch):
    """Mock the config functions to use a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    
    def mock_get_data_path(filename):
        return os.path.join(temp_dir, filename)
    
    def mock_get_processed_path(filename):
        return os.path.join(temp_dir, "processed", filename)
    
    def mock_get_results_path(filename):
        return os.path.join(temp_dir, "results", filename)
    
    def mock_setup_logging(name, level=None):
        import logging
        return logging.getLogger(name)

    # We need to reload the module to pick up the mocked config
    # But since the module imports from config at the top level, we need to patch the config module itself
    # or patch the functions in the validator module after import.
    
    # Let's patch the functions in the validator module directly if possible
    # Or, better, we can create a temporary config module and set sys.modules['config']
    
    # This is getting complex. Let's assume the test environment has the project structure.
    # Instead, we will test the logic by creating a temporary directory and creating the files
    # in that directory, and then patching the config functions to return paths in that directory.
    
    # We will patch the config module's functions
    import config
    monkeypatch.setattr(config, 'get_data_path', mock_get_data_path)
    monkeypatch.setattr(config, 'get_processed_path', mock_get_processed_path)
    monkeypatch.setattr(config, 'get_results_path', mock_get_results_path)
    monkeypatch.setattr(config, 'setup_logging', mock_setup_logging)
    
    # Now reload the validator module to pick up the new config
    import run_quickstart_validation
    importlib.reload(run_quickstart_validation)
    
    return temp_dir

def test_validate_static_baseline_missing(mock_config, monkeypatch):
    """Test that validation fails when static_baseline.csv is missing."""
    import run_quickstart_validation
    result = run_quickstart_validation.validate_static_baseline()
    assert result is False

def test_validate_static_baseline_empty(mock_config, monkeypatch):
    """Test that validation fails when static_baseline.csv is empty."""
    import run_quickstart_validation
    data_path = os.path.join(mock_config, "static_baseline.csv")
    pd.DataFrame().to_csv(data_path, index=False)
    
    result = run_quickstart_validation.validate_static_baseline()
    assert result is False

def test_validate_static_baseline_valid(mock_config, monkeypatch):
    """Test that validation passes when static_baseline.csv is valid."""
    import run_quickstart_validation
    data_path = os.path.join(mock_config, "static_baseline.csv")
    df = pd.DataFrame({
        "code": ["def foo(): pass", "def bar(): pass"],
        "loc": [1, 1],
        "cyclomatic_complexity": [1, 1],
        "static_smell_labels": ["", ""]
    })
    df.to_csv(data_path, index=False)
    
    result = run_quickstart_validation.validate_static_baseline()
    assert result is True

def test_validate_semantic_results_missing(mock_config, monkeypatch):
    """Test that validation fails when semantic_results.json is missing."""
    import run_quickstart_validation
    result = run_quickstart_validation.validate_semantic_results()
    assert result is False

def test_validate_semantic_results_empty(mock_config, monkeypatch):
    """Test that validation fails when semantic_results.json is empty."""
    import run_quickstart_validation
    processed_path = os.path.join(mock_config, "processed")
    os.makedirs(processed_path, exist_ok=True)
    json_path = os.path.join(processed_path, "semantic_results.json")
    with open(json_path, 'w') as f:
        json.dump([], f)
    
    result = run_quickstart_validation.validate_semantic_results()
    assert result is False

def test_validate_semantic_results_valid(mock_config, monkeypatch):
    """Test that validation passes when semantic_results.json is valid."""
    import run_quickstart_validation
    processed_path = os.path.join(mock_config, "processed")
    os.makedirs(processed_path, exist_ok=True)
    json_path = os.path.join(processed_path, "semantic_results.json")
    data = [
        {
            "code": "def foo(): pass",
            "embedding": [0.1] * 384,
            "llm_labels": ["smell1"],
            "static_smell_labels": ["smell2"]
        }
    ]
    with open(json_path, 'w') as f:
        json.dump(data, f)
    
    result = run_quickstart_validation.validate_semantic_results()
    assert result is True

def test_validate_results_artifacts_missing(mock_config, monkeypatch):
    """Test that validation fails when result files are missing."""
    import run_quickstart_validation
    result = run_quickstart_validation.validate_results_artifacts()
    assert result is False

def test_validate_results_artifacts_valid(mock_config, monkeypatch):
    """Test that validation passes when result files are valid."""
    import run_quickstart_validation
    results_path = os.path.join(mock_config, "results")
    os.makedirs(results_path, exist_ok=True)
    
    # Create statistical_significance.json
    with open(os.path.join(results_path, "statistical_significance.json"), 'w') as f:
        json.dump({"test": "result"}, f)
    
    # Create logistic_regression.json
    with open(os.path.join(results_path, "logistic_regression.json"), 'w') as f:
        json.dump({"coefficients": [1.0]}, f)
    
    # Create sensitivity_report.md
    with open(os.path.join(results_path, "sensitivity_report.md"), 'w') as f:
        f.write("# Sensitivity Report\n\nSome content here.")
    
    result = run_quickstart_validation.validate_results_artifacts()
    assert result is True
