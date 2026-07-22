import pytest
import numpy as np
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
import sys
import logging

# Add parent directory to path to import entropy module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from entropy import calculate_shannon_entropy, extract_move_distribution, calculate_entropy_for_trajectory, process_trajectories

# Configure logging to capture warnings
logging.basicConfig(level=logging.WARNING)

class TestCalculateShannonEntropy:
    """Unit tests for Shannon entropy calculation."""

    def test_uniform_distribution(self):
        """Test entropy calculation for uniform distribution."""
        # Uniform distribution of 4 moves: each has probability 0.25
        probs = [0.25, 0.25, 0.25, 0.25]
        entropy = calculate_shannon_entropy(probs)
        
        # Expected entropy: -4 * 0.25 * log(0.25) = log(4) ≈ 1.386
        expected = -4 * 0.25 * np.log(0.25)
        assert abs(entropy - expected) < 1e-6, f"Expected {expected}, got {entropy}"

    def test_deterministic_distribution(self):
        """Test entropy calculation for deterministic distribution (one move with prob 1)."""
        probs = [1.0, 0.0, 0.0]
        entropy = calculate_shannon_entropy(probs)
        
        # Expected entropy: 0 (no uncertainty)
        assert abs(entropy) < 1e-6, f"Expected 0, got {entropy}"

    def test_nan_handling(self):
        """Test that NaN probabilities are handled correctly."""
        # This should not crash and should return inf
        probs = [float('nan'), 0.5, 0.5]
        entropy = calculate_shannon_entropy(probs)
        
        # NaN in input should result in inf output
        assert np.isinf(entropy), f"Expected inf for NaN input, got {entropy}"

    def test_inf_handling(self):
        """Test that Inf probabilities are handled correctly."""
        # This should not crash and should return inf
        probs = [float('inf'), 0.0, 0.0]
        entropy = calculate_shannon_entropy(probs)
        
        # Invalid probabilities should result in inf
        assert np.isinf(entropy), f"Expected inf for invalid input, got {entropy}"

    def test_empty_distribution(self):
        """Test entropy calculation for empty distribution."""
        probs = []
        entropy = calculate_shannon_entropy(probs)
        
        # Empty distribution should return inf
        assert np.isinf(entropy), f"Expected inf for empty distribution, got {entropy}"

    def test_single_move(self):
        """Test entropy calculation for single move."""
        probs = [1.0]
        entropy = calculate_shannon_entropy(probs)
        
        # Single move should have 0 entropy
        assert abs(entropy) < 1e-6, f"Expected 0, got {entropy}"

    def test_numpy_array_input(self):
        """Test that numpy arrays are accepted as input."""
        probs = np.array([0.5, 0.5])
        entropy = calculate_shannon_entropy(probs)
        
        # Expected: -2 * 0.5 * log(0.5) = log(2) ≈ 0.693
        expected = -2 * 0.5 * np.log(0.5)
        assert abs(entropy - expected) < 1e-6, f"Expected {expected}, got {entropy}"

class TestExtractMoveDistribution:
    """Unit tests for move distribution extraction."""

    def test_extract_from_json_string(self):
        """Test extraction from JSON string."""
        row = pd.Series({
            'trajectory_id': 'test1',
            'legal_move_distribution': json.dumps([0.2, 0.3, 0.5])
        })
        
        result = extract_move_distribution(row)
        assert result == [0.2, 0.3, 0.5], f"Expected [0.2, 0.3, 0.5], got {result}"

    def test_extract_from_list(self):
        """Test extraction from list."""
        row = pd.Series({
            'trajectory_id': 'test1',
            'legal_move_distribution': [0.1, 0.9]
        })
        
        result = extract_move_distribution(row)
        assert result == [0.1, 0.9], f"Expected [0.1, 0.9], got {result}"

    def test_extract_from_alternative_column(self):
        """Test extraction from alternative column name."""
        row = pd.Series({
            'trajectory_id': 'test1',
            'move_distribution': [0.4, 0.6]
        })
        
        result = extract_move_distribution(row)
        assert result == [0.4, 0.6], f"Expected [0.4, 0.6], got {result}"

    def test_no_distribution_found(self):
        """Test when no distribution column is found."""
        row = pd.Series({
            'trajectory_id': 'test1',
            'other_column': 'value'
        })
        
        result = extract_move_distribution(row)
        assert result is None, f"Expected None, got {result}"

