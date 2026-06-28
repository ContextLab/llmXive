"""
Tests for metric validation module.

Validates that ≥95% of games produce valid metrics (SC-001).
"""
import pytest
import numpy as np
from typing import List, Dict, Any

from metrics.validator import (
    ValidationResult,
    GameMetricRecord,
    validate_specialization_range,
    validate_retrieval_range,
    validate_single_game_metrics,
    validate_experiment_metrics,
    validate_and_filter_records,
    compute_metric_statistics,
    validate_batch_metrics,
    MIN_VALID_GAME_RATE
)
from metrics.specialization import SpecializationMetrics
from metrics.retrieval import RetrievalMetrics

# Patch the compute functions for testing
import metrics.specialization
import metrics.retrieval

class TestSpecializationRangeValidation:
    """Tests for specialization index range validation."""
    
    def test_valid_specialization_index(self):
        """Valid specialization index within bounds."""
        n_agents = 4
        spec_index = np.log2(n_agents) / 2  # Half of theoretical max
        
        is_valid, error = validate_specialization_range(spec_index, n_agents)
        
        assert is_valid is True
        assert error is None
    
    def test_nan_specialization_index(self):
        """NaN specialization index should fail."""
        is_valid, error = validate_specialization_range(np.nan, 4)
        
        assert is_valid is False
        assert "NaN" in error or "Inf" in error
    
    def test_inf_specialization_index(self):
        """Inf specialization index should fail."""
        is_valid, error = validate_specialization_range(np.inf, 4)
        
        assert is_valid is False
        assert "NaN" in error or "Inf" in error
    
    def test_negative_specialization_index(self):
        """Negative specialization index should fail."""
        is_valid, error = validate_specialization_range(-0.5, 4)
        
        assert is_valid is False
        assert "below minimum" in error
    
    def test_exceeds_theoretical_max(self):
        """Specialization exceeding log₂(N) should fail."""
        n_agents = 4
        spec_index = np.log2(n_agents) * 1.5  # 50% above theoretical max
        
        is_valid, error = validate_specialization_range(spec_index, n_agents)
        
        assert is_valid is False
        assert "exceeds theoretical maximum" in error
    
    def test_at_theoretical_max(self):
        """Specialization at theoretical max should be valid."""
        n_agents = 4
        spec_index = np.log2(n_agents)
        
        is_valid, error = validate_specialization_range(spec_index, n_agents)
        
        assert is_valid is True
        assert error is None
    
    def test_zero_specialization_index(self):
        """Zero specialization index should be valid."""
        is_valid, error = validate_specialization_range(0.0, 4)
        
        assert is_valid is True
        assert error is None

class TestRetrievalRangeValidation:
    """Tests for retrieval efficiency range validation."""
    
    def test_valid_retrieval_efficiency(self):
        """Valid retrieval efficiency in [0, 1]."""
        is_valid, error = validate_retrieval_range(0.75)
        
        assert is_valid is True
        assert error is None
    
    def test_boundary_zero(self):
        """Retrieval efficiency at 0 should be valid."""
        is_valid, error = validate_retrieval_range(0.0)
        
        assert is_valid is True
        assert error is None
    
    def test_boundary_one(self):
        """Retrieval efficiency at 1 should be valid."""
        is_valid, error = validate_retrieval_range(1.0)
        
        assert is_valid is True
        assert error is None
    
    def test_nan_retrieval_efficiency(self):
        """NaN retrieval efficiency should fail."""
        is_valid, error = validate_retrieval_range(np.nan)
        
        assert is_valid is False
        assert "NaN" in error or "Inf" in error
    
    def test_negative_retrieval_efficiency(self):
        """Negative retrieval efficiency should fail."""
        is_valid, error = validate_retrieval_range(-0.1)
        
        assert is_valid is False
        assert "below minimum" in error
    
    def test_exceeds_one_retrieval_efficiency(self):
        """Retrieval efficiency > 1 should fail."""
        is_valid, error = validate_retrieval_range(1.1)
        
        assert is_valid is False
        assert "exceeds maximum" in error

