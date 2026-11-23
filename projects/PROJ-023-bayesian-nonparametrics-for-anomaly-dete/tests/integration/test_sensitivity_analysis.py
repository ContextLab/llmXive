"""
Integration tests for sensitivity analysis script.

These tests verify that the sensitivity analysis script correctly:
- Loads predictions and ground truth
- Sweeps thresholds across the full range
- Calculates metrics accurately
- Outputs the expected JSON structure
"""

import json
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the script functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.sensitivity_analysis import (
    calculate_metrics_at_threshold,
    sweep_thresholds,
    find_optimal_threshold,
    run_analysis
)


class TestSensitivityAnalysisMetrics:
    """Test metric calculation functions."""

    def test_perfect_detection(self):
        """Test metrics when detection is perfect."""
        scores = np.array([0.9, 0.8, 0.7, 0.1, 0.2])
        labels = np.array([1, 1, 1, 0, 0])

        # At threshold 0.5, all should be correctly classified
        metrics = calculate_metrics_at_threshold(scores, labels, 0.5)

        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1_score'] == 1.0
        assert metrics['false_positive_rate'] == 0.0

    def test_no_detection(self):
        """Test metrics when no anomalies are detected."""
        scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        labels = np.array([1, 1, 1, 0, 0])

        # At threshold 0.9, no anomalies detected
        metrics = calculate_metrics_at_threshold(scores, labels, 0.9)

        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1_score'] == 0.0
        assert metrics['false_positive_rate'] == 0.0

    def test_all_detected(self):
        """Test metrics when everything is detected (high false positives)."""
        scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
        labels = np.array([1, 1, 1, 0, 0])

        # At threshold 0.0, everything detected
        metrics = calculate_metrics_at_threshold(scores, labels, 0.0)

        assert metrics['recall'] == 1.0
        assert metrics['false_positive_rate'] == 1.0
        # Precision should be 3/5 = 0.6
        assert abs(metrics['precision'] - 0.6) < 1e-6

    def test_boundary_case(self):
        """Test metrics at threshold boundary."""
        scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        labels = np.array([1, 1, 1, 0, 0])

        # At threshold exactly 0.5, behavior depends on >= comparison
        metrics = calculate_metrics_at_threshold(scores, labels, 0.5)

        # With >= threshold, all scores >= 0.5 are detected
        assert metrics['recall'] == 1.0
        assert metrics['false_positive_rate'] == 1.0


class TestThresholdSweep:
    """Test threshold sweeping functionality."""

    def test_sweep_range(self):
        """Test that sweep covers the full range."""
        scores = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        labels = np.array([0, 0, 1, 1, 1])

        results = sweep_thresholds(scores, labels, start=0.0, end=1.0, step=0.25)

        thresholds = [r['threshold'] for r in results]

        # Should include 0.0, 0.25, 0.5, 0.75, 1.0
        assert 0.0 in thresholds
        assert 1.0 in thresholds
        assert len(thresholds) == 5

    def test_sweep_metrics_present(self):
        """Test that all required metrics are present in results."""
        scores = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        labels = np.array([0, 0, 1, 1, 1])

        results = sweep_thresholds(scores, labels, start=0.0, end=1.0, step=0.5)

        for result in results:
            assert 'threshold' in result
            assert 'precision' in result
            assert 'recall' in result
            assert 'f1_score' in result
            assert 'false_positive_rate' in result

            # All metrics should be between 0 and 1
            assert 0 <= result['precision'] <= 1
            assert 0 <= result['recall'] <= 1
            assert 0 <= result['f1_score'] <= 1
            assert 0 <= result['false_positive_rate'] <= 1


class TestOptimalThreshold:
    """Test optimal threshold finding."""

    def test_find_optimal(self):
        """Test finding the optimal threshold."""
        results = [
            {'threshold': 0.0, 'f1_score': 0.5},
            {'threshold': 0.5, 'f1_score': 0.8},
            {'threshold': 1.0, 'f1_score': 0.3}
        ]

        optimal = find_optimal_threshold(results)

        assert optimal is not None
        assert optimal['threshold'] == 0.5
        assert optimal['f1_score'] == 0.8

    def test_empty_results(self):
        """Test handling of empty results."""
        optimal = find_optimal_threshold([])
        assert optimal is None


class TestRunAnalysis:
    """Test full analysis pipeline."""

    def test_full_pipeline(self):
        """Test the complete analysis pipeline with temporary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test predictions
            predictions_df = pd.DataFrame({
                'timestamp': range(100),
                'score': np.random.uniform(0, 1, 100),
                'anomaly': np.random.randint(0, 2, 100)
            })
            predictions_path = tmpdir_path / 'predictions.csv'
            predictions_df.to_csv(predictions_path, index=False)

            # Create test ground truth
            ground_truth_df = pd.DataFrame({
                'timestamp': range(100),
                'is_anomaly': np.random.randint(0, 2, 100)
            })
            ground_truth_path = tmpdir_path / 'ground_truth.csv'
            ground_truth_df.to_csv(ground_truth_path, index=False)

            output_path = tmpdir_path / 'results.json'

            # Run analysis
            results = run_analysis(
                predictions_path=predictions_path,
                ground_truth_path=ground_truth_path,
                output_path=output_path
            )

            # Verify output file exists
            assert output_path.exists()

            # Verify output structure
            assert 'analysis_summary' in results
            assert 'threshold_sweep_results' in results
            assert results['analysis_summary']['total_thresholds_tested'] > 0

            # Verify JSON file content
            with open(output_path, 'r') as f:
                json_content = json.load(f)

            assert json_content == results

    def test_missing_predictions_file(self):
        """Test error handling for missing predictions file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ground_truth_df = pd.DataFrame({
                'timestamp': range(10),
                'is_anomaly': [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
            })
            ground_truth_path = Path(tmpdir) / 'ground_truth.csv'
            ground_truth_df.to_csv(ground_truth_path, index=False)

            predictions_path = Path(tmpdir) / 'nonexistent.csv'
            output_path = Path(tmpdir) / 'results.json'

            with pytest.raises(FileNotFoundError):
                run_analysis(
                    predictions_path=predictions_path,
                    ground_truth_path=ground_truth_path,
                    output_path=output_path
                )

    def test_mismatched_timestamps(self):
        """Test handling of mismatched timestamps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create predictions with timestamps 0-49
            predictions_df = pd.DataFrame({
                'timestamp': range(50),
                'score': np.random.uniform(0, 1, 50),
                'anomaly': np.random.randint(0, 2, 50)
            })
            predictions_path = tmpdir_path / 'predictions.csv'
            predictions_df.to_csv(predictions_path, index=False)

            # Create ground truth with timestamps 50-99 (no overlap)
            ground_truth_df = pd.DataFrame({
                'timestamp': range(50, 100),
                'is_anomaly': np.random.randint(0, 2, 50)
            })
            ground_truth_path = tmpdir_path / 'ground_truth.csv'
            ground_truth_df.to_csv(ground_truth_path, index=False)

            output_path = tmpdir_path / 'results.json'

            with pytest.raises(ValueError, match="No overlapping timestamps"):
                run_analysis(
                    predictions_path=predictions_path,
                    ground_truth_path=ground_truth_path,
                    output_path=output_path
                )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])