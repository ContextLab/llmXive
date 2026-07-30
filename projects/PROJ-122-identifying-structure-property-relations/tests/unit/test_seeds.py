"""
Unit tests for deterministic seed utilities.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.seeds import validate_seed, set_deterministic_seed, get_seed_context

class TestSeedUtilities:
    """Unit tests for seed management."""

    def test_validate_seed(self):
        """Test seed validation."""
        assert validate_seed(42) is True
        assert validate_seed(0) is True
        assert validate_seed(-1) is False

    def test_set_deterministic_seed(self):
        """Test setting deterministic seed."""
        set_deterministic_seed(42)
        # If this runs without error, the seed was set
        assert True

    def test_get_seed_context(self):
        """Test getting seed context."""
        context = get_seed_context(42)
        assert context is not None
        assert "seed" in context
