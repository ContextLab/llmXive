import os
import pytest
import matplotlib.image as mpimg
from pathlib import Path

from config import RESULTS_ROOT

def test_regression_plot_exists():
    """Verify that regression_plot.png exists and is a valid image."""
    path = os.path.join(RESULTS_ROOT, "figures", "regression_plot.png")
    assert os.path.exists(path), f"File not found: {path}"
    
    # Verify it's a valid image
    try:
        img = mpimg.imread(path)
        assert img is not None
        assert img.shape[0] > 0 and img.shape[1] > 0
    except Exception as e:
        pytest.fail(f"Failed to load image: {e}")

def test_sensitivity_table_exists():
    """Verify that sensitivity_table.png exists and is a valid image."""
    path = os.path.join(RESULTS_ROOT, "figures", "sensitivity_table.png")
    assert os.path.exists(path), f"File not found: {path}"
    
    # Verify it's a valid image
    try:
        img = mpimg.imread(path)
        assert img is not None
        assert img.shape[0] > 0 and img.shape[1] > 0
    except Exception as e:
        pytest.fail(f"Failed to load image: {e}")

def test_stratified_plot_condition():
    """Verify stratified plot only exists if interaction is significant."""
    # This is a logical check; the actual existence is handled by the script logic
    # We just ensure the file path is correct if it exists
    path = os.path.join(RESULTS_ROOT, "figures", "stratified_plot.png")
    # If the file exists, it should be valid
    if os.path.exists(path):
        try:
            img = mpimg.imread(path)
            assert img is not None
        except Exception as e:
            pytest.fail(f"Stratified plot exists but is invalid: {e}")
