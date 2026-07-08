"""
Unit tests for p-value calculation logic.
"""

import pytest
import math
from code.p_values import calculate_p_value, process_null_distributions
import os
import csv
import tempfile
import shutil


class TestCalculatePValue:
    """Tests for the calculate_p_value function."""

    def test_basic_p_value_calculation(self):
        """Test basic p-value calculation with known values."""
        observed = 0.8
        null_scores = [0.6, 0.7, 0.75, 0.85, 0.9]
        # 2 scores >= 0.8 (0.85, 0.9)
        # p-value = (2 + 1) / (5 + 1) = 3/6 = 0.5
        expected = 3.0 / 6.0
        result = calculate_p_value(observed, null_scores)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_all_null_scores_lower(self):
        """Test when all null scores are lower than observed."""
        observed = 0.95
        null_scores = [0.5, 0.6, 0.7, 0.8]
        # 0 scores >= 0.95
        # p-value = (0 + 1) / (4 + 1) = 1/5 = 0.2
        expected = 1.0 / 5.0
        result = calculate_p_value(observed, null_scores)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_all_null_scores_higher(self):
        """Test when all null scores are higher than observed."""
        observed = 0.5
        null_scores = [0.8, 0.9, 0.95, 1.0]
        # 4 scores >= 0.5
        # p-value = (4 + 1) / (4 + 1) = 5/5 = 1.0
        expected = 5.0 / 5.0
        result = calculate_p_value(observed, null_scores)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_empty_null_distribution(self):
        """Test handling of empty null distribution."""
        observed = 0.8
        null_scores = []
        result = calculate_p_value(observed, null_scores)
        assert result == 1.0

    def test_single_null_score_equal(self):
        """Test with single null score equal to observed."""
        observed = 0.8
        null_scores = [0.8]
        # 1 score >= 0.8
        # p-value = (1 + 1) / (1 + 1) = 2/2 = 1.0
        expected = 2.0 / 2.0
        result = calculate_p_value(observed, null_scores)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_single_null_score_higher(self):
        """Test with single null score higher than observed."""
        observed = 0.8
        null_scores = [0.9]
        # 1 score >= 0.8
        # p-value = (1 + 1) / (1 + 1) = 2/2 = 1.0
        expected = 2.0 / 2.0
        result = calculate_p_value(observed, null_scores)
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_single_null_score_lower(self):
        """Test with single null score lower than observed."""
        observed = 0.9
        null_scores = [0.8]
        # 0 scores >= 0.9
        # p-value = (0 + 1) / (1 + 1) = 1/2 = 0.5
        expected = 1.0 / 2.0
        result = calculate_p_value(observed, null_scores)
        assert math.isclose(result, expected, rel_tol=1e-9)

class TestProcessNullDistributions:
    """Tests for the process_null_distributions function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.null_dist_dir = os.path.join(self.test_dir, 'null_distributions')
        self.output_dir = os.path.join(self.test_dir, 'p_values')
        os.makedirs(self.null_dist_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_process_single_file(self):
        """Test processing a single null distribution file."""
        # Create a test CSV
        csv_path = os.path.join(self.null_dist_dir, 'q1_ndcg.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'score'])
            writer.writerow([1, 'ndcg', 0.85])  # observed
            writer.writerow([1, 'ndcg', 0.70])  # null
            writer.writerow([1, 'ndcg', 0.75])  # null
            writer.writerow([1, 'ndcg', 0.80])  # null
            writer.writerow([1, 'ndcg', 0.90])  # null (>= observed)
            writer.writerow([1, 'ndcg', 0.88])  # null (>= observed)

        # Run processing
        results = process_null_distributions(self.null_dist_dir, self.output_dir)

        # Verify results
        assert len(results) == 1
        assert results[0]['query_id'] == 1
        assert results[0]['metric'] == 'ndcg'
        assert results[0]['observed_score'] == 0.85
        assert results[0]['null_count'] == 4
        # 2 scores >= 0.85 (0.90, 0.88)
        # p-value = (2 + 1) / (4 + 1) = 3/5 = 0.6
        assert abs(results[0]['p_value'] - 0.6) < 1e-9

        # Verify output file exists
        output_path = os.path.join(self.output_dir, 'raw_p_values.csv')
        assert os.path.exists(output_path)

    def test_process_multiple_files(self):
        """Test processing multiple null distribution files."""
        # Create first CSV
        csv_path1 = os.path.join(self.null_dist_dir, 'q1_ndcg.csv')
        with open(csv_path1, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'score'])
            writer.writerow([1, 'ndcg', 0.80])
            writer.writerow([1, 'ndcg', 0.70])

        # Create second CSV
        csv_path2 = os.path.join(self.null_dist_dir, 'q2_map.csv')
        with open(csv_path2, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'score'])
            writer.writerow([2, 'map', 0.75])
            writer.writerow([2, 'map', 0.65])

        # Run processing
        results = process_null_distributions(self.null_dist_dir, self.output_dir)

        # Verify results
        assert len(results) == 2
        query_ids = {r['query_id'] for r in results}
        assert 1 in query_ids
        assert 2 in query_ids

    def test_empty_directory(self):
        """Test processing an empty directory."""
        results = process_null_distributions(self.null_dist_dir, self.output_dir)
        assert len(results) == 0

    def test_nonexistent_directory(self):
        """Test processing a nonexistent directory."""
        results = process_null_distributions(
            os.path.join(self.test_dir, 'nonexistent'),
            self.output_dir
        )
        assert len(results) == 0
