"""
Unit tests for edge cases in the llmXive pipeline.
Covers empty batches, malformed data, and boundary conditions.
"""

import json
import os
import sys
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scheduler.state_coverage import (
    initialize_coverage_vector,
    detect_state_transitions,
    aggregate_coverage_vectors,
    merge_coverage_vectors_threadsafe,
    process_rollout_batch,
)
from scheduler.curriculum_scheduler import CurriculumScheduler
from scheduler.error_handling_rollouts import load_rollout_safe, process_rollout_batch as process_rollouts_safe
from analysis.sensitivity import calculate_vector_scalar, align_data, compute_pearson_correlation
from utils.constants import is_valid_coverage_vector, ErrorCodes
from utils.logging import LlmXiveError


class TestEmptyBatches:
    """Tests for handling empty input batches."""

    def test_empty_rollout_batch_processing(self):
        """Test that process_rollout_batch handles an empty list gracefully."""
        empty_batch = []
        result = process_rollout_batch(empty_batch)
        # Should return empty list or zeroed vectors
        assert isinstance(result, list)
        assert len(result) == 0

    def test_empty_coverage_vector_aggregation(self):
        """Test aggregation of an empty list of coverage vectors."""
        empty_vectors = []
        result = aggregate_coverage_vectors(empty_vectors)
        # Should return a valid zero vector or empty list
        assert isinstance(result, list)
        assert len(result) == 0

    def test_empty_scheduler_selection(self):
        """Test scheduler behavior with empty task pool."""
        scheduler = CurriculumScheduler(
            task_pool=[],
            coverage_history=[],
            success_history=[],
            config={}
        )
        # Should handle empty pool without crashing
        with pytest.raises((ValueError, IndexError, KeyError)):
            scheduler.select_batch(batch_size=5)
        # Note: Depending on implementation, it might raise an error or return empty list
        # We expect it NOT to crash with a generic exception

    def test_empty_sensitivity_data(self):
        """Test sensitivity analysis with empty data."""
        vectors = []
        success_rates = []
        # Should handle empty input gracefully
        with pytest.raises((ValueError, TypeError)):
            compute_pearson_correlation(vectors, success_rates)


class TestMalformedData:
    """Tests for handling malformed or corrupted input data."""

    def test_malformed_json_rollout(self):
        """Test that load_rollout_safe handles malformed JSON."""
        malformed_json = '{"invalid": json}'
        result = load_rollout_safe(malformed_json)
        # Should return None or an error indicator
        assert result is None

    def test_malformed_coverage_vector(self):
        """Test detection of malformed coverage vectors."""
        malformed_vector = [1, 2, 3, "invalid", 5]  # Contains non-binary value
        assert not is_valid_coverage_vector(malformed_vector)

    def test_malformed_vector_with_correct_schema(self):
        """Test vector with correct schema but invalid values."""
        # Vector with values outside [0, 1]
        invalid_vector = [0, 1, 2, 0, 1]
        assert not is_valid_coverage_vector(invalid_vector)

    def test_malformed_scheduler_config(self):
        """Test scheduler with missing required config fields."""
        incomplete_config = {"low_coverage_threshold": 0.05}
        # Missing other required fields like 'success_rate_ranges'
        with pytest.raises((KeyError, ValueError)):
            scheduler = CurriculumScheduler(
                task_pool=[{"id": "task1"}],
                coverage_history=[],
                success_history=[],
                config=incomplete_config
            )
            scheduler.select_batch(batch_size=1)

    def test_malformed_state_transition_data(self):
        """Test state transition detection with missing fields."""
        rollout_data = {
            "steps": [
                {"state": {"dark_mode": True}},
                {"state": {}}  # Missing expected field
            ]
        }
        # Should handle missing fields gracefully
        transitions = detect_state_transitions(rollout_data)
        assert isinstance(transitions, list)


