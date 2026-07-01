"""
Unit tests for dataset filtering logic (T014).
Tests sequential stimuli detection and predictability manipulation checks.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from preprocess import (
    is_sequential_stimuli,
    has_predictability_manipulation,
    filter_datasets,
    compute_markov_surprisal
)

class TestSequentialStimuli:
    """Tests for sequential stimuli detection."""
    
    def test_perfectly_sequential(self):
        """Dataset with perfect sequential order should pass."""
        df = pd.DataFrame({
            'stimulus_sequence': list(range(100)),
            'participant_id': ['P1'] * 100
        })
        is_seq, score = is_sequential_stimuli(df)
        assert is_seq is True
        assert score > 0.5
    
    def test_random_sequence(self):
        """Random sequence should fail sequential check."""
        np.random.seed(42)
        df = pd.DataFrame({
            'stimulus_sequence': np.random.randint(0, 100, 100),
            'participant_id': ['P1'] * 100
        })
        is_seq, score = is_sequential_stimuli(df)
        # Random sequences may occasionally have some structure, but should generally be low
        assert score < 0.8  # Allow some tolerance for random chance
    
    def test_missing_column(self):
        """Missing stimulus column should return False."""
        df = pd.DataFrame({
            'other_col': [1, 2, 3],
            'participant_id': ['P1', 'P2', 'P3']
        })
        is_seq, score = is_sequential_stimuli(df, stimulus_col='stimulus_sequence')
        assert is_seq is False
        assert score == 0.0
    
    def test_categorical_sequential(self):
        """Categorical sequence with pattern should be detected."""
        df = pd.DataFrame({
            'stimulus_sequence': ['A', 'B', 'C', 'A', 'B', 'C'] * 20,
            'participant_id': ['P1'] * 120
        })
        is_seq, score = is_sequential_stimuli(df)
        assert is_seq is True
        assert score > 0.5

class TestPredictabilityManipulation:
    """Tests for predictability manipulation detection."""
    
    def test_explicit_predictability_column(self):
        """Dataset with explicit predictability column should pass."""
        df = pd.DataFrame({
            'stimulus_sequence': [1] * 50 + [2] * 50,
            'predictability': ['high'] * 50 + ['low'] * 50,
            'participant_id': ['P1'] * 100
        })
        has_manip, score = has_predictability_manipulation(df, predictability_col='predictability')
        assert has_manip is True
        assert score == 1.0
    
    def test_block_pattern(self):
        """Dataset with blocks of different patterns should be detected."""
        # Block 1: highly predictable
        block1 = ['A'] * 25 + ['B'] * 25
        # Block 2: less predictable
        block2 = ['A', 'B', 'A', 'C', 'B', 'A'] * 10
        df = pd.DataFrame({
            'stimulus_sequence': block1 + block2,
            'participant_id': ['P1'] * len(block1 + block2)
        })
        has_manip, score = has_predictability_manipulation(df)
        # Should detect some variation in predictability
        assert score > 0.1
    
    def test_uniform_sequence(self):
        """Uniform sequence with no variation should fail."""
        df = pd.DataFrame({
            'stimulus_sequence': ['A'] * 100,
            'participant_id': ['P1'] * 100
        })
        has_manip, score = has_predictability_manipulation(df)
        # Single repeated value has no predictability manipulation
        assert score < 0.5

class TestMarkovSurprisal:
    """Tests for Markov surprisal computation."""
    
    def test_surprisal_calculation(self):
        """Test basic surprisal calculation."""
        # Simple sequence: A -> B (high prob), A -> C (low prob)
        df = pd.DataFrame({
            'stimulus_sequence': ['A', 'B', 'A', 'B', 'A', 'C', 'A', 'B'] * 10,
            'participant_id': ['P1'] * 80
        })
        df_surprisal = compute_markov_surprisal(df)
        
        assert 'surprisal' in df_surprisal.columns
        assert not df_surprisal['surprisal'].isna().all()
        
        # First element should be NaN (no previous transition)
        assert pd.isna(df_surprisal['surprisal'].iloc[0])
        
        # Subsequent values should be positive
        positive_surprisal = df_surprisal['surprisal'][1:]
        assert (positive_surprisal > 0).all() or positive_surprisal.isna().all()
    
    def test_surprisal_for_rare_transitions(self):
        """Rare transitions should have higher surprisal."""
        # Create sequence where one transition is rare
        sequence = ['A'] * 40 + ['B'] * 40 + ['C']  # Rare A->C transition
        df = pd.DataFrame({
            'stimulus_sequence': sequence,
            'participant_id': ['P1'] * len(sequence)
        })
        df_surprisal = compute_markov_surprisal(df)
        
        # The transition to C should have higher surprisal
        c_idx = sequence.index('C')
        if c_idx < len(df_surprisal) and not pd.isna(df_surprisal['surprisal'].iloc[c_idx]):
            assert df_surprisal['surprisal'].iloc[c_idx] > 1.0  # Higher than average

class TestFilterDatasets:
    """Integration tests for dataset filtering."""
    
    def test_filter_with_valid_and_invalid_datasets(self, tmp_path):
        """Test filtering with mix of valid and invalid datasets."""
        # Create test datasets
        valid_df = pd.DataFrame({
            'stimulus_sequence': list(range(50)),
            'participant_id': ['P1'] * 50,
            'duration_estimate': [1.0] * 50
        })
        
        invalid_df = pd.DataFrame({
            'other_col': [1, 2, 3],  # Missing required columns
            'participant_id': ['P1', 'P2', 'P3']
        })
        
        # Write test files
        valid_path = tmp_path / 'valid.csv'
        invalid_path = tmp_path / 'invalid.csv'
        valid_df.to_csv(valid_path, index=False)
        invalid_df.to_csv(invalid_path, index=False)
        
        # Run filtering
        exclusion_log_path = str(tmp_path / 'exclusion_log.json')
        filtered_output = tmp_path / 'filtered'
        filtered_output.mkdir()
        
        stats = filter_datasets(
            input_dir=str(tmp_path),
            output_dir=str(filtered_output),
            exclusion_log_path=exclusion_log_path
        )
        
        # Verify results
        assert stats['total_datasets'] == 2
        assert stats['kept_datasets'] == 1
        assert stats['excluded_datasets'] == 1
        
        # Verify exclusion log
        import json
        with open(exclusion_log_path, 'r') as f:
            exclusion_log = json.load(f)
        
        assert len(exclusion_log) == 1
        assert 'missing_columns' in exclusion_log[0]['reason'] or 'non_sequential' in exclusion_log[0]['reason']
        
        # Verify filtered output
        assert (filtered_output / 'valid.csv').exists()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
