"""
Contract tests verifying the interface between Data Generation and Simulation.
"""
import numpy as np
import pytest
from typing import Dict, Any

from code.data_generator import generate_data
from code.simulation_engine import run_single_test_replicate


class TestDataSimContract:
    """Tests ensuring data generation and simulation engine agree on formats."""

    def test_data_gen_returns_tuple(self):
        """Verify generate_data returns (data, metadata) tuple."""
        data, meta = generate_data(
            distribution="normal",
            n=100,
            effect_size=0.5,
            test_type="t-test"
        )
        
        assert isinstance(data, np.ndarray)
        assert isinstance(meta, dict)
        assert "distribution" in meta
        assert "n" in meta
        assert "effect_size" in meta

    def test_simulation_accepts_data(self):
        """Verify simulation engine accepts generated data correctly."""
        # Generate null data
        data, meta = generate_data(
            distribution="normal",
            n=50,
            effect_size=0.0,
            test_type="t-test"
        )
        
        # Run a single replicate (should not crash)
        # We mock the p-value calculation by passing a simple function or using the engine's logic
        # For contract testing, we just ensure the types align
        try:
            # The engine expects specific arguments, let's check signature compatibility
            # by calling with valid generated data
            result = run_single_test_replicate(
                data_group1=data[:25],
                data_group2=data[25:],
                test_type="t-test"
            )
            assert "p_value" in result
            assert "reject_null" in result
        except Exception as e:
            pytest.fail(f"Simulation interface contract broken: {e}")