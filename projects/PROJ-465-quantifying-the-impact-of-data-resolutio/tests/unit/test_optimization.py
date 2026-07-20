"""
Unit tests for performance optimization logic in code/inference/optimization.py.
"""
import pytest
import time
import json
from pathlib import Path
import tempfile
import os

# Import the module under test
# Assuming the project structure allows relative imports or we use sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from inference.optimization import (
    validate_performance_budget,
    TARGET_RUNTIME_SECONDS,
    MAX_RUNTIME_SECONDS,
    PERFORMANCE_MARGIN
)
from inference.optimization import get_optimized_run_config
from bilby.core.prior import Prior


class TestPerformanceBudgetValidation:
    """Tests for validate_performance_budget function."""

    def test_within_target(self):
        """Test duration well within the 4-hour target."""
        is_valid, msg = validate_performance_budget(1000) # ~16 mins
        assert is_valid is True
        assert "within target" in msg.lower()

    def test_over_target_under_limit(self):
        """Test duration over 4h but under 6h."""
        # 5 hours = 18000s
        is_valid, msg = validate_performance_budget(18000)
        assert is_valid is True
        assert "exceeds target" in msg.lower()
        assert "within limit" in msg.lower()

    def test_over_limit(self):
        """Test duration exceeding 6h limit."""
        # 7 hours = 25200s
        is_valid, msg = validate_performance_budget(25200)
        assert is_valid is False
        assert "exceeds limit" in msg.lower()

    def test_zero_duration(self):
        """Test zero duration."""
        is_valid, msg = validate_performance_budget(0)
        assert is_valid is True
        assert "within target" in msg.lower()


class TestOptimizedRunConfig:
    """Tests for get_optimized_run_config function."""

    def test_config_structure(self):
        """Test that the generated config has required keys."""
        prior_dict = {
            'mass_1': Prior(name='mass_1', minimum=10, maximum=50),
        }
        config = get_optimized_run_config(
            "IMRPhenomPv2",
            {'sampling_rate': 4096},
            "dummy.h5",
            prior_dict
        )
        
        required_keys = ['sampler', 'nlive', 'dlogz', 'maxiter', 'boundary', 'sample', 'time_limit']
        for key in required_keys:
            assert key in config, f"Missing key {key} in config"

    def test_live_points_reduction(self):
        """Test that nlive is reduced for speed (heuristic)."""
        prior_dict = {'mass_1': Prior(name='mass_1', minimum=10, maximum=50)}
        config = get_optimized_run_config(
            "IMRPhenomPv2",
            {'sampling_rate': 4096},
            "dummy.h5",
            prior_dict
        )
        # Expecting a reduced number (e.g., 250) vs default 1000
        assert config['nlive'] < 500, f"nlive {config['nlive']} should be reduced for speed"

    def test_time_limit_calculation(self):
        """Test that time_limit is calculated based on target and margin."""
        prior_dict = {'mass_1': Prior(name='mass_1', minimum=10, maximum=50)}
        config = get_optimized_run_config(
            "IMRPhenomPv2",
            {'sampling_rate': 4096},
            "dummy.h5",
            prior_dict
        )
        
        expected_limit = TARGET_RUNTIME_SECONDS * PERFORMANCE_MARGIN
        assert config['time_limit'] == expected_limit, \
            f"Time limit {config['time_limit']} != {expected_limit}"

    def test_boundary_sample_type(self):
        """Test that faster boundary and sample types are selected."""
        prior_dict = {'mass_1': Prior(name='mass_1', minimum=10, maximum=50)}
        config = get_optimized_run_config(
            "IMRPhenomPv2",
            {'sampling_rate': 4096},
            "dummy.h5",
            prior_dict
        )
        
        # 'unif' boundary is generally faster than 'ellipsoid'
        assert config['boundary'] == 'unif', f"Expected 'unif' boundary, got {config['boundary']}"
        # 'rwalk' is a common fast choice
        assert config['sample'] == 'rwalk', f"Expected 'rwalk' sample, got {config['sample']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])