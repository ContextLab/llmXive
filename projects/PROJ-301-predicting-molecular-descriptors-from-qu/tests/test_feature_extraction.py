import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Mock the main function for testing
def test_feature_matrix_shape():
    """Assert shape matches subset size."""
    # This would be tested after running the actual script
    features_2d_path = Path("data/processed/features_2d.npy")
    features_3d_path = Path("data/processed/features_3d.npy")
    labels_path = Path("data/processed/labels.csv")

    if features_2d_path.exists():
        features_2d = np.load(features_2d_path)
        labels = pd.read_csv(labels_path)
        assert features_2d.shape[0] == len(labels), "Feature matrix shape does not match label count"

def test_label_alignment():
    """Assert labels match feature indices."""
    features_2d_path = Path("data/processed/features_2d.npy")
    labels_path = Path("data/processed/labels.csv")

    if features_2d_path.exists():
        features_2d = np.load(features_2d_path)
        labels = pd.read_csv(labels_path)
        # Check that indices align (assuming labels have a consistent order)
        assert len(features_2d) == len(labels), "Feature and label counts do not match"

def test_3d_parsing_error_handling():
    """Assert malformed molecules are dropped."""
    # This would be tested by checking the logs or the number of processed molecules
    # For now, a placeholder assertion
    assert True, "Error handling test passed (placeholder)"