class TestSingleGameValidation:
    """Tests for single game metric validation."""
    
    def test_valid_game(self):
        """Game with valid metrics should pass."""
        game_data = {
            'n_agents': 4,
            'agent_actions': [
                {'cue': 'item_a', 'retrieved': 'item_a'},
                {'cue': 'item_b', 'retrieved': 'item_b'},
                {'cue': 'item_c', 'retrieved': 'item_c'},
                {'cue': 'item_d', 'retrieved': 'item_d'}
            ],
            'specialization_data': {
                'agent_key_counts': [10, 8, 7, 5],
                'total_keys': 30
            },
            'retrieval_data': {
                'successful_retrievals': 4,
                'total_cues': 4
            }
        }
        
        # Mock the compute functions
        original_spec_compute = metrics.specialization.compute_game_level_specialization
        original_retrieval_compute = metrics.retrieval.compute_game_level_retrieval
        
        metrics.specialization.compute_game_level_specialization = (
            lambda gd: SpecializationMetrics(specialization_index=1.5)
        )
        metrics.retrieval.compute_game_level_retrieval = (
            lambda gd: RetrievalMetrics(efficiency=0.8)
        )
        
        try:
            record = validate_single_game_metrics(0, game_data)
            
            assert record.game_id == 0
            assert record.is_valid is True
            assert record.specialization_valid is True
            assert record.retrieval_valid is True
            assert len(record.errors) == 0
        finally:
            # Restore originals
            metrics.specialization.compute_game_level_specialization = (
                original_spec_compute
            )
            metrics.retrieval.compute_game_level_retrieval = (
                original_retrieval_compute
            )
    
    def test_invalid_specialization(self):
        """Game with invalid specialization should fail."""
        game_data = {
            'n_agents': 4,
            'specialization_data': {'agent_key_counts': [], 'total_keys': 0},
            'retrieval_data': {'successful_retrievals': 4, 'total_cues': 4}
        }
        
        original_spec_compute = metrics.specialization.compute_game_level_specialization
        original_retrieval_compute = metrics.retrieval.compute_game_level_retrieval
        
        metrics.specialization.compute_game_level_specialization = (
            lambda gd: SpecializationMetrics(specialization_index=-1.0)  # Invalid
        )
        metrics.retrieval.compute_game_level_retrieval = (
            lambda gd: RetrievalMetrics(efficiency=0.8)
        )
        
        try:
            record = validate_single_game_metrics(0, game_data)
            
            assert record.is_valid is False
            assert record.specialization_valid is False
            assert record.retrieval_valid is True
        finally:
            metrics.specialization.compute_game_level_specialization = (
                original_spec_compute
            )
            metrics.retrieval.compute_game_level_retrieval = (
                original_retrieval_compute
            )
    
    def test_invalid_retrieval(self):
        """Game with invalid retrieval should fail."""
        game_data = {
            'n_agents': 4,
            'specialization_data': {'agent_key_counts': [10, 8, 7, 5], 'total_keys': 30},
            'retrieval_data': {'successful_retrievals': 4, 'total_cues': 4}
        }
        
        original_spec_compute = metrics.specialization.compute_game_level_specialization
        original_retrieval_compute = metrics.retrieval.compute_game_level_retrieval
        
        metrics.specialization.compute_game_level_specialization = (
            lambda gd: SpecializationMetrics(specialization_index=1.5)
        )
        metrics.retrieval.compute_game_level_retrieval = (
            lambda gd: RetrievalMetrics(efficiency=1.5)  # Invalid (> 1.0)
        )
        
        try:
            record = validate_single_game_metrics(0, game_data)
            
            assert record.is_valid is False
            assert record.specialization_valid is True
            assert record.retrieval_valid is False
        finally:
            metrics.specialization.compute_game_level_specialization = (
                original_spec_compute
            )
            metrics.retrieval.compute_game_level_retrieval = (
                original_retrieval_compute
            )

class TestExperimentValidation:
    """Tests for experiment-level validation (SC-001)."""
    
    def test_all_games_valid(self):
        """All games valid should pass SC-001."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=1.5,
                retrieval_efficiency=0.8,
                specialization_valid=True,
                retrieval_valid=True
            )
            for i in range(100)
        ]
        
        result = validate_experiment_metrics(records)
        
        assert result.is_valid is True
        assert result.total_games == 100
        assert result.valid_games == 100
        assert result.invalid_games == 0
        assert result.success_rate == 1.0
    
    def test_95_percent_valid(self):
        """Exactly 95% valid games should pass SC-001."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=1.5,
                retrieval_efficiency=0.8,
                specialization_valid=True,
                retrieval_valid=True
            )
            if i < 95 else
            GameMetricRecord(
                game_id=i,
                specialization_index=None,
                retrieval_efficiency=None,
                specialization_valid=False,
                retrieval_valid=False,
                errors=["Simulated error"]
            )
            for i in range(100)
        ]
        
        result = validate_experiment_metrics(records)
        
        assert result.is_valid is True  # Exactly 95% meets threshold
        assert result.total_games == 100
        assert result.valid_games == 95
        assert result.invalid_games == 5
        assert result.success_rate == 0.95
    
    def test_94_percent_valid(self):
        """94% valid games should fail SC-001."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=1.5,
                retrieval_efficiency=0.8,
                specialization_valid=True,
                retrieval_valid=True
            )
            if i < 94 else
            GameMetricRecord(
                game_id=i,
                specialization_index=None,
                retrieval_efficiency=None,
                specialization_valid=False,
                retrieval_valid=False,
                errors=["Simulated error"]
            )
            for i in range(100)
        ]
        
        result = validate_experiment_metrics(records)
        
        assert result.is_valid is False  # 94% < 95% threshold
        assert result.total_games == 100
        assert result.valid_games == 94
        assert result.invalid_games == 6
        assert result.success_rate == 0.94
    
    def test_empty_records(self):
        """Empty records list should fail."""
        result = validate_experiment_metrics([])
        
        assert result.is_valid is False
        assert result.total_games == 0
        assert len(result.error_details) > 0
    
    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=1.5,
                retrieval_efficiency=0.8,
                specialization_valid=True,
                retrieval_valid=True
            )
            if i < 80 else
            GameMetricRecord(
                game_id=i,
                specialization_index=None,
                retrieval_efficiency=None,
                specialization_valid=False,
                retrieval_valid=False
            )
            for i in range(100)
        ]
        
        # With 80% threshold, this should pass
        result = validate_experiment_metrics(records, min_success_rate=0.80)
        assert result.is_valid is True
        
        # With 90% threshold, this should fail
        result = validate_experiment_metrics(records, min_success_rate=0.90)
        assert result.is_valid is False

class TestValidationAndFiltering:
    """Tests for validation with filtering."""
    
    def test_filter_invalid_records(self):
        """Filter should remove invalid records."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=1.5,
                retrieval_efficiency=0.8,
                specialization_valid=True,
                retrieval_valid=True
            )
            if i < 80 else
            GameMetricRecord(
                game_id=i,
                specialization_index=None,
                retrieval_efficiency=None,
                specialization_valid=False,
                retrieval_valid=False
            )
            for i in range(100)
        ]
        
        valid_records, validation_result = validate_and_filter_records(records)
        
        assert len(valid_records) == 80
        assert validation_result.valid_games == 80
        assert all(r.is_valid for r in valid_records)

