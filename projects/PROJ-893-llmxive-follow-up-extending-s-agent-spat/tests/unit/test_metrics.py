"""
Unit tests for benchmark metrics calculation.
Tests Exact Match, F1-score, and latency statistics calculations.
"""
import pytest
import json
import math
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from benchmark.metrics import (
    calculate_exact_match,
    calculate_f1_score,
    calculate_latency_stats,
    compute_metrics
)


class TestExactMatch:
    """Tests for the exact match calculation."""

    def test_exact_match_strings(self):
        """Test exact match with simple strings."""
        assert calculate_exact_match("hello", "hello") is True
        assert calculate_exact_match("hello", "world") is False

    def test_exact_match_case_insensitive(self):
        """Test that exact match is case insensitive."""
        assert calculate_exact_match("Hello", "hello") is True
        assert calculate_exact_match("HELLO", "hello") is True

    def test_exact_match_numbers(self):
        """Test exact match with numbers."""
        assert calculate_exact_match(5, 5) is True
        assert calculate_exact_match(5, 6) is False
        assert calculate_exact_match(5.0, 5) is True

    def test_exact_match_lists(self):
        """Test exact match with lists."""
        assert calculate_exact_match([1, 2, 3], [1, 2, 3]) is True
        assert calculate_exact_match([1, 2, 3], [3, 2, 1]) is False

    def test_exact_match_string_lists(self):
        """Test exact match with string representations of lists."""
        assert calculate_exact_match("[1, 2, 3]", "[1, 2, 3]") is True
        assert calculate_exact_match("[1, 2, 3]", "[1, 2, 4]") is False

    def test_exact_match_mismatched_types(self):
        """Test exact match with mismatched types."""
        assert calculate_exact_match("5", 5) is True  # String "5" vs int 5
        assert calculate_exact_match("5", 6) is False


class TestF1Score:
    """Tests for F1-score calculation."""

    def test_f1_perfect_match(self):
        """Test F1 score with perfect matches."""
        predictions = [
            {'scene_id': '1', 'prediction': 'yes'},
            {'scene_id': '2', 'prediction': 'no'}
        ]
        ground_truths = [
            {'scene_id': '1', 'answer': 'yes'},
            {'scene_id': '2', 'answer': 'no'}
        ]
        
        precision, recall, f1 = calculate_f1_score(predictions, ground_truths)
        
        assert precision == 1.0
        assert recall == 1.0
        assert f1 == 1.0

    def test_f1_no_matches(self):
        """Test F1 score with no matches."""
        predictions = [
            {'scene_id': '1', 'prediction': 'yes'},
            {'scene_id': '2', 'prediction': 'no'}
        ]
        ground_truths = [
            {'scene_id': '1', 'answer': 'no'},
            {'scene_id': '2', 'answer': 'yes'}
        ]
        
        precision, recall, f1 = calculate_f1_score(predictions, ground_truths)
        
        assert precision == 0.0
        assert recall == 0.0
        assert f1 == 0.0

    def test_f1_partial_match(self):
        """Test F1 score with partial matches."""
        predictions = [
            {'scene_id': '1', 'prediction': 'yes'},
            {'scene_id': '2', 'prediction': 'no'},
            {'scene_id': '3', 'prediction': 'yes'}
        ]
        ground_truths = [
            {'scene_id': '1', 'answer': 'yes'},
            {'scene_id': '2', 'answer': 'yes'},
            {'scene_id': '3', 'answer': 'no'}
        ]
        
        precision, recall, f1 = calculate_f1_score(predictions, ground_truths)
        
        # Only scene 1 matches
        # TP=1, FP=2 (scenes 2,3 wrong), FN=2 (scenes 2,3 missed)
        # Precision = 1/3, Recall = 1/3, F1 = 2*(1/3)*(1/3)/(2/3) = 1/3
        assert abs(precision - 1/3) < 0.0001
        assert abs(recall - 1/3) < 0.0001
        assert abs(f1 - 1/3) < 0.0001

    def test_f1_empty_input(self):
        """Test F1 score with empty input."""
        predictions = []
        ground_truths = []
        
        precision, recall, f1 = calculate_f1_score(predictions, ground_truths)
        
        assert precision == 0.0
        assert recall == 0.0
        assert f1 == 0.0

    def test_f1_mismatched_lengths(self):
        """Test that F1 score raises error for mismatched lengths."""
        predictions = [{'scene_id': '1', 'prediction': 'yes'}]
        ground_truths = [
            {'scene_id': '1', 'answer': 'yes'},
            {'scene_id': '2', 'answer': 'no'}
        ]
        
        with pytest.raises(ValueError):
            calculate_f1_score(predictions, ground_truths)


