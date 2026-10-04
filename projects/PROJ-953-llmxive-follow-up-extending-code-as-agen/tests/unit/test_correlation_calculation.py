import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from scripts.calculate_correlations import encode_target, calculate_correlations

def test_encode_target_pass():
    """Test encoding for 'Pass' outcome."""
    data = pd.Series(['Pass', 'Pass', 'Fail', 'Timeout/Fail', 'Pass'])
    result = encode_target(data)
    expected = np.array([0, 0, 1, 1, 0])
    np.testing.assert_array_equal(result, expected)

def test_encode_target_fail():
    """Test encoding for 'Fail' outcome."""
    data = pd.Series(['Fail', 'Fail'])
    result = encode_target(data)
    expected = np.array([1, 1])
    np.testing.assert_array_equal(result, expected)

def test_calculate_correlations_basic():
    """Test basic correlation calculation with synthetic data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create features CSV
        features_df = pd.DataFrame({
            'task_id': ['t1', 't2', 't3', 't4', 't5'],
            'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_b': [5.0, 4.0, 3.0, 2.0, 1.0],
            'feature_c': [1.0, 1.0, 1.0, 1.0, 1.0]  # Constant feature
        })
        features_path = tmpdir_path / "features.csv"
        features_df.to_csv(features_path, index=False)
        
        # Create ground truth CSV
        ground_truth_df = pd.DataFrame({
            'task_id': ['t1', 't2', 't3', 't4', 't5'],
            'dynamic_execution_outcome': ['Pass', 'Pass', 'Fail', 'Fail', 'Pass']
        })
        ground_truth_path = tmpdir_path / "ground_truth.csv"
        ground_truth_df.to_csv(ground_truth_path, index=False)
        
        # Calculate correlations
        results = calculate_correlations(str(features_path), str(ground_truth_path))
        
        # Verify structure
        assert "correlations" in results
        assert "top_correlations" in results
        assert "framing" in results
        assert results["framing"] == "associational"
        
        # Verify feature_a (positive correlation expected)
        assert results["correlations"]["feature_a"] > 0
        
        # Verify feature_b (negative correlation expected)
        assert results["correlations"]["feature_b"] < 0
        
        # Verify constant feature has 0 correlation
        assert results["correlations"]["feature_c"] == 0.0

def test_calculate_correlations_no_overlap():
    """Test error handling when no task_ids overlap."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create features CSV with task_ids t1-t3
        features_df = pd.DataFrame({
            'task_id': ['t1', 't2', 't3'],
            'feature_a': [1.0, 2.0, 3.0]
        })
        features_path = tmpdir_path / "features.csv"
        features_df.to_csv(features_path, index=False)
        
        # Create ground truth CSV with task_ids t4-t6
        ground_truth_df = pd.DataFrame({
            'task_id': ['t4', 't5', 't6'],
            'dynamic_execution_outcome': ['Pass', 'Fail', 'Pass']
        })
        ground_truth_path = tmpdir_path / "ground_truth.csv"
        ground_truth_df.to_csv(ground_truth_path, index=False)
        
        # Should raise ValueError
        try:
            calculate_correlations(str(features_path), str(ground_truth_path))
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "No overlapping task_ids" in str(e)

def test_calculate_correlations_missing_file():
    """Test error handling for missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            calculate_correlations(
                str(Path(tmpdir) / "nonexistent.csv"),
                str(Path(tmpdir) / "nonexistent2.csv")
            )
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected