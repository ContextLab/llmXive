"""
Unit tests for entropy calculation module.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from entropy import (
    calculate_shannon_entropy,
    extract_move_distribution,
    calculate_entropy_for_trajectory,
    SENTINEL_VALUE
)

class TestCalculateShannonEntropy:
    def test_uniform_distribution(self):
        """Test with a uniform distribution (max entropy)."""
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = calculate_shannon_entropy(probs)
        expected = 2.0  # log2(4)
        assert abs(entropy - expected) < 1e-6

    def test_deterministic_distribution(self):
        """Test with a deterministic distribution (zero entropy)."""
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = calculate_shannon_entropy(probs)
        assert entropy == 0.0

    def test_nan_handling(self):
        """Test that NaN probabilities are handled."""
        probs = np.array([0.5, np.nan, 0.5])
        # Should filter out NaN and calculate on remaining
        entropy = calculate_shannon_entropy(probs)
        # Should be 1.0 (binary uniform)
        assert abs(entropy - 1.0) < 1e-6

    def test_empty_distribution(self):
        """Test with empty array."""
        probs = np.array([])
        entropy = calculate_shannon_entropy(probs)
        assert entropy == SENTINEL_VALUE

    def test_inf_result(self):
        """Test case that might produce Inf (e.g., very small probabilities)."""
        # This is hard to trigger with normalized probabilities, but we test the check
        probs = np.array([1e-10, 1 - 1e-10])
        entropy = calculate_shannon_entropy(probs)
        # Should be a valid small number, not SENTINEL
        assert entropy != SENTINEL_VALUE
        assert entropy > 0

class TestExtractMoveDistribution:
    def test_json_list(self):
        """Test parsing a JSON list of counts."""
        input_str = "[10, 20, 30]"
        dist = extract_move_distribution(input_str)
        expected = np.array([1/6, 2/6, 3/6])
        np.testing.assert_array_almost_equal(dist, expected)

    def test_json_dict(self):
        """Test parsing a JSON dictionary of counts."""
        input_str = '{"a": 10, "b": 20, "c": 30}'
        dist = extract_move_distribution(input_str)
        expected = np.array([1/6, 2/6, 3/6])
        np.testing.assert_array_almost_equal(dist, expected)

    def test_csv_format(self):
        """Test parsing CSV-like format."""
        input_str = "a:0.1,b:0.2,c:0.7"
        dist = extract_move_distribution(input_str)
        expected = np.array([0.1, 0.2, 0.7])
        np.testing.assert_array_almost_equal(dist, expected)

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        input_str = "not json at all"
        dist = extract_move_distribution(input_str)
        # Should return empty array or handle gracefully
        assert len(dist) == 0

    def test_zero_total(self):
        """Test with zero total counts."""
        input_str = "[0, 0, 0]"
        dist = extract_move_distribution(input_str)
        assert np.all(dist == 0)

class TestCalculateEntropyForTrajectory:
    def test_valid_row(self):
        """Test with a valid row containing legal moves."""
        row = pd.Series({
            'trajectory_id': 'test_1',
            'turn': 1,
            'legal_moves': '[0.25, 0.25, 0.25, 0.25]'
        })
        entropy = calculate_entropy_for_trajectory(row)
        assert abs(entropy - 2.0) < 1e-6
        assert entropy != SENTINEL_VALUE

    def test_missing_legal_moves(self):
        """Test with missing legal_moves."""
        row = pd.Series({
            'trajectory_id': 'test_2',
            'turn': 1
        })
        entropy = calculate_entropy_for_trajectory(row)
        assert entropy == SENTINEL_VALUE

    def test_empty_legal_moves(self):
        """Test with empty legal_moves string."""
        row = pd.Series({
            'trajectory_id': 'test_3',
            'turn': 1,
            'legal_moves': ''
        })
        entropy = calculate_entropy_for_trajectory(row)
        assert entropy == SENTINEL_VALUE

    def test_invalid_legal_moves_format(self):
        """Test with invalid legal_moves format."""
        row = pd.Series({
            'trajectory_id': 'test_4',
            'turn': 1,
            'legal_moves': 'invalid_format'
        })
        entropy = calculate_entropy_for_trajectory(row)
        assert entropy == SENTINEL_VALUE

class TestIntegration:
    def test_end_to_end(self):
        """Test the full pipeline with a temporary file."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("trajectory_id,turn,legal_moves\n")
            f.write("t1,1,[0.5, 0.5]\n")
            f.write("t2,2,[1.0, 0.0, 0.0]\n")
            f.write("t3,3,invalid\n")
            input_path = Path(f.name)

        output_path = input_path.parent / "output.csv"

        try:
            # Import process_trajectories for testing
            from entropy import process_trajectories
            df = process_trajectories(input_path, output_path)

            # Verify output
            assert len(df) == 3
            assert 'entropy' in df.columns
            assert 'is_valid' in df.columns

            # Check specific values
            assert df.iloc[0]['entropy'] == 1.0  # binary uniform
            assert df.iloc[0]['is_valid'] == True
            assert df.iloc[1]['entropy'] == 0.0  # deterministic
            assert df.iloc[1]['is_valid'] == True
            assert df.iloc[2]['is_valid'] == False  # invalid format

            # Verify file was written
            assert output_path.exists()
        finally:
            # Cleanup
            input_path.unlink()
            if output_path.exists():
                output_path.unlink()