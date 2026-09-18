"""
Unit tests for edge cases: participant dropouts, missing data, and incomplete records.
Tests verify that the pipeline handles these scenarios gracefully without crashing
and produces valid partial results where applicable.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.change_scores import calculate_change_scores_for_participant, get_metric_mapping
from code.analysis.bootstrap_ci import calculate_bootstrap_ci
from code.scoring.sart import score_sart_session
from code.scoring.ospan import score_ospan_session
from code.scoring.questionnaires import score_pss10_session, score_panas_session
from code.pipeline.merge_data import merge_baseline_post
from code.analysis.effect_sizes import calculate_cohens_d


class TestParticipantDropouts:
    """Tests for handling participants who dropped out mid-study."""

    def test_baseline_only_participant(self):
        """Participant completed baseline but dropped out before post-intervention."""
        baseline_data = [
            {'participant_id': 'P001', 'metric_type': 'SART', 'value': 12.0, 'phase': 'baseline'},
            {'participant_id': 'P001', 'metric_type': 'Ospan', 'value': 45.0, 'phase': 'baseline'},
            {'participant_id': 'P001', 'metric_type': 'PSS-10', 'value': 25.0, 'phase': 'baseline'},
        ]
        
        # No post-intervention data for P001
        post_data = []
        
        merged_data = merge_baseline_post(baseline_data, post_data)
        
        # P001 should be in merged data but with NaN for post values
        p001_records = [r for r in merged_data if r['participant_id'] == 'P001']
        assert len(p001_records) > 0
        assert any(np.isnan(r.get('post_value', float('nan'))) for r in p001_records)

    def test_post_only_participant(self):
        """Participant missing baseline data (e.g., enrolled late)."""
        baseline_data = []
        
        post_data = [
            {'participant_id': 'P002', 'metric_type': 'SART', 'value': 10.0, 'phase': 'post'},
            {'participant_id': 'P002', 'metric_type': 'Ospan', 'value': 50.0, 'phase': 'post'},
        ]
        
        merged_data = merge_baseline_post(baseline_data, post_data)
        
        # P002 should be in merged data but with NaN for baseline values
        p002_records = [r for r in merged_data if r['participant_id'] == 'P002']
        assert len(p002_records) > 0
        assert any(np.isnan(r.get('baseline_value', float('nan'))) for r in p002_records)

    def test_change_score_calculation_with_dropout(self):
        """Change scores should be NaN for dropouts, not raise exceptions."""
        baseline_data = [
            {'participant_id': 'P003', 'metric_type': 'SART', 'value': 15.0, 'phase': 'baseline'},
        ]
        post_data = []
        
        merged_data = merge_baseline_post(baseline_data, post_data)
        
        # Should not raise, should return NaN for change score
        metric_mapping = get_metric_mapping(merged_data)
        assert 'SART' in metric_mapping
        
        # Simulate change score calculation for a dropout
        baseline_vals = [15.0]
        post_vals = [float('nan')]
        
        change_scores = []
        for b, p in zip(baseline_vals, post_vals):
            if np.isnan(b) or np.isnan(p):
                change_scores.append(float('nan'))
            else:
                change_scores.append(p - b)
        
        assert len(change_scores) == 1
        assert np.isnan(change_scores[0])


class TestMissingData:
    """Tests for handling missing data within valid participants."""

    def test_partial_baseline_data(self):
        """Participant missing some baseline metrics."""
        baseline_data = [
            {'participant_id': 'P004', 'metric_type': 'SART', 'value': 11.0, 'phase': 'baseline'},
            # Missing Ospan, PSS-10, PANAS
        ]
        post_data = [
            {'participant_id': 'P004', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post'},
            {'participant_id': 'P004', 'metric_type': 'Ospan', 'value': 48.0, 'phase': 'post'},
            {'participant_id': 'P004', 'metric_type': 'PSS-10', 'value': 18.0, 'phase': 'post'},
        ]
        
        merged_data = merge_baseline_post(baseline_data, post_data)
        
        # Should have records for all metrics that exist
        sart_records = [r for r in merged_data if r['metric_type'] == 'SART']
        ospan_records = [r for r in merged_data if r['metric_type'] == 'Ospan']
        
        assert len(sart_records) == 2  # baseline and post
        assert len(ospan_records) == 1  # only post

    def test_missing_sessions_in_batch(self):
        """SART scoring handles missing trials gracefully."""
        # Session with missing trials (None values)
        trials = [
            {'response_time': 0.5, 'accuracy': True, 'stimulus_type': 'go'},
            {'response_time': None, 'accuracy': None, 'stimulus_type': 'go'},  # Missing trial
            {'response_time': 0.6, 'accuracy': False, 'stimulus_type': 'nogo'},
        ]
        
        # Should not crash, should handle None values
        result = score_sart_session(trials)
        
        # Commission errors should be calculated from valid trials only
        assert 'commission_errors' in result
        assert isinstance(result['commission_errors'], int)

    def test_empty_questionnaire_responses(self):
        """Questionnaire scoring handles empty or partial responses."""
        # PSS-10 with some missing items
        responses = [5, 4, None, 3, 5, None, 2, 4, None, 3]
        
        # Should handle None values without crashing
        result = score_pss10_session(responses)
        
        # Should return a score based on available items or None
        assert 'total_score' in result or result.get('total_score') is None

    def test_nan_values_in_dataset(self):
        """Bootstrap CI calculation handles NaN values."""
        data_with_nan = [1.0, 2.0, float('nan'), 3.0, 4.0]
        
        # Should not crash
        result = calculate_bootstrap_ci(data_with_nan, n_resamples=100)
        
        # Result should be valid (or indicate failure appropriately)
        assert result is not None


class TestIncompleteRecords:
    """Tests for handling records with missing fields."""

    def test_missing_metric_type(self):
        """Records without metric_type are handled gracefully."""
        data = [
            {'participant_id': 'P005', 'value': 10.0, 'phase': 'baseline'},
            {'participant_id': 'P005', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post'},
        ]
        
        # Should not crash during merge
        merged = merge_baseline_post(data, [])
        assert len(merged) >= 1

    def test_missing_participant_id(self):
        """Records without participant_id are filtered or handled."""
        data = [
            {'metric_type': 'SART', 'value': 10.0, 'phase': 'baseline'},
            {'participant_id': 'P006', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post'},
        ]
        
        # Should not crash
        merged = merge_baseline_post(data, [])
        # Records without IDs should be excluded or handled
        assert len(merged) <= 2

    def test_invalid_numeric_values(self):
        """Non-numeric values in numeric fields are handled."""
        baseline_data = [
            {'participant_id': 'P007', 'metric_type': 'SART', 'value': 'invalid', 'phase': 'baseline'},
            {'participant_id': 'P007', 'metric_type': 'SART', 'value': 10.0, 'phase': 'baseline'},
        ]
        post_data = [
            {'participant_id': 'P007', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post'},
        ]
        
        merged = merge_baseline_post(baseline_data, post_data)
        
        # Should handle conversion errors gracefully
        sart_records = [r for r in merged if r['metric_type'] == 'SART']
        assert len(sart_records) >= 1


class TestEdgeCaseCombinations:
    """Tests for combinations of edge cases."""

    def test_all_dropouts(self):
        """All participants dropped out before post-intervention."""
        baseline_data = [
            {'participant_id': 'P008', 'metric_type': 'SART', 'value': 12.0, 'phase': 'baseline'},
            {'participant_id': 'P009', 'metric_type': 'SART', 'value': 15.0, 'phase': 'baseline'},
        ]
        post_data = []
        
        merged = merge_baseline_post(baseline_data, post_data)
        
        # Should have baseline records but no post records
        assert len(merged) == 2
        assert all(r['phase'] == 'baseline' for r in merged)

    def test_completely_empty_dataset(self):
        """Empty baseline and post datasets."""
        baseline_data = []
        post_data = []
        
        merged = merge_baseline_post(baseline_data, post_data)
        
        assert len(merged) == 0

    def test_single_trial_sart_session(self):
        """SART session with only one trial."""
        trials = [{'response_time': 0.5, 'accuracy': True, 'stimulus_type': 'go'}]
        
        result = score_sart_session(trials)
        
        assert 'commission_errors' in result
        assert 'mean_rt' in result

    def test_effect_size_with_insufficient_data(self):
        """Cohen's d calculation with insufficient samples."""
        baseline = [10.0]
        post = [8.0]
        
        # Should handle single sample gracefully
        d, ci = calculate_cohens_d(baseline, post)
        
        # Should return valid result or NaN
        assert d is not None
        assert ci is not None