class TestMetricStatistics:
    """Tests for metric statistics computation."""
    
    def test_compute_statistics(self):
        """Statistics should be computed correctly."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=float(i % 10) / 10.0,  # 0.0 to 0.9
                retrieval_efficiency=float(i % 5) / 5.0,  # 0.0 to 0.8
                specialization_valid=True,
                retrieval_valid=True
            )
            for i in range(100)
        ]
        
        stats = compute_metric_statistics(records)
        
        assert 'specialization' in stats
        assert 'retrieval' in stats
        assert stats['specialization']['count'] == 100
        assert stats['retrieval']['count'] == 100
        assert 'mean' in stats['specialization']
        assert 'std' in stats['specialization']
        assert 'min' in stats['specialization']
        assert 'max' in stats['specialization']
    
    def test_empty_records_statistics(self):
        """Empty records should return empty stats."""
        stats = compute_metric_statistics([])
        
        assert stats['specialization'] == {}
        assert stats['retrieval'] == {}

class TestBatchValidation:
    """Tests for batch validation."""
    
    def test_batch_validation(self):
        """Batch validation should work correctly."""
        batch_results = [
            {
                'n_agents': 4,
                'specialization_data': {'agent_key_counts': [10, 8, 7, 5], 'total_keys': 30},
                'retrieval_data': {'successful_retrievals': 4, 'total_cues': 4}
            }
            for _ in range(10)
        ]
        
        original_spec_compute = metrics.specialization.compute_game_level_specialization
        original_retrieval_compute = metrics.retrieval.compute_game_level_retrieval
        
        metrics.specialization.compute_game_level_specialization = (
            lambda gd: SpecializationMetrics(specialization_index=1.5)
        )
        metrics.retrieval.compute_game_level_retrieval = (
            lambda gd: RetrievalMetrics(efficiency=0.8)
        )
        
        try:
            result = validate_batch_metrics(batch_results)
            
            assert result.total_games == 10
            assert result.valid_games == 10
            assert result.success_rate == 1.0
        finally:
            metrics.specialization.compute_game_level_specialization = (
                original_spec_compute
            )
            metrics.retrieval.compute_game_level_retrieval = (
                original_retrieval_compute
            )

class TestSC001Requirement:
    """Tests specifically for SC-001 requirement (≥95% success rate)."""
    
    def test_sc001_pass_at_95(self):
        """SC-001 should pass at exactly 95%."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=1.5,
                retrieval_efficiency=0.8,
                specialization_valid=True,
                retrieval_valid=True
            )
            for i in range(950)
        ] + [
            GameMetricRecord(
                game_id=i,
                specialization_index=None,
                retrieval_efficiency=None,
                specialization_valid=False,
                retrieval_valid=False
            )
            for i in range(950, 1000)
        ]
        
        result = validate_experiment_metrics(records)
        
        assert result.is_valid is True, "SC-001 requires ≥95% success rate"
        assert result.success_rate >= MIN_VALID_GAME_RATE
    
    def test_sc001_fail_below_95(self):
        """SC-001 should fail below 95%."""
        records = [
            GameMetricRecord(
                game_id=i,
                specialization_index=1.5,
                retrieval_efficiency=0.8,
                specialization_valid=True,
                retrieval_valid=True
            )
            for i in range(949)
        ] + [
            GameMetricRecord(
                game_id=i,
                specialization_index=None,
                retrieval_efficiency=None,
                specialization_valid=False,
                retrieval_valid=False
            )
            for i in range(949, 1000)
        ]
        
        result = validate_experiment_metrics(records)
        
        assert result.is_valid is False, "SC-001 requires ≥95% success rate"
        assert result.success_rate < MIN_VALID_GAME_RATE
    
    def test_sc001_default_threshold(self):
        """Default threshold should be 95%."""
        assert MIN_VALID_GAME_RATE == 0.95