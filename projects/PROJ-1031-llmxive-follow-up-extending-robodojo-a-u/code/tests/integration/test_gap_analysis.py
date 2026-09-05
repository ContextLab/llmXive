"""
Integration test for Physics Fidelity Gap calculation.
"""
import pytest
import sys
from pathlib import Path
import json
import tempfile

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.stats_analysis import calculate_physics_fidelity_gap


class TestGapAnalysis:
    """Integration tests for fidelity gap calculation."""

    def test_gap_calculation(self):
        """Verify gap calculation logic."""
        oracle_rate = 0.95
        real_world_rate = 0.80

        gap = calculate_physics_fidelity_gap(oracle_rate, real_world_rate)

        assert gap == 0.15
        assert isinstance(gap, float)
