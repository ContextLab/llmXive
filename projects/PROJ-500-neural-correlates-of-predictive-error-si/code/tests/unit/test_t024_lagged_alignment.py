import os
import sys
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.data.align import compute_lagged_alignment, calculate_block_accuracy, calculate_mmn_amplitude

class TestT024LaggedAlignment:
    
    def test_calculate_block_accuracy(self):
        """Test accuracy calculation for a block."""
        df = pd.DataFrame({
            'trial': [0, 1, 2, 3, 4],
            'accuracy': [1, 1, 0, 1, 1]
        })
        acc = calculate_block_accuracy(df, 1, 4)
        assert acc == 2/3  # trials 1, 2, 3 -> 1, 0, 1 -> 2/3
        
    def test_lagged_alignment_schema(self):
        """Test that the output schema matches requirements."""
        # Mock data
        mock_epochs = {
            'CP3': np.random.randn(100, 700),
            'CP4': np.random.randn(100, 700),
            'C3': np.random.randn(100, 700),
            'C4': np.random.randn(100, 700),
            'metadata': pd.DataFrame({
                'trial': range(100),
                'stimulus_type': ['standard'] * 80 + ['deviant'] * 20,
                'correct': [1] * 100
            })
        }
        mock_behavioral = pd.DataFrame({
            'trial': range(100),
            'accuracy': [1] * 100
        })
        
        results = compute_lagged_alignment(
            subject_id="sub-001",
            epochs=mock_epochs,
            behavioral_df=mock_behavioral,
            window_size=50,
            step_size=10
        )
        
        assert len(results) > 0
        first = results[0]
        assert 'subject_id' in first
        assert 'block_id' in first
        assert 'mmn_amplitude' in first
        assert 'source_window_start_trial' in first
        
        # Check types
        assert isinstance(first['subject_id'], str)
        assert isinstance(first['mmn_amplitude'], (int, float, np.floating))
        assert isinstance(first['source_window_start_trial'], int)

    def test_lagged_window_logic(self):
        """Test that the window logic (t-50 to t-10) is applied correctly."""
        # We can't easily test the exact numerical values without real data,
        # but we can verify the source_window_start_trial is consistent with the block_id logic
        mock_epochs = {
            'CP3': np.random.randn(100, 700),
            'CP4': np.random.randn(100, 700),
            'C3': np.random.randn(100, 700),
            'C4': np.random.randn(100, 700),
            'metadata': pd.DataFrame({
                'trial': range(100),
                'stimulus_type': ['standard'] * 80 + ['deviant'] * 20,
                'correct': [1] * 100
            })
        }
        mock_behavioral = pd.DataFrame({
            'trial': range(100),
            'accuracy': [1] * 100
        })
        
        results = compute_lagged_alignment(
            subject_id="sub-001",
            epochs=mock_epochs,
            behavioral_df=mock_behavioral,
            window_size=50,
            step_size=10
        )
        
        # First block should start at t = 50 + 10 = 60
        # MMN window: 10 to 50
        # source_window_start_trial should be 10
        if len(results) > 0:
            assert results[0]['source_window_start_trial'] == 10
            # Block ID should reflect the start of the target block (t=60)
            # Our implementation uses f"{subject_id}_block_{t}"
            assert "block_60" in results[0]['block_id']