"""
Tests for counterbalance assignment generation (T027a).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.counterbalance import generate_counterbalance_assignments, SESSION_ORDER_A, SESSION_ORDER_B


class TestCounterbalanceGeneration:
    """Tests for the counterbalance assignment logic."""

    def test_seed_reproducibility(self):
        """Verify that the same seed produces the same assignment."""
        df1 = generate_counterbalance_assignments(num_participants=20, seed=42)
        df2 = generate_counterbalance_assignments(num_participants=20, seed=42)

        pd.testing.assert_frame_equal(df1, df2)

    def test_even_split_even_count(self):
        """Verify equal split for even number of participants."""
        n = 100
        df = generate_counterbalance_assignments(num_participants=n, seed=42)

        count_a = (df["session_order"] == SESSION_ORDER_A).sum()
        count_b = (df["session_order"] == SESSION_ORDER_B).sum()

        assert count_a == count_b, f"Expected equal split, got A={count_a}, B={count_b}"
        assert count_a + count_b == n

    def test_odd_split_odd_count(self):
        """Verify near-equal split for odd number of participants."""
        n = 101
        df = generate_counterbalance_assignments(num_participants=n, seed=42)

        count_a = (df["session_order"] == SESSION_ORDER_A).sum()
        count_b = (df["session_order"] == SESSION_ORDER_B).sum()

        # Difference should be at most 1
        assert abs(count_a - count_b) == 1, f"Expected diff of 1, got {abs(count_a - count_b)}"
        assert count_a + count_b == n

    def test_valid_session_orders(self):
        """Verify all assigned orders are valid constants."""
        df = generate_counterbalance_assignments(num_participants=50, seed=42)
        unique_orders = set(df["session_order"].unique())
        expected_orders = {SESSION_ORDER_A, SESSION_ORDER_B}

        assert unique_orders.issubset(expected_orders), f"Invalid orders found: {unique_orders - expected_orders}"

    def test_participant_id_format(self):
        """Verify participant IDs follow P{N:03d} format."""
        df = generate_counterbalance_assignments(num_participants=10, seed=42)
        expected_ids = [f"P{i+1:03d}" for i in range(10)]
        assert list(df["participant_id"]) == expected_ids

    def test_output_schema(self):
        """Verify the DataFrame has the correct columns."""
        df = generate_counterbalance_assignments(num_participants=10, seed=42)
        assert "participant_id" in df.columns
        assert "session_order" in df.columns
        assert len(df.columns) == 2