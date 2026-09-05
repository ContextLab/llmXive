"""
Unit tests for T024: Lagged Alignment Logic.
"""
import os
import sys
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path if not already
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from src.data.align import calculate_lagged_mmns, load_accuracy_blocks, load_mmn_epochs

class TestT024LaggedAlignment:
    
    @pytest.fixture
    def sample_mmn_epochs(self):
        """Create a mock MMN epochs DataFrame."""
        data = []
        # Create data for subject 1
        # Trials 1 to 100
        for i in range(1, 101):
            data.append({
                'subject_id': 1,
                'trial_id': i,
                'mmn_amplitude': float(i * 0.1) # Simple linear trend for testing
            })
        # Create data for subject 2
        for i in range(1, 101):
            data.append({
                'subject_id': 2,
                'trial_id': i,
                'mmn_amplitude': float(i * 0.2)
            })
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_accuracy_blocks(self):
        """Create a mock accuracy blocks DataFrame."""
        data = [
            {
                'subject_id': 1,
                'block_id': 1,
                'accuracy': 0.85,
                'trial_start': 60, # Window: 10 to 50
                'trial_end': 70
            },
            {
                'subject_id': 1,
                'block_id': 2,
                'accuracy': 0.90,
                'trial_start': 80, # Window: 30 to 70
                'trial_end': 90
            },
            {
                'subject_id': 2,
                'block_id': 1,
                'accuracy': 0.75,
                'trial_start': 60,
                'trial_end': 70
            }
        ]
        return pd.DataFrame(data)

    def test_calculate_lagged_mmns_basic(self, sample_mmn_epochs, sample_accuracy_blocks):
        """Test basic calculation of lagged MMN."""
        result = calculate_lagged_mmns(sample_mmn_epochs, sample_accuracy_blocks)
        
        assert not result.empty
        assert 'subject_id' in result.columns
        assert 'block_id' in result.columns
        assert 'mmn_amplitude' in result.columns
        assert 'source_window_start_trial' in result.columns

        # Check subject 1, block 1
        # Block starts at 60. Window: 60-50=10 to 60-10=50.
        # Trials 10 to 50.
        # Expected MMN: mean of [1.0, 1.1, ..., 5.0]
        # Sum = (1.0 + 5.0) * 41 / 2 = 123.0
        # Mean = 123.0 / 41 = 3.0
        row = result[(result['subject_id'] == 1) & (result['block_id'] == 1)]
        assert len(row) == 1
        assert row['source_window_start_trial'].values[0] == 10
        assert np.isclose(row['mmn_amplitude'].values[0], 3.0)

    def test_calculate_lagged_mmns_empty_window(self, sample_mmn_epochs, sample_accuracy_blocks):
        """Test behavior when window has no data (e.g., start trial too early)."""
        # Create a block starting at trial 5
        # Window: 5-50 = -45 to 5-10 = -5. No data.
        extra_block = pd.DataFrame([{
            'subject_id': 1,
            'block_id': 99,
            'accuracy': 0.5,
            'trial_start': 5,
            'trial_end': 15
        }])
        combined_blocks = pd.concat([sample_accuracy_blocks, extra_block], ignore_index=True)
        
        result = calculate_lagged_mmns(sample_mmn_epochs, combined_blocks)
        
        # The row for block 99 should not exist in the result
        row_99 = result[(result['subject_id'] == 1) & (result['block_id'] == 99)]
        assert len(row_99) == 0

    def test_calculate_lagged_mmns_multiple_subjects(self, sample_mmn_epochs, sample_accuracy_blocks):
        """Test that calculation works correctly for multiple subjects."""
        result = calculate_lagged_mmns(sample_mmn_epochs, sample_accuracy_blocks)
        
        # Should have 3 rows (2 for sub 1, 1 for sub 2)
        assert len(result) == 3

        # Check subject 2, block 1
        # Window: 10 to 50.
        # MMN values: i * 0.2
        # Mean = mean(i * 0.2 for i in 10..50) = 0.2 * 3.0 = 0.6
        row = result[(result['subject_id'] == 2) & (result['block_id'] == 1)]
        assert len(row) == 1
        assert np.isclose(row['mmn_amplitude'].values[0], 0.6)

    def test_calculate_lagged_mmns_schema(self, sample_mmn_epochs, sample_accuracy_blocks):
        """Verify the output schema matches T024 requirements."""
        result = calculate_lagged_mmns(sample_mmn_epochs, sample_accuracy_blocks)
        
        expected_cols = ['subject_id', 'block_id', 'mmn_amplitude', 'source_window_start_trial']
        assert list(result.columns) == expected_cols