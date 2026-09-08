"""
Tests for counterbalance assignment generation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.data.counterbalance import generate_counterbalance_assignments
from code.config import get_data_path

class TestCounterbalance:
    """Test suite for counterbalance assignment generation."""

    def test_generate_assignments_basic(self):
        """Test basic generation of counterbalance assignments."""
        participant_ids = ["PID001", "PID002", "PID003", "PID004"]
        
        df = generate_counterbalance_assignments(participant_ids, seed=42)
        
        assert len(df) == 4
        assert list(df.columns) == [
            'participant_id', 
            'session_order', 
            'complexity_condition_1', 
            'complexity_condition_2'
        ]
        assert set(df['session_order']) == {'Low-High', 'High-Low'}
        assert all(df['participant_id'].isin(participant_ids))

    def test_generate_assignments_reproducibility(self):
        """Test that the same seed produces the same results."""
        participant_ids = ["PID001", "PID002", "PID003", "PID004", "PID005", "PID006"]
        
        df1 = generate_counterbalance_assignments(participant_ids, seed=42)
        df2 = generate_counterbalance_assignments(participant_ids, seed=42)
        
        pd.testing.assert_frame_equal(df1, df2)

    def test_generate_assignments_odd_count(self):
        """Test with an odd number of participants."""
        participant_ids = ["PID001", "PID002", "PID003"]
        
        df = generate_counterbalance_assignments(participant_ids, seed=42)
        
        assert len(df) == 3
        # Should have 2 of one order and 1 of the other
        counts = df['session_order'].value_counts()
        assert 1 in counts.values
        assert 2 in counts.values

    def test_generate_assignments_empty_list(self):
        """Test that empty participant list raises ValueError."""
        with pytest.raises(ValueError):
            generate_counterbalance_assignments([], seed=42)

    def test_generate_assignments_condition_mapping(self):
        """Test that conditions are correctly mapped to session orders."""
        participant_ids = ["PID001", "PID002", "PID003", "PID004"]
        
        df = generate_counterbalance_assignments(participant_ids, seed=42)
        
        for _, row in df.iterrows():
            if row['session_order'] == 'Low-High':
                assert row['complexity_condition_1'] == 'Low'
                assert row['complexity_condition_2'] == 'High'
            elif row['session_order'] == 'High-Low':
                assert row['complexity_condition_1'] == 'High'
                assert row['complexity_condition_2'] == 'Low'

    def test_generate_assignments_output_path(self):
        """Test that output is written to the correct path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary output path
            output_path = Path(tmpdir) / "counterbalance_test.csv"
            
            participant_ids = ["PID001", "PID002"]
            df = generate_counterbalance_assignments(
                participant_ids, 
                seed=42, 
                output_path=output_path
            )
            
            assert output_path.exists()
            
            # Read back and verify
            df_read = pd.read_csv(output_path)
            pd.testing.assert_frame_equal(df, df_read)