class TestBoundaryConditions:
    """Tests for boundary and edge value handling."""

    def test_zero_success_rate(self):
        """Test scheduler behavior when all tasks have 0% success."""
        scheduler = CurriculumScheduler(
            task_pool=[{"id": f"task{i}"} for i in range(10)],
            coverage_history=[{"task_id": f"task{i}", "coverage": [0]*5, "success": 0.0} for i in range(10)],
            success_history=[0.0] * 10,
            config={}
        )
        # Should fall back to entropy or random selection
        batch = scheduler.select_batch(batch_size=3)
        assert len(batch) == 3

    def test_perfect_success_rate(self):
        """Test scheduler behavior when all tasks have 100% success."""
        scheduler = CurriculumScheduler(
            task_pool=[{"id": f"task{i}"} for i in range(10)],
            coverage_history=[{"task_id": f"task{i}", "coverage": [1]*5, "success": 1.0} for i in range(10)],
            success_history=[1.0] * 10,
            config={}
        )
        # Should expand range or fall back to entropy
        batch = scheduler.select_batch(batch_size=3)
        assert len(batch) == 3

    def test_single_element_vector(self):
        """Test handling of single-element coverage vectors."""
        single_vector = [1]
        assert is_valid_coverage_vector(single_vector)

    def test_vector_dimension_mismatch(self):
        """Test detection of dimension mismatch in vectors."""
        vector1 = [1, 0, 1]
        vector2 = [1, 0]  # Different dimension
        with pytest.raises(ValueError):
            merge_coverage_vectors_threadsafe([vector1, vector2])

    def test_null_values_in_data(self):
        """Test handling of None/null values in data structures."""
        data_with_nulls = [
            {"task_id": "task1", "coverage": None, "success": 0.5},
            {"task_id": "task2", "coverage": [1, 0, 1], "success": None},
        ]
        # Should handle gracefully or raise specific error
        with pytest.raises((TypeError, ValueError)):
            align_data(data_with_nulls)


class TestLargeInputHandling:
    """Tests for handling large input sizes."""

    def test_large_rollout_batch(self):
        """Test processing a large batch of rollouts."""
        large_batch = [
            {
                "task_id": f"task{i}",
                "steps": [{"state": {"dark_mode": i % 2}} for _ in range(100)]
            }
            for i in range(1000)
        ]
        result = process_rollout_batch(large_batch)
        assert len(result) == 1000

    def test_large_coverage_vector_aggregation(self):
        """Test aggregation of many coverage vectors."""
        many_vectors = [[1 if j % 2 == 0 else 0 for j in range(5)] for _ in range(5000)]
        result = aggregate_coverage_vectors(many_vectors)
        assert isinstance(result, list)
        assert len(result) == 5  # Should aggregate to single vector of same dimension


class TestErrorHandling:
    """Tests for specific error handling scenarios."""

    def test_invalid_coverage_ratio_calculation(self):
        """Test calculation with invalid inputs."""
        with pytest.raises((ValueError, TypeError)):
            # Passing non-list or invalid list
            from utils.constants import calculate_coverage_ratio
            calculate_coverage_ratio("invalid")

    def test_scheduler_timeout_handling(self):
        """Test that scheduler handles timeout scenarios."""
        # Simulate a scenario where selection takes too long
        # This is hard to test directly, but we can test the fallback
        scheduler = CurriculumScheduler(
            task_pool=[{"id": f"task{i}"} for i in range(10000)],
            coverage_history=[],
            success_history=[],
            config={"selection_timeout": 0.001}  # Very short timeout
        )
        # Should fall back to random selection
        batch = scheduler.select_batch(batch_size=5)
        assert len(batch) == 5

    def test_unexpected_characters_in_data(self):
        """Test handling of unexpected characters in JSON data."""
        malformed_json = '{"task_id": "test\\x00", "value": 1}'
        result = load_rollout_safe(malformed_json)
        assert result is None