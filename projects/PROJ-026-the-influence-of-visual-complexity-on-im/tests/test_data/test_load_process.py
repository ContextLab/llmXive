import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.load import generate_synthetic_response_logs, load_response_logs
from data.process import filter_trials, calculate_d_score, aggregate_d_scores

class TestDataLoading:
    def test_generate_synthetic_response_logs(self):
        """Test that synthetic data generation works correctly."""
        df = generate_synthetic_response_logs(n_participants=5, n_trials=20, seed=42)
        
        assert len(df) == 5 * 2 * 20  # 5 participants, 2 sessions, 20 trials
        assert 'participant_id' in df.columns
        assert 'session_id' in df.columns
        assert 'reaction_time' in df.columns
        assert 'is_correct' in df.columns
        
        # Check reaction time range
        assert df['reaction_time'].min() >= 200
        assert df['reaction_time'].max() <= 2000
        
        # Check participant IDs
        unique_pids = df['participant_id'].unique()
        assert len(unique_pids) == 5

    def test_load_response_logs_missing_dir(self):
        """Test that missing data directory raises error."""
        with pytest.raises(FileNotFoundError):
            load_response_logs("/nonexistent/path")

class TestDataProcessing:
    def test_filter_trials_latency_bounds(self):
        """Test that trials outside latency bounds are removed."""
        df = pd.DataFrame({
            'participant_id': ['P001'] * 5,
            'session_id': ['session_1'] * 5,
            'reaction_time': [200, 300, 500, 10000, 11000],
            'is_correct': [True] * 5
        })
        
        filtered = filter_trials(df)
        
        # Should keep 300, 500, 10000 (3 trials)
        assert len(filtered) == 3
        assert filtered['reaction_time'].min() >= 300
        assert filtered['reaction_time'].max() <= 10000

    def test_filter_trials_errors(self):
        """Test that incorrect trials are removed."""
        df = pd.DataFrame({
            'participant_id': ['P001'] * 5,
            'session_id': ['session_1'] * 5,
            'reaction_time': [500, 500, 500, 500, 500],
            'is_correct': [True, False, True, False, True]
        })
        
        filtered = filter_trials(df)
        
        # Should keep only correct trials (3)
        assert len(filtered) == 3
        assert all(filtered['is_correct'] == True)

    def test_calculate_d_score_insufficient_trials(self):
        """Test D-score calculation with insufficient trials."""
        df = pd.DataFrame({
            'participant_id': ['P001'] * 5,
            'session_id': ['session_1'] * 5,
            'reaction_time': [500, 500, 500, 500, 500],
            'is_correct': [True] * 5
        })
        
        d_score = calculate_d_score(df)
        assert np.isnan(d_score)

    def test_calculate_d_score_valid(self):
        """Test D-score calculation with valid data."""
        # Create two blocks with different means
        df = pd.DataFrame({
            'participant_id': ['P001'] * 20,
            'session_id': ['session_1'] * 10 + ['session_2'] * 10,
            'reaction_time': [500] * 10 + [600] * 10,
            'is_correct': [True] * 20
        })
        
        d_score = calculate_d_score(df)
        assert not np.isnan(d_score)
        # Should be positive since session_2 is slower
        assert d_score > 0

    def test_aggregate_d_scores(self):
        """Test full aggregation pipeline."""
        # Generate synthetic data
        df = generate_synthetic_response_logs(n_participants=10, n_trials=20, seed=42)
        
        # Aggregate
        aggregated = aggregate_d_scores(df)
        
        # Check output schema
        assert 'participant_id' in aggregated.columns
        assert 'session_id' in aggregated.columns
        assert 'd_score' in aggregated.columns
        assert 'n_trials_valid' in aggregated.columns
        assert 'status' in aggregated.columns
        
        # Check that some are valid
        valid_count = len(aggregated[aggregated['status'] == 'valid'])
        assert valid_count > 0

    def test_aggregate_d_scores_insufficient_trials(self):
        """Test aggregation with insufficient trials."""
        # Create data with only 5 trials per participant-session
        df = pd.DataFrame({
            'participant_id': ['P001'] * 10,
            'session_id': ['session_1'] * 5 + ['session_2'] * 5,
            'reaction_time': [500] * 10,
            'is_correct': [True] * 10
        })
        
        aggregated = aggregate_d_scores(df)
        
        # All should have insufficient_trials status
        assert all(aggregated['status'] == 'insufficient_trials')
        assert all(aggregated['d_score'].isna())