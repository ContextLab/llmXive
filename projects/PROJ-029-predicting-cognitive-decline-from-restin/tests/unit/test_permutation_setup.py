"""Unit tests for mini-permutation setup (T042a).

This module verifies the data loading logic required for the permutation test
by creating a mock dataset of 5 subjects and ensuring the loader handles it correctly.
"""

import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.logger import get_logger

logger = get_logger("test_permutation_setup")


def create_mock_dataset(num_subjects: int = 5, temp_dir: str = None):
    """Create a minimal mock dataset for permutation testing.

    Args:
        num_subjects: Number of mock subjects to create.
        temp_dir: Directory to write mock files. If None, uses a temporary directory.

    Returns:
        Tuple of (temp_dir_path, features_df, labels_df)
    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="mock_permutation_")

    # Create mock graph metrics (simulating data/processed/graph_metrics.csv)
    # Schema: subject_id, node_degree, global_efficiency, clustering_coeff, path_length
    data = {
        "subject_id": [f"sub_{i:03d}" for i in range(num_subjects)],
        "node_degree": np.random.uniform(10, 50, num_subjects),
        "global_efficiency": np.random.uniform(0.1, 0.5, num_subjects),
        "clustering_coeff": np.random.uniform(0.2, 0.6, num_subjects),
        "path_length": np.random.uniform(1.5, 4.0, num_subjects),
    }
    features_df = pd.DataFrame(data)

    # Create mock labels (simulating cognitive decline status)
    # 0 = stable, 1 = declined
    labels_data = {
        "subject_id": features_df["subject_id"],
        "decline_label": np.random.randint(0, 2, num_subjects),
        "mmse_baseline": np.random.randint(24, 30, num_subjects),
        "mmse_followup": np.random.randint(20, 30, num_subjects),
    }
    labels_df = pd.DataFrame(labels_data)

    # Write to disk
    features_path = os.path.join(temp_dir, "mock_graph_metrics.csv")
    labels_path = os.path.join(temp_dir, "mock_labels.csv")

    features_df.to_csv(features_path, index=False)
    labels_df.to_csv(labels_path, index=False)

    return temp_dir, features_df, labels_df


def test_mini_permutation_setup():
    """Test that the mock dataset creation and loading logic works correctly.

    This test verifies:
    1. Mock dataset of 5 subjects can be created
    2. Data loading logic correctly reads the mock files
    3. Data shapes and types are as expected
    4. Subject IDs match between features and labels
    """
    # Create mock dataset
    temp_dir, expected_features, expected_labels = create_mock_dataset(num_subjects=5)

    try:
        # Load data as the permutation test would
        features_path = os.path.join(temp_dir, "mock_graph_metrics.csv")
        labels_path = os.path.join(temp_dir, "mock_labels.csv")

        loaded_features = pd.read_csv(features_path)
        loaded_labels = pd.read_csv(labels_path)

        # Assertions
        assert loaded_features.shape[0] == 5, "Should have 5 subjects"
        assert loaded_labels.shape[0] == 5, "Should have 5 subjects"

        # Check columns exist
        expected_feature_cols = ["subject_id", "node_degree", "global_efficiency",
                                 "clustering_coeff", "path_length"]
        assert list(loaded_features.columns) == expected_feature_cols, "Feature columns mismatch"

        expected_label_cols = ["subject_id", "decline_label", "mmse_baseline", "mmse_followup"]
        assert list(loaded_labels.columns) == expected_label_cols, "Label columns mismatch"

        # Check subject ID alignment
        assert list(loaded_features["subject_id"]) == list(loaded_labels["subject_id"]), \
            "Subject IDs must match between features and labels"

        # Check data types
        assert loaded_features["node_degree"].dtype in [np.float64, np.float32], \
            "node_degree should be numeric"
        assert loaded_labels["decline_label"].dtype in [np.int64, np.int32], \
            "decline_label should be integer"

        logger.log("test_mini_permutation_setup", status="passed", subjects=5)

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_data_loading_handles_edge_cases():
    """Test that data loading handles edge cases gracefully."""
    # Test with 1 subject (minimum viable dataset)
    temp_dir, _, _ = create_mock_dataset(num_subjects=1)

    try:
        features_path = os.path.join(temp_dir, "mock_graph_metrics.csv")
        labels_path = os.path.join(temp_dir, "mock_labels.csv")

        features = pd.read_csv(features_path)
        labels = pd.read_csv(labels_path)

        assert features.shape[0] == 1
        assert labels.shape[0] == 1

        logger.log("test_data_loading_handles_edge_cases", status="passed")

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_mock_data_is_realistic():
    """Test that mock data falls within realistic ranges for fMRI graph metrics."""
    temp_dir, features, _ = create_mock_dataset(num_subjects=5)

    try:
        # Check ranges based on typical AAL atlas (90 regions)
        assert features["node_degree"].between(0, 90).all(), \
            "Node degree should be between 0 and 90 (number of regions)"
        assert features["global_efficiency"].between(0, 1).all(), \
            "Global efficiency should be between 0 and 1"
        assert features["clustering_coeff"].between(0, 1).all(), \
            "Clustering coefficient should be between 0 and 1"
        assert features["path_length"].between(0, 10).all(), \
            "Path length should be positive and reasonable"

        logger.log("test_mock_data_is_realistic", status="passed")

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)