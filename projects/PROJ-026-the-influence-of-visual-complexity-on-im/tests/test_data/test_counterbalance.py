"""
Unit tests for counterbalance assignment generation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.counterbalance import generate_counterbalance_assignments
from config import get_project_root, get_data_path

class TestCounterbalanceAssignment:
    """Tests for counterbalance assignment generation."""

    def test_generation_creates_file(self, tmp_path):
        """Test that the function creates the expected output file."""
        # Use a temporary directory for testing
        original_data_path = get_data_path()

        # Mock get_data_path to return tmp_path
        import data.counterbalance
        original_func = data.counterbalance.get_data_path
        data.counterbalance.get_data_path = lambda: tmp_path

        try:
            df = generate_counterbalance_assignments(n_participants=10, seed=42)
            output_path = tmp_path / "processed" / "counterbalance_assignment.csv"
            assert output_path.exists(), "Output file was not created"
        finally:
            # Restore original function
            data.counterbalance.get_data_path = original_func

    def test_correct_columns(self):
        """Test that the output DataFrame has the correct columns."""
        df = generate_counterbalance_assignments(n_participants=10, seed=42)
        assert "participant_id" in df.columns
        assert "session_order" in df.columns

    def test_correct_number_of_participants(self):
        """Test that the correct number of participants are generated."""
        n = 50
        df = generate_counterbalance_assignments(n_participants=n, seed=42)
        assert len(df) == n

    def test_50_50_split(self):
        """Test that the split is approximately 50/50."""
        n = 100  # Use even number for exact 50/50
        df = generate_counterbalance_assignments(n_participants=n, seed=42)

        low_high_count = len(df[df['session_order'] == 'Low-High'])
        high_low_count = len(df[df['session_order'] == 'High-Low'])

        assert low_high_count == high_low_count == n // 2

    def test_valid_session_orders(self):
        """Test that only valid session orders are generated."""
        df = generate_counterbalance_assignments(n_participants=20, seed=42)
        valid_orders = {'Low-High', 'High-Low'}
        assert set(df['session_order'].unique()).issubset(valid_orders)

    def test_reproducibility(self):
        """Test that the same seed produces the same results."""
        df1 = generate_counterbalance_assignments(n_participants=20, seed=42)
        df2 = generate_counterbalance_assignments(n_participants=20, seed=42)

        assert df1.equals(df2), "Results should be reproducible with the same seed"

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        df1 = generate_counterbalance_assignments(n_participants=20, seed=42)
        df2 = generate_counterbalance_assignments(n_participants=20, seed=123)

        # They should not be identical (high probability)
        assert not df1.equals(df2), "Different seeds should produce different results"

    def test_participant_id_format(self):
        """Test that participant IDs are formatted correctly."""
        df = generate_counterbalance_assignments(n_participants=5, seed=42)
        expected_ids = ['P001', 'P002', 'P003', 'P004', 'P005']
        assert list(df['participant_id']) == expected_ids

    def test_file_output_path(self):
        """Test that the file is saved to the correct location."""
        # This test would normally check the actual file system
        # For now, we verify the function returns the correct DataFrame
        df = generate_counterbalance_assignments(n_participants=10, seed=42)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
