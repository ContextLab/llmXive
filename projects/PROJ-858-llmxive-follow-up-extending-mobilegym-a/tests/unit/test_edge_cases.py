"""
Unit tests for edge cases in the llmXive pipeline.

Tests cover:
1. Empty batches in scheduler and coverage aggregation
2. Malformed data handling in rollouts and analysis modules
3. Boundary conditions for state coverage vectors
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from scheduler.curriculum_scheduler import CurriculumScheduler
from scheduler.state_coverage import (
    initialize_coverage_vector,
    detect_state_transitions,
    aggregate_coverage_vectors,
    merge_coverage_vectors_threadsafe,
    process_rollout_batch
)
from utils.constants import (
    get_coverage_vector_dimensions,
    get_semantic_proxies,
    is_valid_coverage_vector
)
from utils.logging import get_logger
from analysis.sensitivity import calculate_vector_scalar, align_data
from analysis.convergence import load_logs
from scheduler.error_handling_rollouts import load_rollout_safe


class TestEmptyBatches:
    """Tests for handling empty batches and data structures."""

    def test_empty_rollout_batch_processing(self):
        """Test that process_rollout_batch handles empty list gracefully."""
        empty_batch = []
        result = process_rollout_batch(empty_batch)
        
        assert result is not None
        assert len(result) == 0
    
    def test_empty_coverage_aggregation(self):
        """Test aggregation of empty list of coverage vectors."""
        empty_vectors = []
        result = aggregate_coverage_vectors(empty_vectors)
        
        # Should return initialized vector or empty structure
        assert result is not None
        if isinstance(result, dict):
            assert "vector" in result or len(result) == 0
    
    def test_scheduler_with_empty_history(self):
        """Test CurriculumScheduler with empty coverage history."""
        scheduler = CurriculumScheduler()
        
        # Empty history should not crash
        try:
            batch = scheduler.select_batch(coverage_history=[])
            assert batch is not None
        except Exception as e:
            pytest.fail(f"Scheduler crashed on empty history: {e}")
    
    def test_empty_merge_threadsafe(self):
        """Test thread-safe merge with empty vectors."""
        vectors_to_merge = []
        result = merge_coverage_vectors_threadsafe(vectors_to_merge)
        
        assert result is not None

class TestMalformedData:
    """Tests for handling malformed or corrupted data."""

    def test_malformed_json_rollout(self):
        """Test load_rollout_safe with malformed JSON string."""
        malformed_json = '{"invalid": json, "missing": quote}'
        
        result = load_rollout_safe(malformed_json)
        
        # Should return None or raise specific error, not crash
        assert result is None or isinstance(result, dict)
    
    def test_malformed_rollout_batch(self):
        """Test process_rollout_batch with mixed valid/invalid data."""
        batch = [
            {"task": "valid", "state": {"dark_mode": True}},
            "not a dict",
            None,
            {"task": "another_valid", "state": {"unread_count": 5}},
            12345,
            ["array", "instead", "of", "dict"]
        ]
        
        # Should handle without crashing
        result = process_rollout_batch(batch)
        assert result is not None
    
    def test_invalid_coverage_vector_shape(self):
        """Test is_valid_coverage_vector with incorrect dimensions."""
        valid_dim = get_coverage_vector_dimensions()
        
        # Too short
        short_vector = [0] * (valid_dim - 1)
        assert not is_valid_coverage_vector(short_vector)
        
        # Too long
        long_vector = [0] * (valid_dim + 1)
        assert not is_valid_coverage_vector(long_vector)
        
        # Wrong type
        assert not is_valid_coverage_vector("not a list")
        assert not is_valid_coverage_vector([0.5, 0.3])  # Non-binary
    
    def test_malformed_json_in_analysis(self):
        """Test load_logs with corrupted JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ "corrupted": ')
            temp_path = f.name
        
        try:
            with pytest.raises((json.JSONDecodeError, ValueError)):
                load_logs(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_null_values_in_rollout(self):
        """Test handling of None/null values in rollout data."""
        rollout_with_nulls = {
            "task": "test_task",
            "state": {
                "dark_mode": None,
                "unread_count": 5,
                "nested": None
            }
        }
        
        result = load_rollout_safe(json.dumps(rollout_with_nulls))
        assert result is not None

class TestBoundaryConditions:
    """Tests for boundary conditions and edge values."""

    def test_all_zeros_coverage_vector(self):
        """Test coverage vector with all zeros."""
        vector = [0] * get_coverage_vector_dimensions()
        assert is_valid_coverage_vector(vector)
        
        scalar = calculate_vector_scalar(vector)
        assert scalar == 0
    
    def test_all_ones_coverage_vector(self):
        """Test coverage vector with all ones."""
        vector = [1] * get_coverage_vector_dimensions()
        assert is_valid_coverage_vector(vector)
        
        scalar = calculate_vector_scalar(vector)
        assert scalar == get_coverage_vector_dimensions()
    
    def test_single_bit_toggle(self):
        """Test detection of single state transition."""
        initial_state = {
            "dark_mode": False,
            "unread_count": 0,
            "current_app": "home"
        }
        
        final_state = {
            "dark_mode": True,  # Changed
            "unread_count": 0,
            "current_app": "home"
        }
        
        transitions = detect_state_transitions(initial_state, final_state)
        assert len(transitions) == 1
        assert "dark_mode" in transitions
    
    def test_empty_state_dictionary(self):
        """Test handling of empty state dictionaries."""
        initial = {}
        final = {}
        
        transitions = detect_state_transitions(initial, final)
        assert len(transitions) == 0
    
    def test_missing_keys_in_state(self):
        """Test state comparison when keys are missing."""
        initial = {"dark_mode": False}
        final = {"dark_mode": True, "unread_count": 5}  # Extra key
        
        # Should handle gracefully without KeyError
        transitions = detect_state_transitions(initial, final)
        assert transitions is not None

class TestSchedulerEdgeCases:
    """Tests for scheduler-specific edge cases."""

    def test_scheduler_with_single_state_covered(self):
        """Test scheduler when only one state is covered."""
        scheduler = CurriculumScheduler()
        
        history = [
            {
                "vector": [1] + [0] * (get_coverage_vector_dimensions() - 1),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        try:
            batch = scheduler.select_batch(coverage_history=history)
            assert batch is not None
        except Exception as e:
            pytest.fail(f"Scheduler failed with single covered state: {e}")
    
    def test_scheduler_all_states_covered(self):
        """Test scheduler deadlock prevention when all states covered."""
        scheduler = CurriculumScheduler()
        
        full_vector = [1] * get_coverage_vector_dimensions()
        history = [
            {
                "vector": full_vector,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        try:
            batch = scheduler.select_batch(coverage_history=history)
            # Should use fallback mechanism
            assert batch is not None
        except Exception as e:
            pytest.fail(f"Scheduler crashed on full coverage: {e}")

class TestAlignmentEdgeCases:
    """Tests for data alignment edge cases."""

    def test_align_data_empty_lists(self):
        """Test align_data with empty input lists."""
        vectors = []
        results = []
        
        aligned_vectors, aligned_results = align_data(vectors, results)
        
        assert len(aligned_vectors) == 0
        assert len(aligned_results) == 0
    
    def test_align_data_mismatched_lengths(self):
        """Test align_data with mismatched vector and result lengths."""
        vectors = [[0, 1], [1, 0]]
        results = [0.5]  # Only one result for two vectors
        
        # Should handle gracefully or raise clear error
        try:
            aligned_vectors, aligned_results = align_data(vectors, results)
            # If it succeeds, lengths should match or be truncated
            assert len(aligned_vectors) == len(aligned_results)
        except ValueError:
            pass  # Expected behavior for mismatched lengths

if __name__ == "__main__":
    pytest.main([__file__, "-v"])