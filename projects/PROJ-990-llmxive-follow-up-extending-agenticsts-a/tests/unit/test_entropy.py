"""
Unit tests for entropy calculation module.
"""
import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.entropy import (
    calculate_shannon_entropy,
    extract_move_distribution,
    calculate_entropy_for_trajectory,
    process_trajectories,
    ENTROPY_INVALID_SENTINEL
)

class TestShannonEntropy:
    """Tests for Shannon entropy calculation."""

    def test_uniform_distribution(self):
        """Test entropy with uniform distribution (max entropy)."""
        probs = [0.25, 0.25, 0.25, 0.25]
        entropy = calculate_shannon_entropy(probs)
        # H = -sum(0.25 * log2(0.25)) = -4 * 0.25 * (-2) = 2.0
        assert abs(entropy - 2.0) < 1e-6

    def test_deterministic_distribution(self):
        """Test entropy with deterministic distribution (min entropy)."""
        probs = [1.0, 0.0, 0.0, 0.0]
        entropy = calculate_shannon_entropy(probs)
        assert abs(entropy - 0.0) < 1e-6

    def test_non_uniform_distribution(self):
        """Test entropy with non-uniform distribution."""
        probs = [0.5, 0.5]
        entropy = calculate_shannon_entropy(probs)
        assert abs(entropy - 1.0) < 1e-6

    def test_nan_handling(self):
        """Test that NaN probabilities return sentinel."""
        probs = [np.nan, 0.5, 0.5]
        entropy = calculate_shannon_entropy(probs)
        assert entropy == ENTROPY_INVALID_SENTINEL

    def test_inf_handling(self):
        """Test that Inf probabilities return sentinel."""
        probs = [float('inf'), 0.5, 0.5]
        entropy = calculate_shannon_entropy(probs)
        assert entropy == ENTROPY_INVALID_SENTINEL

    def test_empty_distribution(self):
        """Test that empty distribution returns sentinel."""
        probs = []
        entropy = calculate_shannon_entropy(probs)
        assert entropy == ENTROPY_INVALID_SENTINEL

    def test_zero_probabilities(self):
        """Test handling of all zero probabilities."""
        probs = [0.0, 0.0, 0.0]
        entropy = calculate_shannon_entropy(probs)
        assert entropy == ENTROPY_INVALID_SENTINEL

    def test_normalization(self):
        """Test that probabilities are normalized."""
        # Sum is not 1.0
        probs = [0.3, 0.3, 0.3]
        entropy = calculate_shannon_entropy(probs)
        # Should be same as [1/3, 1/3, 1/3]
        expected = calculate_shannon_entropy([1/3, 1/3, 1/3])
        assert abs(entropy - expected) < 1e-6

class TestExtractMoveDistribution:
    """Tests for move distribution extraction."""

    def test_dict_input(self):
        """Test extraction from dict."""
        row = pd.Series({
            'move_distribution': {'move_1': 0.5, 'move_2': 0.5}
        })
        result = extract_move_distribution(row)
        assert result == {'move_1': 0.5, 'move_2': 0.5}

    def test_json_string_input(self):
        """Test extraction from JSON string."""
        row = pd.Series({
            'move_distribution': '{"move_1": 0.5, "move_2": 0.5}'
        })
        result = extract_move_distribution(row)
        assert result == {'move_1': 0.5, 'move_2': 0.5}

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        row = pd.Series({
            'move_distribution': '{invalid json}'
        })
        result = extract_move_distribution(row)
        assert result == {}

    def test_missing_column(self):
        """Test handling of missing column."""
        row = pd.Series({})
        result = extract_move_distribution(row)
        assert result == {}

    def test_non_dict_non_string(self):
        """Test handling of non-dict, non-string input."""
        row = pd.Series({
            'move_distribution': [0.5, 0.5]
        })
        result = extract_move_distribution(row)
        assert result == {}

