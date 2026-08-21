"""
Unit tests for sensitivity analysis module (T024).
"""
import pytest
import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from sensitivity_analysis import determine_significance, run_sensitivity_analysis, load_corrected_p_values


class TestDetermineSignificance:
    """Tests for the determine_significance function."""

    def test_p_value_less_than_alpha(self):
        """Test that p < alpha returns True."""
        assert determine_significance(0.04, 0.05) is True
        assert determine_significance(0.001, 0.05) is True

    def test_p_value_equal_to_alpha(self):
        """Test that p == alpha returns True."""
        assert determine_significance(0.05, 0.05) is True

    def test_p_value_greater_than_alpha(self):
        """Test that p > alpha returns False."""
        assert determine_significance(0.06, 0.05) is False
        assert determine_significance(0.1, 0.05) is False


class TestLoadCorrectedPValues:
    """Tests for loading corrected p-values."""

    @patch('sensitivity_analysis.RESULTS_DIR', Path('/tmp/test_results'))
    def test_load_from_file(self, tmp_path):
        """Test loading p-values from a CSV file."""
        # Create a mock corrected_p_values.csv
        p_values_dir = tmp_path / 'p_values'
        p_values_dir.mkdir(parents=True)
        csv_path = p_values_dir / 'corrected_p_values.csv'
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
            writer.writerow([1, 'NDCG@10', 0.03, 0.04, 'True'])
            writer.writerow([2, 'MAP', 0.06, 0.07, 'False'])
        
        # Mock the RESULTS_DIR to point to our temp directory
        with patch('sensitivity_analysis.RESULTS_DIR', tmp_path):
            data = load_corrected_p_values()
            
            assert len(data) == 2
            assert data[0]['query_id'] == 1
            assert data[0]['metric'] == 'NDCG@10'
            assert data[0]['corrected_p'] == 0.04
            assert data[0]['is_significant'] is True
            assert data[1]['query_id'] == 2
            assert data[1]['is_significant'] is False

    @patch('sensitivity_analysis.RESULTS_DIR', Path('/tmp/test_results'))
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        with patch('sensitivity_analysis.RESULTS_DIR', Path('/nonexistent')):
            with pytest.raises(FileNotFoundError):
                load_corrected_p_values()


class TestRunSensitivityAnalysis:
    """Tests for the sensitivity analysis runner."""

    def test_alpha_sweep_logic(self):
        """Test that the sensitivity analysis correctly counts significant queries."""
        # We'll mock the load_corrected_p_values function to return known data
        mock_data = [
            {'query_id': 1, 'metric': 'NDCG@10', 'corrected_p': 0.03, 'is_significant': True},
            {'query_id': 2, 'metric': 'MAP', 'corrected_p': 0.04, 'is_significant': True},
            {'query_id': 3, 'metric': 'NDCG@10', 'corrected_p': 0.06, 'is_significant': False},
            {'query_id': 4, 'metric': 'MAP', 'corrected_p': 0.08, 'is_significant': False},
        ]

        with patch('sensitivity_analysis.load_corrected_p_values', return_value=mock_data):
            # Test with a specific alpha range
            alpha_range = [0.02, 0.05, 0.1]
            results = run_sensitivity_analysis(alpha_range=alpha_range)
            
            assert len(results) == 3
            
            # At alpha=0.02: only p=0.03 and p=0.04 are > 0.02, so 0 significant
            # Wait, 0.03 > 0.02, 0.04 > 0.02, so 0 significant
            assert results[0]['alpha'] == 0.02
            assert results[0]['significant_count'] == 0
            
            # At alpha=0.05: p=0.03 and p=0.04 are <= 0.05, so 2 significant
            assert results[1]['alpha'] == 0.05
            assert results[1]['significant_count'] == 2
            
            # At alpha=0.1: all p-values are <= 0.1, so 4 significant
            assert results[2]['alpha'] == 0.1
            assert results[2]['significant_count'] == 4

    def test_default_alpha_range(self):
        """Test that default alpha range is used when not specified."""
        mock_data = [
            {'query_id': 1, 'metric': 'NDCG@10', 'corrected_p': 0.05, 'is_significant': True},
        ]

        with patch('sensitivity_analysis.load_corrected_p_values', return_value=mock_data):
            # Call without alpha_range to use default
            results = run_sensitivity_analysis()
            
            # Default range has 12 values
            assert len(results) == 12
            
            # Check that the first alpha is 0.001
            assert results[0]['alpha'] == 0.001
            
            # Check that the last alpha is 0.1
            assert results[-1]['alpha'] == 0.1