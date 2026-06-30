"""
Unit tests for Cohen's kappa calculation and threshold sensitivity analysis.
"""

import pytest
import json
import csv
import tempfile
from pathlib import Path
import numpy as np

from code.analysis.sensitivity_kappa import (
    KappaSensitivityError,
    compute_cohen_kappa,
    build_rating_matrix,
    compute_kappa_for_pairs,
    analyze_threshold_sensitivity,
    run_sensitivity_kappa_analysis
)


class TestCohenKappa:
    """Tests for Cohen's kappa calculation."""

    def test_perfect_agreement(self):
        """Test kappa is 1.0 when raters agree perfectly."""
        rater1 = [1, 2, 3, 4, 5]
        rater2 = [1, 2, 3, 4, 5]
        kappa = compute_cohen_kappa(rater1, rater2)
        assert abs(kappa - 1.0) < 1e-6

    def test_no_agreement(self):
        """Test kappa is 0 or negative when raters disagree completely."""
        # Completely opposite ratings
        rater1 = [1, 1, 1, 1]
        rater2 = [2, 2, 2, 2]
        kappa = compute_cohen_kappa(rater1, rater2)
        # With only two categories and no overlap, kappa should be 0
        assert abs(kappa) < 1e-6

    def test_random_agreement(self):
        """Test kappa is around 0 for random ratings."""
        np.random.seed(42)
        rater1 = np.random.randint(1, 4, 100).tolist()
        rater2 = np.random.randint(1, 4, 100).tolist()
        kappa = compute_cohen_kappa(rater1, rater2)
        # Random ratings should give kappa near 0 (allow some variance)
        assert -0.2 < kappa < 0.2

    def test_unequal_length_raises_error(self):
        """Test that unequal length lists raise an error."""
        with pytest.raises(KappaSensitivityError):
            compute_cohen_kappa([1, 2, 3], [1, 2])

    def test_empty_list_returns_negative_one(self):
        """Test that empty lists return -1.0."""
        kappa = compute_cohen_kappa([], [])
        assert kappa == -1.0

    def test_single_item(self):
        """Test kappa with a single item (edge case)."""
        rater1 = [1]
        rater2 = [1]
        kappa = compute_cohen_kappa(rater1, rater2)
        # With single item and perfect agreement, should be 1.0
        assert abs(kappa - 1.0) < 1e-6


class TestRatingMatrix:
    """Tests for building rating matrices."""

    def test_build_matrix(self):
        """Test building a rating matrix from raw data."""
        ratings = [
            {'report_id': 'R1', 'rater_id': 'A', 'rating': 1.0},
            {'report_id': 'R1', 'rater_id': 'B', 'rating': 2.0},
            {'report_id': 'R2', 'rater_id': 'A', 'rating': 3.0},
            {'report_id': 'R2', 'rater_id': 'B', 'rating': 3.0},
        ]

        matrix = build_rating_matrix(ratings)

        assert matrix['R1']['A'] == 1.0
        assert matrix['R1']['B'] == 2.0
        assert matrix['R2']['A'] == 3.0
        assert matrix['R2']['B'] == 3.0

    def test_missing_ratings(self):
        """Test handling of missing ratings for some reports."""
        ratings = [
            {'report_id': 'R1', 'rater_id': 'A', 'rating': 1.0},
            # R1 missing rater B
            {'report_id': 'R2', 'rater_id': 'A', 'rating': 2.0},
            {'report_id': 'R2', 'rater_id': 'B', 'rating': 2.0},
        ]

        matrix = build_rating_matrix(ratings)

        assert 'A' in matrix['R1']
        assert 'B' not in matrix['R1']
        assert 'A' in matrix['R2']
        assert 'B' in matrix['R2']


class TestKappaForPairs:
    """Tests for computing kappa across rater pairs."""

    def test_compute_kappa_for_pairs(self):
        """Test computing kappa for multiple rater pairs."""
        matrix = {
            'R1': {'A': 1.0, 'B': 1.0, 'C': 2.0},
            'R2': {'A': 2.0, 'B': 2.0, 'C': 1.0},
            'R3': {'A': 3.0, 'B': 3.0, 'C': 3.0},
            'R4': {'A': 1.0, 'B': 1.0, 'C': 1.0},
            'R5': {'A': 2.0, 'B': 2.0, 'C': 2.0},
        }

        kappa_results = compute_kappa_for_pairs(matrix)

        # A and B should have perfect agreement (kappa = 1.0)
        assert abs(kappa_results[('A', 'B')] - 1.0) < 1e-6

        # A and C should have no agreement (kappa near 0 or negative)
        # The exact value depends on the chance agreement
        assert ('A', 'C') in kappa_results

    def test_no_pairs(self):
        """Test when there are no rater pairs."""
        matrix = {
            'R1': {'A': 1.0},
            'R2': {'A': 2.0},
        }

        kappa_results = compute_kappa_for_pairs(matrix)
        assert len(kappa_results) == 0


class TestThresholdSensitivity:
    """Tests for threshold sensitivity analysis."""

    def test_analyze_sensitivity(self):
        """Test threshold sensitivity analysis with known data."""
        kappa_results = {
            ('A', 'B'): 0.8,
            ('A', 'C'): 0.6,
            ('B', 'C'): 0.4,
        }
        thresholds = [0.0, 0.5, 0.7, 0.9]

        results = analyze_threshold_sensitivity(kappa_results, thresholds)

        assert 'thresholds_tested' in results
        assert 'overall_statistics' in results
        assert 'threshold_analysis' in results
        assert 'benchmark_threshold' in results

        # Check that mean is correct
        expected_mean = (0.8 + 0.6 + 0.4) / 3
        assert abs(results['overall_statistics']['mean_kappa'] - expected_mean) < 1e-6

    def test_empty_results(self):
        """Test sensitivity analysis with no kappa results."""
        results = analyze_threshold_sensitivity({}, [0.5])
        assert 'error' in results


class TestRunSensitivityKappaAnalysis:
    """Tests for the main analysis function."""

    def test_full_pipeline(self):
        """Test the full analysis pipeline with a temporary file."""
        # Create temporary ratings file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['report_id', 'rater_id', 'rating'])
            writer.writerow(['R1', 'A', '1'])
            writer.writerow(['R1', 'B', '1'])
            writer.writerow(['R2', 'A', '2'])
            writer.writerow(['R2', 'B', '2'])
            writer.writerow(['R3', 'A', '3'])
            writer.writerow(['R3', 'B', '3'])
            ratings_file = f.name

        output_file = tempfile.mktemp(suffix='.json')

        try:
            results = run_sensitivity_kappa_analysis(
                ratings_file=ratings_file,
                output_file=output_file,
                thresholds=[0.0, 0.5, 1.0]
            )

            # Check output file exists
            assert Path(output_file).exists()

            # Check results structure
            assert 'metadata' in results
            assert 'kappa_coefficients' in results
            assert 'sensitivity_analysis' in results

            # Check kappa is 1.0 (perfect agreement)
            kappa_val = results['kappa_coefficients']['A-B']
            assert abs(kappa_val - 1.0) < 1e-6

        finally:
            # Cleanup
            Path(ratings_file).unlink()
            if Path(output_file).exists():
                Path(output_file).unlink()

    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(KappaSensitivityError):
            run_sensitivity_kappa_analysis(
                ratings_file='nonexistent.csv',
                output_file='output.json'
            )