class TestLatencyStats:
    """Tests for latency statistics calculation."""

    def test_latency_stats_single_value(self):
        """Test latency stats with a single value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"scene_id": "1", "latency_seconds": 1.5}\n')
            temp_path = Path(f.name)
        
        try:
            stats = calculate_latency_stats(temp_path)
            
            assert stats['mean_seconds'] == 1.5
            assert stats['median_seconds'] == 1.5
            assert stats['min_seconds'] == 1.5
            assert stats['max_seconds'] == 1.5
            assert stats['std_seconds'] == 0.0
            assert stats['count'] == 1
        finally:
            temp_path.unlink()

    def test_latency_stats_multiple_values(self):
        """Test latency stats with multiple values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"scene_id": "1", "latency_seconds": 1.0}\n')
            f.write('{"scene_id": "2", "latency_seconds": 2.0}\n')
            f.write('{"scene_id": "3", "latency_seconds": 3.0}\n')
            temp_path = Path(f.name)
        
        try:
            stats = calculate_latency_stats(temp_path)
            
            assert stats['mean_seconds'] == 2.0
            assert stats['median_seconds'] == 2.0
            assert stats['min_seconds'] == 1.0
            assert stats['max_seconds'] == 3.0
            assert stats['count'] == 3
            # std = sqrt(((1-2)^2 + (2-2)^2 + (3-2)^2) / 3) = sqrt(2/3) ≈ 0.816
            expected_std = math.sqrt(2/3)
            assert abs(stats['std_seconds'] - expected_std) < 0.0001
        finally:
            temp_path.unlink()

    def test_latency_stats_even_count(self):
        """Test latency stats with even number of values (median calculation)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"scene_id": "1", "latency_seconds": 1.0}\n')
            f.write('{"scene_id": "2", "latency_seconds": 2.0}\n')
            f.write('{"scene_id": "3", "latency_seconds": 3.0}\n')
            f.write('{"scene_id": "4", "latency_seconds": 5.0}\n')
            temp_path = Path(f.name)
        
        try:
            stats = calculate_latency_stats(temp_path)
            
            assert stats['mean_seconds'] == 2.75
            assert stats['median_seconds'] == 2.5  # (2+3)/2
            assert stats['count'] == 4
        finally:
            temp_path.unlink()

    def test_latency_stats_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            calculate_latency_stats(Path("/nonexistent/file.jsonl"))

    def test_latency_stats_empty_file(self):
        """Test latency stats with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            stats = calculate_latency_stats(temp_path)
            
            assert stats['mean_seconds'] == 0.0
            assert stats['median_seconds'] == 0.0
            assert stats['count'] == 0
        finally:
            temp_path.unlink()

    def test_latency_stats_invalid_json(self):
        """Test that invalid JSON lines are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"scene_id": "1", "latency_seconds": 1.0}\n')
            f.write('invalid json\n')
            f.write('{"scene_id": "2", "latency_seconds": 2.0}\n')
            temp_path = Path(f.name)
        
        try:
            stats = calculate_latency_stats(temp_path)
            
            assert stats['count'] == 2
            assert stats['mean_seconds'] == 1.5
        finally:
            temp_path.unlink()


class TestComputeMetrics:
    """Integration tests for the full metrics computation."""

    def test_compute_metrics_full(self):
        """Test full metrics computation with all inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create predictions JSONL
            predictions_path = tmp_path / "predictions.jsonl"
            with open(predictions_path, 'w') as f:
                f.write('{"scene_id": "1", "prediction": "yes"}\n')
                f.write('{"scene_id": "2", "prediction": "no"}\n')
            
            # Create ground truth CSV
            ground_truth_path = tmp_path / "ground_truth.csv"
            with open(ground_truth_path, 'w') as f:
                f.write('scene_id,answer\n')
                f.write('1,yes\n')
                f.write('2,no\n')
            
            # Create VLM baseline CSV
            vlm_baseline_path = tmp_path / "vlm_baseline.csv"
            with open(vlm_baseline_path, 'w') as f:
                f.write('scene_id,prediction\n')
                f.write('1,yes\n')
                f.write('2,yes\n')
            
            # Create latency log
            latency_log_path = tmp_path / "latency_log.jsonl"
            with open(latency_log_path, 'w') as f:
                f.write('{"scene_id": "1", "latency_seconds": 1.0}\n')
                f.write('{"scene_id": "2", "latency_seconds": 2.0}\n')
            
            metrics = compute_metrics(
                predictions_path,
                ground_truth_path,
                vlm_baseline_path,
                latency_log_path
            )
            
            # Verify symbolic solver metrics (perfect match)
            assert metrics['symbolic_solver']['f1_score'] == 1.0
            assert metrics['symbolic_solver']['precision'] == 1.0
            assert metrics['symbolic_solver']['recall'] == 1.0
            
            # Verify VLM baseline metrics (1/2 match)
            assert metrics['vlm_baseline']['f1_score'] == 0.5
            
            # Verify latency stats
            assert metrics['latency']['median_seconds'] == 1.5
            assert metrics['latency']['count'] == 2
            assert metrics['sample_size'] == 2

    def test_compute_metrics_missing_file(self):
        """Test that missing input file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_metrics(
                Path("/nonexistent/predictions.jsonl"),
                Path("/nonexistent/ground_truth.csv"),
                Path("/nonexistent/vlm_baseline.csv"),
                Path("/nonexistent/latency_log.jsonl")
            )