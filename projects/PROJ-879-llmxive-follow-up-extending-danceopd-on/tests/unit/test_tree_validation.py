#!/usr/bin/env python
"""
Unit tests for T021d: Validate Model Metadata and Results.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
import json
from pathlib import Path
import hashlib
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.config import get_config
from code_01_train_trees import validate_model_metadata, load_and_split_data, train_forests
# Note: In a real scenario, we would mock the heavy training part, but here we test the validation logic


@pytest.fixture
def temp_results_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock results directory structure
        results_dir = Path(tmpdir) / 'data' / 'results'
        state_dir = Path(tmpdir) / 'state'
        results_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        # Create mock tree_accuracy.csv
        tree_df = pd.DataFrame({
            'max_depth': [2, 5, 10, 20],
            'train_accuracy': [0.85, 0.90, 0.95, 0.99],
            'test_accuracy': [0.82, 0.88, 0.92, 0.90]
        })
        tree_path = results_dir / 'tree_accuracy.csv'
        tree_df.to_csv(tree_path, index=False)

        # Create mock forest_accuracy.csv
        forest_df = pd.DataFrame({
            'n_estimators': [10, 50, 100],
            'train_accuracy': [0.88, 0.92, 0.95],
            'test_accuracy': [0.85, 0.90, 0.91]
        })
        forest_path = results_dir / 'forest_accuracy.csv'
        forest_df.to_csv(forest_path, index=False)

        yield results_dir, state_dir, tree_path, forest_path


def test_validate_model_metadata_success(temp_results_dir):
    """Test that validation passes for valid data."""
    results_dir, state_dir, tree_path, forest_path = temp_results_dir

    # We need to temporarily patch the config to point to our temp dir
    # Since get_config() is global, we might need to mock it or rely on env vars if the config supports it.
    # For this test, we assume the config can be overridden or we test the logic directly.
    # However, the function `validate_model_metadata` uses `get_config()`.
    # Let's test the logic by mocking the paths inside the function or by setting up the environment.

    # For simplicity in this unit test, we will assume the environment is set up correctly
    # or we will patch the function's internal calls.
    # A better approach for a pure unit test is to refactor the function to accept paths,
    # but since we are implementing T021d, we assume the function is as designed.
    # We will test the logic by ensuring the files exist and are valid.

    # We'll mock the config to return our temp paths
    class MockConfig:
        PROJECT_ROOT = str(Path(temp_results_dir[0]).parent.parent)

    original_get_config = None
    try:
        import utils.config as config_module
        original_get_config = config_module.get_config
        config_module.get_config = lambda: MockConfig()

        # Run validation
        # Note: The function expects specific relative paths based on PROJECT_ROOT
        # We need to ensure the relative paths match our temp structure
        # Our temp structure: tmpdir/data/results/tree_accuracy.csv
        # Config PROJECT_ROOT: tmpdir
        # Expected: tmpdir/data/results/tree_accuracy.csv -> Matches!

        metadata = validate_model_metadata()

        assert metadata is not None
        assert 'tree_accuracy_csv' in metadata
        assert 'forest_accuracy_csv' in metadata
        assert metadata['tree_accuracy_csv']['status'] == 'validated'
        assert metadata['forest_accuracy_csv']['status'] == 'validated'

        # Check state file
        state_file = Path(MockConfig.PROJECT_ROOT) / 'state' / 'model_metadata.yaml'
        assert state_file.exists()

        with open(state_file, 'r') as f:
            saved_metadata = yaml.safe_load(f)

        assert saved_metadata['tree_accuracy_csv']['sha256'] == metadata['tree_accuracy_csv']['sha256']

    finally:
        if original_get_config:
            config_module.get_config = original_get_config


def test_validate_model_metadata_nan_values(temp_results_dir):
    """Test that validation fails if NaN values are present."""
    results_dir, state_dir, tree_path, forest_path = temp_results_dir

    # Introduce NaN
    df = pd.read_csv(tree_path)
    df.loc[0, 'test_accuracy'] = np.nan
    df.to_csv(tree_path, index=False)

    class MockConfig:
        PROJECT_ROOT = str(Path(temp_results_dir[0]).parent.parent)

    import utils.config as config_module
    original_get_config = config_module.get_config
    config_module.get_config = lambda: MockConfig()

    try:
        with pytest.raises(ValueError, match="NaN"):
            validate_model_metadata()
    finally:
        config_module.get_config = original_get_config


def test_validate_model_metadata_unsorted(temp_results_dir):
    """Test that validation sorts the data if unsorted."""
    results_dir, state_dir, tree_path, forest_path = temp_results_dir

    # Unsort the data
    df = pd.read_csv(tree_path)
    df = df.iloc[[3, 0, 1, 2]] # Shuffle
    df.to_csv(tree_path, index=False)

    class MockConfig:
        PROJECT_ROOT = str(Path(temp_results_dir[0]).parent.parent)

    import utils.config as config_module
    original_get_config = config_module.get_config
    config_module.get_config = lambda: MockConfig()

    try:
        metadata = validate_model_metadata()
        # Check if the file was re-sorted
        reloaded = pd.read_csv(tree_path)
        assert reloaded['max_depth'].is_monotonic_increasing
    finally:
        config_module.get_config = original_get_config