class TestCalculateEntropyForTrajectory:
    """Unit tests for trajectory-level entropy calculation."""

    def test_multiple_turns(self):
        """Test calculation across multiple turns."""
        trajectory_id = 'test_traj'
        turns = [
            {'turn_index': 0, 'legal_move_distribution': [0.5, 0.5]},
            {'turn_index': 1, 'legal_move_distribution': [0.25, 0.25, 0.25, 0.25]},
            {'turn_index': 2, 'legal_move_distribution': [1.0]}
        ]
        
        results = calculate_entropy_for_trajectory(trajectory_id, turns)
        
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # Check specific entropy values
        # Turn 0: log(2) ≈ 0.693
        assert abs(results[0][1] - np.log(2)) < 1e-6
        # Turn 1: log(4) ≈ 1.386
        assert abs(results[1][1] - np.log(4)) < 1e-6
        # Turn 2: 0
        assert abs(results[2][1]) < 1e-6

    def test_missing_distribution(self):
        """Test handling of turns with missing distribution."""
        trajectory_id = 'test_traj'
        turns = [
            {'turn_index': 0, 'legal_move_distribution': [0.5, 0.5]},
            {'turn_index': 1},  # Missing distribution
            {'turn_index': 2, 'legal_move_distribution': [1.0]}
        ]
        
        results = calculate_entropy_for_trajectory(trajectory_id, turns)
        
        # Should only have 2 results (turns 0 and 2)
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"
        assert results[0][0] == 0
        assert results[1][0] == 2

class TestProcessTrajectories:
    """Integration tests for the full trajectory processing pipeline."""

    def test_process_valid_csv(self):
        """Test processing a valid CSV file."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('trajectory_id,turn_index,legal_move_distribution\n')
            f.write('traj1,0,"[0.5, 0.5]"\n')
            f.write('traj1,1,"[0.25, 0.25, 0.25, 0.25]"\n')
            f.write('traj2,0,"[1.0]"\n')
            input_path = f.name

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            result_df = process_trajectories(input_path, output_path)
            
            # Check output
            assert len(result_df) == 3, f"Expected 3 rows, got {len(result_df)}"
            assert 'entropy' in result_df.columns
            assert 'trajectory_id' in result_df.columns
            assert 'turn_index' in result_df.columns
            
            # Verify entropy values
            assert abs(result_df.iloc[0]['entropy'] - np.log(2)) < 1e-6
            assert abs(result_df.iloc[1]['entropy'] - np.log(4)) < 1e-6
            assert abs(result_df.iloc[2]['entropy']) < 1e-6

        finally:
            # Cleanup
            os.unlink(input_path)
            os.unlink(output_path)
            # Also check for warning log file
            log_path = Path(output_path).parent / 'edge_case_warnings.log'
            if log_path.exists():
                os.unlink(log_path)

    def test_process_with_nan_entropy(self):
        """Test processing that results in NaN/Inf entropy."""
        # Create temporary input file with problematic data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('trajectory_id,turn_index,legal_move_distribution\n')
            f.write('traj1,0,"[0.5, 0.5]"\n')
            f.write('traj1,1,"[1.0]"\n')  # This is valid, but we'll add a warning case
            input_path = f.name

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            result_df = process_trajectories(input_path, output_path)
            
            # Check that output was created
            assert os.path.exists(output_path), "Output file was not created"
            assert len(result_df) == 2, f"Expected 2 rows, got {len(result_df)}"

        finally:
            # Cleanup
            os.unlink(input_path)
            os.unlink(output_path)
            # Also check for warning log file
            log_path = Path(output_path).parent / 'edge_case_warnings.log'
            if log_path.exists():
                os.unlink(log_path)

    def test_missing_input_file(self):
        """Test error handling for missing input file."""
        with pytest.raises(FileNotFoundError):
            process_trajectories('/nonexistent/path/input.csv', '/tmp/output.csv')

    def test_missing_distribution_column(self):
        """Test error handling for missing distribution column."""
        # Create temporary input file without distribution column
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('trajectory_id,turn_index,other_column\n')
            f.write('traj1,0,value\n')
            input_path = f.name

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(ValueError, match="Could not find move distribution column"):
                process_trajectories(input_path, output_path)
        finally:
            # Cleanup
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)