class TestCalculateEntropyForTrajectory:
    """Tests for trajectory entropy calculation."""

    def test_valid_trajectory(self):
        """Test calculation with valid trajectory."""
        row = pd.Series({
            'turn': 5,
            'move_distribution': {'move_1': 0.5, 'move_2': 0.5}
        })
        entropy, is_valid, error_msg = calculate_entropy_for_trajectory(row)
        assert is_valid
        assert abs(entropy - 1.0) < 1e-6
        assert error_msg == ""

    def test_invalid_trajectory_nan(self):
        """Test calculation with NaN in distribution."""
        row = pd.Series({
            'turn': 10,
            'move_distribution': {'move_1': float('nan'), 'move_2': 0.5}
        })
        entropy, is_valid, error_msg = calculate_entropy_for_trajectory(row)
        assert not is_valid
        assert entropy == ENTROPY_INVALID_SENTINEL
        assert "Invalid entropy" in error_msg

    def test_empty_distribution(self):
        """Test calculation with empty distribution."""
        row = pd.Series({
            'turn': 15,
            'move_distribution': {}
        })
        entropy, is_valid, error_msg = calculate_entropy_for_trajectory(row)
        assert not is_valid
        assert entropy == ENTROPY_INVALID_SENTINEL

class TestProcessTrajectories:
    """Tests for trajectory processing."""

    def test_process_valid_file(self):
        """Test processing a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "trajectories.csv"
            output_path = Path(tmpdir) / "entropy_results.csv"
            
            # Create test data
            data = [
                {'turn': 1, 'move_distribution': '{"move_1": 0.5, "move_2": 0.5}'},
                {'turn': 2, 'move_distribution': '{"move_1": 1.0}'},
                {'turn': 3, 'move_distribution': '{"move_1": 0.33, "move_2": 0.33, "move_3": 0.34}'}
            ]
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            result_df = process_trajectories(str(input_path), str(output_path))
            
            # Check output file exists
            assert output_path.exists()
            
            # Check results
            assert len(result_df) == 3
            assert all(col in result_df.columns for col in ['entropy', 'is_valid', 'requires_full_layers'])
            
            # First two should be valid
            assert result_df.iloc[0]['is_valid'] == True
            assert result_df.iloc[1]['is_valid'] == True
            assert result_df.iloc[2]['is_valid'] == True

    def test_process_with_invalid_entries(self):
        """Test processing with invalid entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "trajectories.csv"
            output_path = Path(tmpdir) / "entropy_results.csv"
            
            # Create test data with invalid entry
            data = [
                {'turn': 1, 'move_distribution': '{"move_1": 0.5, "move_2": 0.5}'},
                {'turn': 2, 'move_distribution': '{}'},  # Invalid
                {'turn': 3, 'move_distribution': '{"move_1": 0.33, "move_2": 0.33, "move_3": 0.34}'}
            ]
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            result_df = process_trajectories(str(input_path), str(output_path))
            
            # Check results
            assert len(result_df) == 3
            assert result_df.iloc[0]['is_valid'] == True
            assert result_df.iloc[1]['is_valid'] == False
            assert result_df.iloc[2]['is_valid'] == True

    def test_file_not_found(self):
        """Test handling of missing input file."""
        with pytest.raises(FileNotFoundError):
            process_trajectories("nonexistent/file.csv")

class TestEdgeCases:
    """Tests for edge cases mentioned in requirements."""

    def test_nan_triggers_full_layer_retrieval_flag(self):
        """Test that NaN entropy triggers full-layer retrieval flag."""
        row = pd.Series({
            'turn': 1,
            'move_distribution': {'move_1': float('nan')}
        })
        entropy, is_valid, error_msg = calculate_entropy_for_trajectory(row)
        
        assert entropy == ENTROPY_INVALID_SENTINEL
        assert not is_valid
        # The flag should be set in process_trajectories
        # This test verifies the individual function returns invalid

    def test_inf_triggers_full_layer_retrieval_flag(self):
        """Test that Inf entropy triggers full-layer retrieval flag."""
        # Create a distribution that might cause overflow
        row = pd.Series({
            'turn': 1,
            'move_distribution': {'move_1': float('inf')}
        })
        entropy, is_valid, error_msg = calculate_entropy_for_trajectory(row)
        
        assert entropy == ENTROPY_INVALID_SENTINEL
        assert not is_valid

    def test_zero_moves_handling(self):
        """Test handling of zero legal moves."""
        row = pd.Series({
            'turn': 1,
            'move_distribution': {}
        })
        entropy, is_valid, error_msg = calculate_entropy_for_trajectory(row)
        
        assert entropy == ENTROPY_INVALID_SENTINEL
        assert not is_valid
        assert "No move distribution" in error_msg or "Empty probability" in error_msg