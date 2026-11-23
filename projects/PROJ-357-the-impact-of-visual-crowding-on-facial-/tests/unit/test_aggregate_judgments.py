"""
Unit tests for the aggregate_judgments module (T029).

Tests:
- compute_accuracy: Correctly identifies matching vs non-matching labels
- aggregate_judgments: Correctly groups and computes statistics
- Edge cases: Empty data, single trial, missing columns
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.aggregate_judgments import compute_accuracy, aggregate_judgments

class TestComputeAccuracy:
    def test_compute_accuracy_all_correct(self):
        """Test when all responses match true labels."""
        df = pd.DataFrame({
            'stimulus_id': ['s1', 's2', 's3'],
            'true_label': ['happy', 'sad', 'angry'],
            'response_label': ['happy', 'sad', 'angry']
        })
        
        result = compute_accuracy(df)
        
        assert 'accuracy' in result.columns
        assert all(result['accuracy'] == 1.0)
        assert len(result) == 3

    def test_compute_accuracy_all_incorrect(self):
        """Test when no responses match true labels."""
        df = pd.DataFrame({
            'stimulus_id': ['s1', 's2', 's3'],
            'true_label': ['happy', 'sad', 'angry'],
            'response_label': ['sad', 'angry', 'happy']
        })
        
        result = compute_accuracy(df)
        
        assert 'accuracy' in result.columns
        assert all(result['accuracy'] == 0.0)
        assert len(result) == 3

    def test_compute_accuracy_mixed(self):
        """Test with mixed correct/incorrect responses."""
        df = pd.DataFrame({
            'stimulus_id': ['s1', 's2', 's3', 's4'],
            'true_label': ['happy', 'sad', 'angry', 'fear'],
            'response_label': ['happy', 'fear', 'angry', 'surprise']
        })
        
        result = compute_accuracy(df)
        
        assert 'accuracy' in result.columns
        expected_accuracy = [1.0, 0.0, 1.0, 0.0]
        assert list(result['accuracy']) == expected_accuracy

    def test_compute_accuracy_empty(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame(columns=['true_label', 'response_label'])
        result = compute_accuracy(df)
        
        assert len(result) == 0
        assert 'accuracy' in result.columns

    def test_compute_accuracy_missing_columns(self):
        """Test error when required columns are missing."""
        df = pd.DataFrame({
            'stimulus_id': ['s1'],
            'true_label': ['happy']
            # Missing response_label
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            compute_accuracy(df)

class TestAggregateJudgments:
    def test_aggregate_single_trial_per_group(self):
        """Test aggregation with one trial per stimulus group."""
        df = pd.DataFrame({
            'stimulus_id': ['s1', 's2', 's3'],
            'emotion_label': ['happy', 'sad', 'angry'],
            'flanker_count': [3, 5, 7],
            'accuracy': [1.0, 0.0, 1.0]
        })
        
        result = aggregate_judgments(df)
        
        assert len(result) == 3
        assert list(result['mean_accuracy']) == [1.0, 0.0, 1.0]
        assert list(result['trial_count']) == [1, 1, 1]
        assert list(result['std_accuracy']) == [0.0, 0.0, 0.0]  # std is 0 for single trial

    def test_aggregate_multiple_trials_per_group(self):
        """Test aggregation with multiple trials per stimulus group."""
        df = pd.DataFrame({
            'stimulus_id': ['s1', 's1', 's1', 's2', 's2'],
            'emotion_label': ['happy', 'happy', 'happy', 'sad', 'sad'],
            'flanker_count': [3, 3, 3, 5, 5],
            'accuracy': [1.0, 1.0, 0.0, 0.0, 1.0]
        })
        
        result = aggregate_judgments(df)
        
        assert len(result) == 2
        
        # Check s1 group
        s1_row = result[result['stimulus_id'] == 's1'].iloc[0]
        assert s1_row['mean_accuracy'] == pytest.approx(2/3, rel=0.01)
        assert s1_row['trial_count'] == 3
        
        # Check s2 group
        s2_row = result[result['stimulus_id'] == 's2'].iloc[0]
        assert s2_row['mean_accuracy'] == pytest.approx(0.5, rel=0.01)
        assert s2_row['trial_count'] == 2

    def test_aggregate_empty(self):
        """Test aggregation with empty DataFrame."""
        df = pd.DataFrame(columns=['stimulus_id', 'emotion_label', 'flanker_count', 'accuracy'])
        result = aggregate_judgments(df)
        
        assert len(result) == 0
        assert list(result.columns) == ['stimulus_id', 'emotion_label', 'flanker_count', 'mean_accuracy', 'trial_count', 'std_accuracy']

    def test_aggregate_missing_columns(self):
        """Test error when required columns are missing."""
        df = pd.DataFrame({
            'stimulus_id': ['s1'],
            'emotion_label': ['happy']
            # Missing flanker_count and accuracy
        })
        
        with pytest.raises(ValueError, match="Missing required columns for aggregation"):
            aggregate_judgments(df)

    def test_aggregate_preserves_all_groups(self):
        """Test that all unique combinations are preserved."""
        df = pd.DataFrame({
            'stimulus_id': ['s1', 's1', 's2', 's2'],
            'emotion_label': ['happy', 'sad', 'happy', 'sad'],  # Different emotions for same stimulus
            'flanker_count': [3, 3, 3, 3],
            'accuracy': [1.0, 0.0, 1.0, 0.0]
        })
        
        result = aggregate_judgments(df)
        
        # Should have 4 groups (s1+happy, s1+sad, s2+happy, s2+sad)
        assert len(result) == 4

class TestIntegration:
    def test_full_pipeline(self):
        """Test compute_accuracy followed by aggregate_judgments."""
        raw_df = pd.DataFrame({
            'stimulus_id': ['s1', 's1', 's2', 's2', 's3'],
            'true_label': ['happy', 'happy', 'sad', 'sad', 'angry'],
            'response_label': ['happy', 'sad', 'sad', 'angry', 'angry']
        })
        
        # Compute accuracy
        df_with_acc = compute_accuracy(raw_df)
        
        # Add flanker_count for aggregation
        df_with_acc['emotion_label'] = df_with_acc['true_label']
        df_with_acc['flanker_count'] = [3, 3, 5, 5, 7]
        
        # Aggregate
        aggregated = aggregate_judgments(df_with_acc)
        
        # Verify results
        assert len(aggregated) == 5  # 5 unique stimulus groups
        assert 'mean_accuracy' in aggregated.columns
        assert 'trial_count' in aggregated.columns
        
        # s1 should have 2 trials with mean accuracy 0.5
        s1_row = aggregated[aggregated['stimulus_id'] == 's1']
        assert len(s1_row) == 1
        assert s1_row['trial_count'].values[0] == 2
        assert s1_row['mean_accuracy'].values[0] == pytest.approx(0.5, rel=0.01)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])