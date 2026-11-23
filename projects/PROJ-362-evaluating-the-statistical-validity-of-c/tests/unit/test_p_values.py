"""
Unit tests for p-value calculation logic in p_values.py.
"""
import pytest
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

# Import the module under test
import sys
# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from p_values import calculate_p_value, process_null_distributions, run_p_value_calculation
from config import RESULTS_DIR

class TestCalculatePValue:
    """Tests for the calculate_p_value function."""

    def test_p_value_basic(self):
        """Test basic p-value calculation."""
        observed = 0.5
        null_scores = [0.4, 0.45, 0.55, 0.6, 0.3]
        # r = count(null >= observed) = 2 (0.55, 0.6)
        # p = (2 + 1) / (5 + 1) = 3/6 = 0.5
        expected = 0.5
        result = calculate_p_value(observed, null_scores)
        assert result == expected

    def test_p_value_all_lower(self):
        """Test when all null scores are lower than observed."""
        observed = 0.9
        null_scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        # r = 0
        # p = (0 + 1) / (5 + 1) = 1/6
        expected = 1.0 / 6.0
        result = calculate_p_value(observed, null_scores)
        assert result == expected

    def test_p_value_all_higher(self):
        """Test when all null scores are higher than observed."""
        observed = 0.1
        null_scores = [0.9, 0.8, 0.7, 0.6, 0.5]
        # r = 5
        # p = (5 + 1) / (5 + 1) = 1.0
        expected = 1.0
        result = calculate_p_value(observed, null_scores)
        assert result == expected

    def test_p_value_single_permutation(self):
        """Test with a single permutation."""
        observed = 0.5
        null_scores = [0.6]
        # r = 1
        # p = (1 + 1) / (1 + 1) = 1.0
        expected = 1.0
        result = calculate_p_value(observed, null_scores)
        assert result == expected

    def test_p_value_empty_null_distribution(self):
        """Test that empty null distribution raises ValueError."""
        with pytest.raises(ValueError, match="Null distribution cannot be empty"):
            calculate_p_value(0.5, [])

class TestProcessNullDistributions:
    """Tests for the process_null_distributions function."""

    def test_process_with_mock_files(self):
        """Test processing of mock null distribution files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock null distribution files
            # qrels_1_ndcg_null_dist.csv
            null_file_1 = tmpdir_path / "qrels_1_ndcg_null_dist.csv"
            with open(null_file_1, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'score'])
                writer.writeheader()
                writer.writerows([
                    {'query_id': '1', 'metric': 'ndcg', 'score': '0.4'},
                    {'query_id': '1', 'metric': 'ndcg', 'score': '0.5'},
                    {'query_id': '1', 'metric': 'ndcg', 'score': '0.6'},
                ])

            # qrels_2_map_null_dist.csv
            null_file_2 = tmpdir_path / "qrels_2_map_null_dist.csv"
            with open(null_file_2, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'score'])
                writer.writeheader()
                writer.writerows([
                    {'query_id': '2', 'metric': 'map', 'score': '0.3'},
                    {'query_id': '2', 'metric': 'map', 'score': '0.4'},
                ])

            # Create observed scores file
            obs_file = tmpdir_path / "observed_scores.csv"
            with open(obs_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'observed_score'])
                writer.writeheader()
                writer.writerows([
                    {'query_id': '1', 'metric': 'ndcg', 'observed_score': '0.55'},
                    {'query_id': '2', 'metric': 'map', 'observed_score': '0.35'},
                ])

            # Process
            results = process_null_distributions(tmpdir_path, obs_file)

            # Verify results
            assert len(results) == 2

            # Check query 1, ndcg
            q1_result = next(r for r in results if r['query_id'] == '1' and r['metric'] == 'ndcg')
            # observed = 0.55, null = [0.4, 0.5, 0.6]
            # r = 1 (only 0.6 >= 0.55)
            # p = (1+1)/(3+1) = 0.5
            assert q1_result['p_value'] == 0.5
            assert q1_result['permutation_count'] == 3

            # Check query 2, map
            q2_result = next(r for r in results if r['query_id'] == '2' and r['metric'] == 'map')
            # observed = 0.35, null = [0.3, 0.4]
            # r = 1 (only 0.4 >= 0.35)
            # p = (1+1)/(2+1) = 2/3
            assert abs(q2_result['p_value'] - 2/3) < 1e-6
            assert q2_result['permutation_count'] == 2

    def test_process_missing_observed_scores(self):
        """Test behavior when observed scores file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a null distribution file
            null_file = tmpdir_path / "qrels_1_ndcg_null_dist.csv"
            with open(null_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'score'])
                writer.writeheader()
                writer.writerows([
                    {'query_id': '1', 'metric': 'ndcg', 'score': '0.5'},
                ])

            # Process without observed scores file
            results = process_null_distributions(tmpdir_path, observed_scores_file=None)

            # Should still return results, but with observed_score = 0.0
            assert len(results) == 1
            assert results[0]['observed_score'] == 0.0
            # If observed=0.0 and null=[0.5], r=1, p=(1+1)/(1+1)=1.0
            assert results[0]['p_value'] == 1.0

class TestRunPValueCalculation:
    """Tests for the run_p_value_calculation function."""

    def test_run_and_save(self):
        """Test running calculation and saving to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create null distribution
            null_file = tmpdir_path / "qrels_100_ndcg_null_dist.csv"
            with open(null_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'score'])
                writer.writeheader()
                writer.writerows([
                    {'query_id': '100', 'metric': 'ndcg', 'score': '0.1'},
                    {'query_id': '100', 'metric': 'ndcg', 'score': '0.2'},
                    {'query_id': '100', 'metric': 'ndcg', 'score': '0.3'},
                ])

            # Create observed scores
            obs_file = tmpdir_path / "observed_scores.csv"
            with open(obs_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'observed_score'])
                writer.writeheader()
                writer.writerows([
                    {'query_id': '100', 'metric': 'ndcg', 'observed_score': '0.25'},
                ])

            output_file = tmpdir_path / "raw_p_values.csv"

            # Run
            results = run_p_value_calculation(
                null_dist_dir=tmpdir_path,
                observed_scores_file=obs_file,
                output_file=output_file
            )

            # Verify results
            assert len(results) == 1
            assert results[0]['p_value'] == 0.5  # (1+1)/(3+1) = 0.5

            # Verify file was created
            assert output_file.exists()
            
            # Verify file contents
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert float(rows[0]['p_value']) == 0.5
                assert rows[0]['query_id'] == '100'
                assert rows[0]['metric'] == 'ndcg'