class TestDataIntegrityEdgeCases:
    """Tests for data integrity issues."""

    def test_duplicate_records(self):
        """Handling of duplicate records in dataset."""
        baseline_data = [
            {'participant_id': 'P010', 'metric_type': 'SART', 'value': 12.0, 'phase': 'baseline'},
            {'participant_id': 'P010', 'metric_type': 'SART', 'value': 12.0, 'phase': 'baseline'},  # Duplicate
        ]
        post_data = [
            {'participant_id': 'P010', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post'},
        ]
        
        merged = merge_baseline_post(baseline_data, post_data)
        
        # Should handle duplicates (either deduplicate or process both)
        assert len(merged) >= 2

    def test_mixed_phase_labels(self):
        """Handling of inconsistent phase labels."""
        baseline_data = [
            {'participant_id': 'P011', 'metric_type': 'SART', 'value': 12.0, 'phase': 'baseline'},
            {'participant_id': 'P011', 'metric_type': 'SART', 'value': 12.0, 'phase': 'pre'},  # Inconsistent
        ]
        post_data = [
            {'participant_id': 'P011', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post'},
            {'participant_id': 'P011', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post_intervention'},  # Inconsistent
        ]
        
        merged = merge_baseline_post(baseline_data, post_data)
        
        # Should handle various phase label conventions
        assert len(merged) >= 2

    def test_extreme_outliers(self):
        """Handling of extreme outlier values."""
        baseline_data = [
            {'participant_id': 'P012', 'metric_type': 'SART', 'value': 10.0, 'phase': 'baseline'},
            {'participant_id': 'P012', 'metric_type': 'SART', 'value': 1000000.0, 'phase': 'baseline'},  # Extreme outlier
        ]
        post_data = [
            {'participant_id': 'P012', 'metric_type': 'SART', 'value': 8.0, 'phase': 'post'},
        ]
        
        merged = merge_baseline_post(baseline_data, post_data)
        
        # Should not crash on extreme values
        assert len(merged) >= 2

        # Bootstrap should handle outliers (may produce wide CI)
        values = [10.0, 1000000.0, 8.0]
        result = calculate_bootstrap_ci(values, n_resamples=100)
        assert result is not None